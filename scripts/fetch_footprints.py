"""Official ArcGIS extraction using frozen object-ID sets, never offset-only first-page fetches."""
import argparse,json,sys,hashlib,datetime
from pathlib import Path
from nyc.download import Downloader,ROOT,query_url,atomic_json,now,sha
SERVICE='https://services6.arcgis.com/yG5s3afENB5iO9fj/arcgis/rest/services/BUILDING_view/FeatureServer'
BOROUGHS={'manhattan':1,'bronx':2,'brooklyn':3,'queens':4,'staten-island':5}
SAMPLES={'lower-manhattan':('manhattan',[-74.0165,40.7045,-74.007,40.7115]),'midtown':('manhattan',[-73.989,40.748,-73.977,40.7565]),'brooklyn-dumbo':('brooklyn',[-73.993,40.698,-73.985,40.705]),'queens-lic':('queens',[-73.949,40.743,-73.940,40.751]),'bronx-mott-haven':('bronx',[-73.929,40.807,-73.921,40.815]),'staten-st-george':('staten-island',[-74.084,40.639,-74.073,40.648])}
def fetch(args):
 d=Downloader(interval=args.interval);out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True);version=args.version
 if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-'for c in version):raise ValueError('version must be a safe directory name')
 raw=ROOT/'data/raw/footprints'/version/args.name;raw.mkdir(parents=True,exist_ok=True)
 layer=json.loads(d.get(SERVICE+'/0?f=pjson',raw/'layer-start.json').read_text());oid=layer['objectIdField'];batch=min(args.batch,layer['maxRecordCount'],1000)
 where='1=1'
 if args.borough:
  n=BOROUGHS[args.borough];where=f"BASE_BBL LIKE '{n}%'"
 common={'f':'json','where':where}
 if args.bbox:
  if len(args.bbox)!=4 or not(-180<=args.bbox[0]<args.bbox[2]<=180 and -90<=args.bbox[1]<args.bbox[3]<=90):raise ValueError('invalid WGS84 bbox')
  common.update({'geometry':','.join(map(str,args.bbox)),'geometryType':'esriGeometryEnvelope','inSR':4326,'spatialRel':'esriSpatialRelIntersects'})
 count=json.loads(d.get(query_url(SERVICE+'/0/query',{**common,'returnCountOnly':'true'}),raw/'count.json').read_text())['count']
 ids=sorted(json.loads(d.get(query_url(SERVICE+'/0/query',{**common,'returnIdsOnly':'true'}),raw/'ids.json').read_text())['objectIds']or[])
 if len(ids)!=count or len(ids)!=len(set(ids)):raise ValueError('count/unique-ID snapshot mismatch; use a fresh version')
 if args.max_features and len(ids)>args.max_features:raise ValueError(f'{len(ids)} records exceed budget {args.max_features}; narrow bbox or explicitly raise limit')
 state_path=out/'fetch-state.json';state=json.loads(state_path.read_text())if state_path.exists()else{'completed':{},'started_at':now()}
 signature=hashlib.sha256(json.dumps([version,args.name,ids,common,batch],sort_keys=True).encode()).hexdigest()
 if state.get('signature',signature)!=signature:raise ValueError('resume parameters changed; choose another output directory')
 state.update({'signature':signature,'source':SERVICE,'version':version,'count_expected':count,'ids_sha256':sha(raw/'ids.json'),'scope':{'borough':args.borough,'bbox_wgs84':args.bbox,'where':where},'pipeline_version':'0.1.0-stage2'})
 work=[(i,ids[i:i+batch])for i in range(0,len(ids),batch)];pages=[];seen=[];fresh=0
 for i,group in work:
  key=f'page-{i:08d}';dest=raw/(key+'.json');refresh=args.refetch_page==key
  if args.refetch_page and not any(key==args.refetch_page for key,_ in [(f'page-{x:08d}',g)for x,g in work]):raise ValueError('requested page does not exist')
  url=query_url(SERVICE+'/0/query',{'f':'json','objectIds':','.join(map(str,group)),'outFields':'*','returnGeometry':'true','orderByFields':oid+' ASC','returnZ':'false'})
  p=d.get(url,dest,refresh=refresh);page=json.loads(p.read_text());got=[f['attributes'][oid]for f in page.get('features',[])]
  if page.get('exceededTransferLimit')or set(got)!=set(group)or len(got)!=len(group):raise ValueError('page incomplete, deleted/changed IDs or transfer limit: '+key)
  seen.extend(got);pages.append({'id':key,'path':str(p.relative_to(ROOT)),'sha256':sha(p),'records':len(got)})
  was=key in state['completed'];state['completed'][key]=pages[-1];state['last_success_at']=now();atomic_json(state_path,state)
  if not was:fresh+=1
  print(args.name,key,len(got),'cached'if was and not refresh else'validated',flush=True)
  if args.stop_after_pages and fresh>=args.stop_after_pages:print('INTERRUPTED_AFTER_CHECKPOINT',flush=True);return 75
 if len(seen)!=len(ids)or len(set(seen))!=count:raise ValueError('final unique-ID coverage mismatch')
 end=json.loads(d.get(SERVICE+'/0?f=pjson',raw/'layer-end.json',refresh=True).read_text());end_ids_path=d.get(query_url(SERVICE+'/0/query',{**common,'returnIdsOnly':'true'}),raw/'ids-end.json',refresh=True);end_ids=sorted(json.loads(end_ids_path.read_text())['objectIds']or[])
 changed=layer.get('editingInfo',{}).get('dataLastEditDate')!=end.get('editingInfo',{}).get('dataLastEditDate')or end_ids!=ids
 manifest={**{k:v for k,v in state.items()if k!='completed'},'finished_at':now(),'pages':pages,'records_downloaded':len(seen),'unique_object_ids':len(set(seen)),'consistency':{'start_edit':layer.get('editingInfo'),'end_edit':end.get('editingInfo'),'id_set_equal':end_ids==ids,'service_changed_during_window':changed,'atomic_snapshot':False,'limitation':'Dynamic service; unchanged last-edit and ID set are checks, not a transactional snapshot. Re-fetch a new version if flagged.'},'raw_spatial_reference':layer.get('extent',{}).get('spatialReference'),'height_units':'feet; relative roof height, not elevation','vertical_datum':'Ground often NAVD88 per metadata; per-feature datum not guaranteed','downloaded_at':now(),'observation_date':None,'source_metadata_date':'2025-10-09','license':'NYC Open Data Terms; see captured terms; not blanket CC0','license_class':'local-processing-and-distribution-subject-to-NYC-terms'}
 atomic_json(out/'manifest.json',manifest);return 0
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--borough',choices=BOROUGHS);p.add_argument('--bbox',nargs=4,type=float);p.add_argument('--sample',choices=SAMPLES);p.add_argument('--name',default='custom');p.add_argument('--version',required=True);p.add_argument('--output',required=True);p.add_argument('--batch',type=int,default=256);p.add_argument('--interval',type=float,default=.4);p.add_argument('--max-features',type=int,default=10000);p.add_argument('--stop-after-pages',type=int,default=0);p.add_argument('--refetch-page')
 a=p.parse_args()
 if a.sample:a.borough,a.bbox=SAMPLES[a.sample];a.name=a.sample
 if not 1<=a.batch<=1000:p.error('batch must be 1..1000')
 sys.exit(fetch(a))
