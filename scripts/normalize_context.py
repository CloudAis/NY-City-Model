"""Separate per-page projection cache and atomic context publication; interrupted merges cannot duplicate rows."""
import json,subprocess,sqlite3,os
from pathlib import Path
from nyc.download import ROOT,atomic_json,sha,now
out=ROOT/'data/processed/context';out.mkdir(parents=True,exist_ok=True);gpkg=out/'context.gpkg';cache=ROOT/'data/intermediate/context-cache';specs=[]
for name,folder in [('borough','borough'),('roadbed','roadbed-rowid'),('water','water-rowid')]:
 mp=ROOT/'data/raw/vectors'/folder/'manifest.json'
 if not mp.exists():raise FileNotFoundError('source not validated complete: '+str(mp))
 specs.append((name,mp,json.loads(mp.read_text())))
signature={name:sha(mp)for name,mp,m in specs};done=out/'publish.json'
if done.exists()and gpkg.exists():
 meta=json.loads(done.read_text())
 if meta['sources']==signature and meta['sha256']==sha(gpkg):print('CONTEXT_CACHE_VALID',flush=True);raise SystemExit(0)
chunks=[]
for name,mp,mf in specs:
 for i,page in enumerate(mf['pages']):
  path=ROOT/page['path'];target=cache/name/f'{i:06d}.gpkg';rec=target.with_suffix('.json');target.parent.mkdir(parents=True,exist_ok=True)
  if rec.exists()and target.exists():
   meta=json.loads(rec.read_text())
   if meta['source_sha256']==page['sha256']and meta['sha256']==sha(target):chunks.append((name,target));continue
  if sha(path)!=page['sha256']:raise ValueError('raw context page checksum mismatch')
  temp=target.with_name(target.stem+'-partial.gpkg');temp.unlink(missing_ok=True)
  subprocess.run(['ogr2ogr','-f','GPKG',str(temp),str(path),'-nln',name,'-s_srs','EPSG:4326','-t_srs','EPSG:32118','-nlt','PROMOTE_TO_MULTI'],check=True,capture_output=True,text=True)
  os.replace(temp,target);atomic_json(rec,{'source_sha256':page['sha256'],'sha256':sha(target)});chunks.append((name,target))
# Rebuild only the cheap publication stage after an interruption, from validated metric chunks.
temp=out/'context-partial.gpkg';temp.unlink(missing_ok=True);seen=set()
for name,chunk in chunks:
 cmd=['ogr2ogr','-f','GPKG',str(temp),str(chunk),name,'-nln',name]
 if temp.exists():cmd+=['-update']
 if name in seen:cmd+=['-append','-unsetFid']
 subprocess.run(cmd,check=True,capture_output=True,text=True);seen.add(name)
report=[]
with sqlite3.connect(temp)as db:
 for name,mp,mf in specs:
  count=db.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0]
  if count!=mf['count']:raise ValueError('projected context count mismatch')
  report.append({'layer':name,'records':count,'source_manifest':str(mp.relative_to(ROOT)),'crs':'EPSG:32118','units':'metre','vertical_datum':None,'independently_verified':False})
os.replace(temp,gpkg);atomic_json(done,{'sources':signature,'sha256':sha(gpkg)});atomic_json(ROOT/'reports/context-quality.json',{'at':now(),'path':str(gpkg.relative_to(ROOT)),'layers':report,'sha256':sha(gpkg),'processor':'system ogr2ogr; version in reports/environment.json'});print('CONTEXT_COMPLETE',report,flush=True)
