"""Stream the tested offline runtime, source and association table into ZIP64.

Never accumulate multi-GiB city resources in RAM. Read back every entry with
CRC and SHA256. Large original GIS/old-model/source SQLite are not included.
"""
import json,hashlib,zipfile,os
from nyc.download import ROOT,sha,atomic_json,now
def main():
 q=json.loads((ROOT/'reports/stage4/quality-report.json').read_text());b=json.loads((ROOT/'reports/stage4/browser.json').read_text());f=json.loads((ROOT/'reports/stage4/foundation/browser.json').read_text())
 if b['errors']or f['errors']or q['reviewed_actual_objects']<200:raise ValueError('candidate has not passed review')
 requests=b['requests']+f['requests'];scripts=list((ROOT/'dist/assets').glob('*.js'))
 if not scripts or any(not any(u.endswith('/assets/'+p.name)for u in requests)for p in scripts):raise ValueError('current JavaScript build differs from actual tested candidate')
 paths={}
 for p in sorted((ROOT/'dist').rglob('*')):
  if p.is_file():paths['app/'+str(p.relative_to(ROOT/'dist'))]=p
 for directory in['docs','src','scripts','tests']:
  for p in sorted((ROOT/directory).rglob('*')):
   if p.is_file()and'__pycache__'not in p.parts and p.suffix in['.py','.ts','.mjs','.css','.html','.md']:paths[('source/'if directory!='docs'else'')+str(p.relative_to(ROOT))]=p
 for name in['README.md','AGENTS.md','package.json','package-lock.json','requirements-lock.txt','vite.config.ts','tsconfig.json','index.html','terrain.html','buildings.html','THIRD_PARTY_NOTICES.md','reports/BUILDING_QUALITY.md','reports/GEOGRAPHIC_REGISTRATION.md','data/processed/building-stage4/city/associations.sqlite','data/processed/building-stage4/review-selection.json']:
  paths[name]=ROOT/name
 for directory in['data/manifests/stage4','reports/stage4']:
  for p in sorted((ROOT/directory).rglob('*')):
   if p.is_file()and p.suffix in['.json','.jsonl','.csv','.log']and p.name!='release.json':paths[str(p.relative_to(ROOT))]=p
 target=ROOT/'reports/nyc-stage4-buildings.zip';tmp=target.with_suffix('.zip.tmp');hashes={};total=0
 start="""NYC evidence-gated building pipeline / stage 4
Unzip. Without Internet or npm:
  python3 -m http.server 8000 --bind 127.0.0.1 --directory app
Open http://localhost:8000/buildings.html
Choose a real sample or five-borough data, then a borough.

DEFAULT STRICT: real official overhead outlines; unknown heights remain null.
OPTIONAL HYPOTHESIS: source HEIGHT_ROOF * assumed 0.3048; open envelope,
not verified ground walls, roofs, building components or current appearance.
Canonical verified building solids / reliable roofs / detailed facades: ZERO.
No random buildings or default heights. Placeholder triangles excluded.

All source entities and full-detail resources are local; city overview hides
full-detail tiles until zooming in. No fictional low-LOD building substitutes.
Ground/vertical reference conflicts remain unresolved, as documented.
219 actual objects compared to saved source; no independent reality survey.

The association SQLite and modular code are included. The large original
source SQLite, raw pages, PLUTO, old 3dm and GIS inputs stay in the workspace
and are not all included; full raw-source audit/rebuild needs those originals.
Normal file:// was not verified; serve app via local HTTP as above.
See reports/BUILDING_QUALITY.md, sources, quality JSON and docs/KNOWN_GAPS.md.
"""
 with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True)as z:
  z.writestr('START.txt',start);hashes['START.txt']=hashlib.sha256(start.encode()).hexdigest()
  for i,(name,p)in enumerate(paths.items()):
   digest=hashlib.sha256()
   with p.open('rb')as src,z.open(name,'w',force_zip64=True)as dst:
    while chunk:=src.read(1024*1024):digest.update(chunk);dst.write(chunk);total+=len(chunk)
   hashes[name]=digest.hexdigest()
   if i%2000==0:print('ZIP_WRITE',i,'input_bytes',total,flush=True)
  z.writestr('CHECKSUMS.json',json.dumps(hashes,indent=2))
 with zipfile.ZipFile(tmp)as z:
  for i,(name,expected)in enumerate(hashes.items()):
   digest=hashlib.sha256()
   with z.open(name)as src:
    while chunk:=src.read(1024*1024):digest.update(chunk)
   if digest.hexdigest()!=expected:raise ValueError('ZIP SHA mismatch: '+name)
   if i%3000==0:print('ZIP_READBACK',i,flush=True)
 os.replace(tmp,target)
 atomic_json(ROOT/'reports/stage4/release.json',{'at_utc':now(),'archive':str(target.relative_to(ROOT)),'bytes':target.stat().st_size,'sha256':sha(target),'entries':len(hashes)+1,'uncompressed_file_bytes':total,'all_entry_crc_and_sha_readback_passed':True,'actual_browser_js_matches_current_build':True,'full_city_source_outline_resources_included':True,'optional_hypothesis_resources_included':True,'association_sqlite_included':True,'original_bulk_gis_inputs_included':False,'verified_building_solids':0,'reliable_roofs':0,'verified_facades':0})
 print('STAGE4_PACKAGE_COMPLETE',target.stat().st_size,len(hashes)+1,flush=True)
if __name__=='__main__':main()
