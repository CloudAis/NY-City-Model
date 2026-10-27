import json,urllib.parse
from pathlib import Path
from nyc.download import Downloader,ROOT,atomic_json,now,sha
DATASETS={'borough':('gthc-hcne','borocode'),'roadbed':('i36f-5ih7','source_id'),'water':('pjs3-c3z5','source_id')}
D=Downloader(interval=.5);report=[]
for name,(id,key)in DATASETS.items():
 root=ROOT/'data/raw/vectors'/(name+'-rowid'if name!='borough'else name);root.mkdir(parents=True,exist_ok=True);base=f'https://data.cityofnewyork.us/resource/{id}'
 count=json.loads(D.get(base+'.json?'+urllib.parse.urlencode({'$select':'count(*)'}),root/'count.json').read_text())[0]['count'];count=int(count);page_size=100 if name=='borough'else 500
 ids=[];pages=[];features=0
 for offset in range(0,count,page_size):
  params={'$limit':page_size,'$offset':offset,'$order':key+' ASC'}
  if name!='borough':
   fields=[c['fieldName']for c in json.load(open(ROOT/f'data/raw/supporting/{name}-metadata.json'))['columns']if not c['fieldName'].startswith(':')]
   params.update({'$select':':id as socrata_row_id,'+','.join(fields),'$order':':id ASC'})
  url=base+'.geojson?'+urllib.parse.urlencode(params)
  path=D.get(url,root/f'page-{offset:08d}.geojson');data=json.loads(path.read_text())
  if data.get('type')!='FeatureCollection':raise ValueError('not GeoJSON')
  got=data['features'];features+=len(got);ids.extend(str(f['properties'].get('socrata_row_id'if name!='borough'else key))for f in got);pages.append({'path':str(path.relative_to(ROOT)),'sha256':sha(path),'features':len(got)})
 if features!=count or len(set(ids))!=count:raise ValueError('count/unique stable source ID mismatch: '+name)
 meta=json.loads((ROOT/f'data/raw/supporting/{name}-metadata.json').read_text())
 # Fresh end checks detect changed counts/publication timestamps despite a successful cache replay.
 end_count_path=D.get(base+'.json?'+urllib.parse.urlencode({'$select':'count(*)'}),root/'count-end.json',refresh=True)
 end_count=int(json.loads(end_count_path.read_text())[0]['count'])
 end_meta_path=D.get(f'https://data.cityofnewyork.us/api/views/{id}.json',root/'metadata-end.json',refresh=True)
 end_meta=json.loads(end_meta_path.read_text());changed=end_count!=count or end_meta.get('rowsUpdatedAt')!=meta.get('rowsUpdatedAt')
 if changed:raise ValueError('dynamic vector source changed: capture a new version instead of publishing mixed pages')
 times=[json.loads((ROOT/p['path']).with_name(Path(p['path']).name+'.receipt.json').read_text())['download_started_at']for p in pages]
 atomic_json(root/'manifest.json',{'dataset_id':id,'publisher':meta.get('attribution'),'count':count,'unique_ids':len(set(ids)),'source_id_field':'socrata_row_id'if name!='borough'else key,'source_logical_id_field':key,'id_stability':'Socrata row ID is version-scoped; logical source IDs may repeat','pages':pages,'crs':'EPSG:4326 per GeoJSON','units':'degrees raw, convert before metric calculations','data_updated_at':meta.get('rowsUpdatedAt'),'page_updated_at':meta.get('viewLastModified'),'download_started_at':min(times),'download_finished_at':now(),'end_count':end_count,'end_data_updated_at':end_meta.get('rowsUpdatedAt'),'changed_during_window':changed,'license':'NYC Open Data Terms; see source metadata','coverage':'citywide source dataset','consistency':'ordered pagination, unique row IDs, count and end publication timestamp checked; not a transactional snapshot or per-row historical diff'})
 report.append({'dataset':name,'count':count,'manifest':str((root/'manifest.json').relative_to(ROOT))});print(name,count,flush=True)
atomic_json(ROOT/'reports/support-vector-audit.json',report)
