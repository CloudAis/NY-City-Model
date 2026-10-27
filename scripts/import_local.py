"""Import real local polygon GeoJSON; unknown provenance is retained in quarantine, never auto-published."""
import argparse,json,hashlib,urllib.parse
from pathlib import Path
from pyproj import CRS
from nyc.download import ROOT,atomic_json,sha,now
from nyc.normalize import normalize,FT
p=argparse.ArgumentParser();p.add_argument('--file',required=True);p.add_argument('--crs',required=True);p.add_argument('--source-id',default='local-user-data');p.add_argument('--source-url');p.add_argument('--version',required=True);p.add_argument('--output',required=True);p.add_argument('--height-field');p.add_argument('--height-kind',choices=['roof_relative']);p.add_argument('--height-unit',choices=['ft','m']);a=p.parse_args()
raw=Path(a.file).read_bytes()
if len(raw)>512*1024**2:raise ValueError('local import exceeds 512MiB budget')
x=json.loads(raw);epsg=CRS.from_user_input(a.crs).to_epsg()
if epsg is None:raise ValueError('explicit supported EPSG CRS required')
if x.get('type')!='FeatureCollection':raise ValueError('polygon GeoJSON FeatureCollection required')
if a.height_field and(not a.height_kind or not a.height_unit):raise ValueError('height semantics and units must both be explicit')
digest=hashlib.sha256(raw).hexdigest();dest=ROOT/'data/raw/local'/f'{digest}.geojson';dest.parent.mkdir(parents=True,exist_ok=True)
if dest.exists():
 if dest.read_bytes()!=raw:raise ValueError('raw hash collision')
else:dest.write_bytes(raw)
source={'source_id':a.source_id,'source_url':a.source_url,'original_path':str(Path(a.file).resolve()),'raw_path':str(dest.relative_to(ROOT)),'sha256':digest,'downloaded_at':None,'local_imported_at':now(),'source_version':a.version,'observation_date':None,'license':'unknown unless separately documented','crs':a.crs,'units':'source CRS units','vertical_datum':None,'provenance_status':'user_declared_unverified'if a.source_url else'unknown_pending_verification'}
out=Path(a.output);out.mkdir(parents=True,exist_ok=True);atomic_json(out/'source.json',source)
if not a.source_url:
 atomic_json(ROOT/'data/manifests/local-pending'/f'{digest}.json',source);print('PENDING_PROVENANCE: raw retained; no normalized records or scene publication');raise SystemExit(0)
if urllib.parse.urlsplit(a.source_url).scheme not in ['http','https']:raise ValueError('source URL must be an http(s) reference')
rows=[];ids=[]
for i,f in enumerate(x['features']):
 g=f.get('geometry')or{};props=f.get('properties')or{};kind=g.get('type')
 if kind not in ['Polygon','MultiPolygon']:raise ValueError('only genuine polygon footprints accepted; no point-to-box generation')
 rings=g['coordinates']if kind=='Polygon'else[r for poly in g['coordinates']for r in poly];sourceid=f.get('id')or props.get('id')or hashlib.sha256(json.dumps(g,sort_keys=True).encode()).hexdigest()[:24];ids.append(str(sourceid));lower={k.lower():v for k,v in props.items()};h=props.get(a.height_field)if a.height_field else None
 if h is not None and a.height_unit=='m':h=float(h)/FT
 rows.append({'attributes':{'OBJECTID':i+1,'DOITT_ID':sourceid,'BASE_BBL':lower.get('base_bbl')or lower.get('bbl'),'BIN':lower.get('bin'),'NAME':lower.get('name'),'HEIGHT_ROOF':h,'GROUND_ELEVATION':None,'CONSTRUCTION_YEAR':None,'FEATURE_CODE':2100,'GEOM_SOURCE':'local user-declared; not independently verified'},'geometry':{'rings':rings}})
if len(set(ids))!=len(ids):raise ValueError('duplicate source IDs; resolve identity instead of overwriting')
work=ROOT/'data/intermediate/local'/digest;work.mkdir(parents=True,exist_ok=True);atomic_json(work/'parsed-esri.json',{'spatialReference':{'wkid':epsg},'features':rows});manifest={'pages':[{'path':str((work/'parsed-esri.json').relative_to(ROOT)),'sha256':sha(work/'parsed-esri.json')}],'raw_spatial_reference':{'wkid':epsg},'version':a.version,'scope':{'borough':None,'bbox_wgs84':None,'local_import':True},'records_downloaded':len(rows),'partition_only':True,'consistency':{'service_changed_during_window':False}};atomic_json(work/'manifest.json',manifest);report=normalize(work/'manifest.json',out)
records=[json.loads(s)for s in(out/'buildings.jsonl').read_text().splitlines()]
for r in records:
 r['id']=a.source_id+':'+r['source_id'];r['raw_record']={'path':str(dest.relative_to(ROOT)),'sha256':digest,'feature_id':r['source_id']};r['identity_stability']='declared_source_id_or_geometry_hash';r['license']='unknown; must be checked before distribution'
 for e in r['evidence'].values():e['source']=a.source_id;e['source_url']=a.source_url;e['provenance_status']='user_declared_unverified'
 for part in r['parts']:part['part_id']=r['id']+':part:'+part['part_id'].split(':part:')[-1]
(out/'buildings.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n'for r in records));report.update({'source_id':a.source_id,'source_url':a.source_url,'source_declared_not_verified':True,'output_sha256':sha(out/'buildings.jsonl'),'citywide_complete':False,'publication_allowed':False,'publication_block':'license and source provenance require review; this command never changes default scene'});atomic_json(out/'quality.json',report);print(json.dumps(report,indent=2))
