"""Same evidence-gated pipeline for source AOI, object, owner tile and five boroughs.

Raw source SQLite is opened read-only. Derived index and completed GLBs resume
independently; a publication manifest is replaced only after every tile verifies.
"""
import argparse,json,sqlite3,math,hashlib,os
from collections import Counter
from pathlib import Path
from shapely.geometry import shape,box
from nyc.download import ROOT,sha,atomic_json,now
from nyc.buildings import VERSION,BOROUGHS,classify,glb
from nyc.coordinates import metric_to_geographic,geographic_to_metric

def compact(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);raw=json.dumps(data,ensure_ascii=False,separators=(',',':')).encode();tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_bytes(raw);os.replace(tmp,path)

def build_index(args):
 source=ROOT/args.database;out=ROOT/args.output;work=ROOT/args.work;work.mkdir(parents=True,exist_ok=True)
 digest=hashlib.sha256(b''.join((ROOT/p).read_bytes()for p in['scripts/build_buildings.py','scripts/nyc/buildings.py','scripts/nyc/coordinates.py'])).hexdigest()
 config={'version':args.version,'borough':args.borough,'aoi':args.aoi,'id':args.id,'tile':args.tile,'bbox':args.bbox,'source_database':str(source),'source_sha256':sha(source),'processor_sha256':digest,'pipeline_version':VERSION}
 configpath=work/'input.json'
 if configpath.exists()and json.loads(configpath.read_text())!=config:raise ValueError('derived work belongs to different inputs/code; choose new --work and --output or explicitly archive the derived directory')
 if not configpath.exists():atomic_json(configpath,config)
 dst=sqlite3.connect(work/'associations.sqlite');dst.execute('PRAGMA journal_mode=WAL')
 dst.executescript('CREATE TABLE IF NOT EXISTS progress(key TEXT PRIMARY KEY,value TEXT); CREATE TABLE IF NOT EXISTS objects(id TEXT PRIMARY KEY,source_rowid INTEGER UNIQUE,borough TEXT,gx INTEGER,gy INTEGER,state TEXT,metadata TEXT,geometry TEXT); CREATE INDEX IF NOT EXISTS owner ON objects(borough,gx,gy,id);')
 progress=dict(dst.execute('select key,value from progress'))
 if progress.get('complete')=='true':return dst,config
 src=sqlite3.connect(f'file:{source}?mode=ro',uri=True)
 last=int(progress.get('last_rowid',0));sql='select rowid,payload from buildings where capture like ? and rowid>?';params=[args.version+':%',last]
 if args.borough:sql+=' and borough=?';params.append(args.borough)
 if args.id:sql+=' and id=?';params.append(args.id)
 if args.aoi:
  b=json.loads((ROOT/f'data/intermediate/{args.aoi}/manifest.json').read_text())['scope']['bbox_wgs84'];args.bbox=b
 if args.bbox:
  w,s,e,n=args.bbox;region=box(w,s,e,n);xy=[geographic_to_metric(x,y)for x,y in[(w,s),(e,n),(w,n),(e,s)]];xs=[p[0]for p in xy];ys=[p[1]for p in xy]
  sql+=' and rowid in(select row_id from spatial where minx<=? and maxx>=? and miny<=? and maxy>=?)';params.extend([max(xs)+1,min(xs)-1,max(ys)+1,min(ys)-1])
 sql+=' order by rowid'
 count=dst.execute('select count(*) from objects').fetchone()[0];batch=[]
 for rowid,payload in src.execute(sql,params):
  r=json.loads(payload)
  if args.bbox and not shape(r['geometry_wgs84']).intersects(region):continue
  m=classify(r);b=m['bounds_metric_m'];gx=math.floor((b[0]+b[2])/1000);gy=math.floor((b[1]+b[3])/1000)
  if args.tile and (gx,gy)!=tuple(args.tile):continue
  m['owner']={'rule':'complete object, 500m cell containing source bounding-box centre; no clipping; no duplicate neighbours','gx':gx,'gy':gy}
  batch.append((m['id'],rowid,m['borough'],gx,gy,m['state'],json.dumps(m,separators=(',',':')),json.dumps(r['geometry'],separators=(',',':'))));count+=1
  if len(batch)>=2000:
   dst.executemany('insert into objects values(?,?,?,?,?,?,?,?)',batch);dst.execute('insert or replace into progress values(?,?)',('last_rowid',str(rowid)));dst.commit();batch=[]
   if count%20000==0:print('INDEX',count,flush=True)
 dst.executemany('insert into objects values(?,?,?,?,?,?,?,?)',batch);dst.execute('insert or replace into progress values(?,?)',('complete','true'));dst.commit();dst.execute('PRAGMA wal_checkpoint(TRUNCATE)');src.close()
 if count==0:raise ValueError('no source records matched; no scene published')
 print('INDEX_COMPLETE',count,flush=True);return dst,config

def root_region(items):
 bounds=[i['bounds_wgs84']for i in items];b=[min(v[0]for v in bounds),min(v[1]for v in bounds),max(v[2]for v in bounds),max(v[3]for v in bounds)]
 return [*(math.radians(x)for x in b),-100,2000],b

def publish(args,db,config):
 out=ROOT/args.output;out.mkdir(parents=True,exist_ok=True);catalog=[];total=Counter();borough_stats=[]
 for borough in BOROUGHS:
  count=db.execute('select count(*) from objects where borough=?',(borough,)).fetchone()[0]
  if not count:continue
  dest=out/borough;dest.mkdir(exist_ok=True);leaves={'strict':[],'hypothesis':[]};items=[];stats=Counter();issues=dest/'anomalies.jsonl';issue_tmp=issues.with_suffix('.jsonl.tmp')
  with issue_tmp.open('w')as anomaly:
   for gx,gy in db.execute('select distinct gx,gy from objects where borough=? order by gx,gy',(borough,)):
    rows=list(db.execute('select metadata,geometry from objects where borough=? and gx=? and gy=? order by id',(borough,gx,gy)))
    records=[]
    for text,geometry in rows:
     m=json.loads(text);stats['source_records']+=1;stats['geometry_parts']+=m['polygon_parts'];stats['interior_rings']+=m['interior_rings'];stats['source_height_numeric_valid']+=m['height_evidence_status']=='source_explicit_unit_unresolved';stats['hypothesis_eligible']+=m['height_hypothesis_m']is not None
     for reason in m['reasons']:stats['reason:'+reason]+=1
     if m['placeholder']:stats['excluded_placeholders']+=1
     else:records.append((m,json.loads(geometry)));stats['published_outline_entities']+=1;stats['published_outline_parts']+=m['polygon_parts']
     if m['placeholder']or m['height_hypothesis_m']is None or m['repair']:
      anomaly.write(json.dumps({'id':m['id'],'borough':borough,'bounds_metric_m':m['bounds_metric_m'],'source_raw':m['raw_record'],'reasons':m['reasons'],'repair':m['repair'],'feature_code':m['feature_code'],'height_raw_ft':m['relative_height_raw_ft']})+'\n')
    for start in range(0,len(records),200):
     group=records[start:start+200];tileid=f'{gx}_{gy}_{start//200:03d}';receipt=dest/(tileid+'.receipt.json')
     identity=hashlib.sha256(json.dumps([(m['id'],m['geometry_sha256'],m['height_hypothesis_m'])for m,_ in group]).encode()).hexdigest()
     prior=json.loads(receipt.read_text())if receipt.exists()else None
     cached=(not args.force_tile or (gx,gy)!=tuple(args.force_tile))and prior and prior.get('identity_sha256')==identity and prior.get('processor_sha256')==config['processor_sha256']and all((dest/f).exists()and sha(dest/f)==v for f,v in prior['files'].items())
     if cached:item=prior['tile']
     else:
      assets={};boxes={};mat=None;parts=None
      for mode in ['strict','hypothesis']:
       data,mat,bv,parts=glb(group,((gx+.5)*500,(gy+.5)*500),mode);p=dest/f'{tileid}-{mode}.glb';tmp=p.with_suffix('.glb.tmp');tmp.write_bytes(data);os.replace(tmp,p);assets[p.name]=sha(p);boxes[mode]=bv
      x1=min(m['bounds_metric_m'][0]for m,_ in group);y1=min(m['bounds_metric_m'][1]for m,_ in group);x2=max(m['bounds_metric_m'][2]for m,_ in group);y2=max(m['bounds_metric_m'][3]for m,_ in group)
      corners=[metric_to_geographic(x,y)for x,y in[(x1,y1),(x1,y2),(x2,y1),(x2,y2)]]
      bounds=[min(p[0]for p in corners),min(p[1]for p in corners),max(p[0]for p in corners),max(p[1]for p in corners)]
      # A volume prevents empty parents requesting the entire city at overview.
      near=[metric_to_geographic(x,y)for x,y in[(x1-5000,y1-5000),(x2+5000,y2+5000)]]
      item={'id':tileid,'entities':len(group),'parts':sum(m['polygon_parts']for m,_ in group),'feature_ids':[m['id']for m,_ in group],'bounds_wgs84':bounds,'enu_to_ecef_column_major':mat,'box_local_enu_m':boxes,'viewer_request_region':[*(math.radians(x)for x in[*near[0],*near[1]]),-100,7500],'strict_glb':f'{tileid}-strict.glb','hypothesis_glb':f'{tileid}-hypothesis.glb','metadata':f'{tileid}.json'}
      compact(dest/item['metadata'],{'source':config,'objects':[m for m,_ in group],'parts':parts});assets[item['metadata']]=sha(dest/item['metadata']);atomic_json(receipt,{'identity_sha256':identity,'processor_sha256':config['processor_sha256'],'files':assets,'tile':item})
     for mode in leaves:
      leaves[mode].append({'boundingVolume':{'box':item['box_local_enu_m'][mode]},'transform':item['enu_to_ecef_column_major'],'viewerRequestVolume':{'region':item['viewer_request_region']},'geometricError':0,'content':{'uri':item[mode+'_glb']}})
     items.append(item)
   anomaly.flush()
  os.replace(issue_tmp,issues)
  if not items:continue
  region,bounds=root_region(items)
  for mode,children in leaves.items():
   compact(dest/f'{mode}.json',{'asset':{'version':'1.1','extras':{'mode':mode,'verified_building_solids':0,'not_world_ground':'ellipsoid display reference only','semantic_level':'outline_only regardless of hypothesis view'}},'geometricError':1000,'root':{'boundingVolume':{'region':region},'geometricError':500,'refine':'ADD','children':children}})
  compact(dest/'tiles.json',items);atomic_json(dest/'quality.json',dict(stats))
  catalog.append({'id':borough,'records':count,'outlines':stats['published_outline_entities'],'tiles':len(items),'bounds_wgs84':bounds,'strict':f'{borough}/strict.json','hypothesis':f'{borough}/hypothesis.json','index':f'{borough}/tiles.json','quality':f'{borough}/quality.json'})
  total.update(stats);borough_stats.append({'borough':borough,**stats});print('PUBLISHED',borough,count,'tiles',len(items),flush=True)
 if not catalog:raise ValueError('all selected geometry is excluded; no publishable tiles')
 manifest={'schema_version':4,'pipeline_version':VERSION,'source':config,'mode_default':'strict','strict_meaning':'source overhead outlines only; canonical height/base/roof unresolved','hypothesis_meaning':'explicit opt-in source height * assumed international foot; open vertical envelope on ellipsoid reference, not actual wall/roof/base','hypothesis_initially_visible':False,'world_registered_buildings':False,'canonical_building_solids':0,'reliable_roofs':0,'verified_facades':0,'semantic_lod_independent':True,'owner_rule':'whole source entity belongs to one 500m owner cell by bbox centre; no clipping or cross-tile duplicate','load_policy':'source polygons unchanged; leaf request region extends 5km horizontally and ellipsoid height -100..7500m; overview explicitly hides these full-detail tiles','boroughs':catalog,'counts':dict(total),'borough_counts':borough_stats,'source_terms':'NYC Open Data Terms; attribution retained','sources_manifest':'sources.json'}
 compact(out/'manifest.json',manifest);atomic_json(ROOT/'reports/stage4'/f'{out.name}-summary.json',manifest);print('PUBLICATION_COMPLETE',sum(d['records']for d in catalog),flush=True)
 return manifest

def main():
 p=argparse.ArgumentParser();p.add_argument('--database',default='data/processed/city/buildings.sqlite');p.add_argument('--version',default='2026-10-27-city');p.add_argument('--borough',choices=BOROUGHS);p.add_argument('--aoi');p.add_argument('--bbox',nargs=4,type=float);p.add_argument('--id');p.add_argument('--tile',nargs=2,type=int);p.add_argument('--force-tile',nargs=2,type=int,help='rebuild only this owner cell; validate/reuse all other outputs');p.add_argument('--work',required=True);p.add_argument('--output',required=True);p.add_argument('--index-only',action='store_true');a=p.parse_args()
 if a.bbox and not(-180<=a.bbox[0]<a.bbox[2]<=180 and -90<=a.bbox[1]<a.bbox[3]<=90):raise ValueError('valid WGS84 bbox required')
 if a.aoi and a.bbox:raise ValueError('choose aoi or bbox')
 db,config=build_index(a)
 if not a.index_only:publish(a,db,config)
 db.close()
if __name__=='__main__':main()
