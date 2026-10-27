"""Bundle the offline browser samples and checksum the retained large stage-3 inputs."""
import json,zipfile,hashlib
from pathlib import Path
from nyc.download import ROOT,sha,atomic_json,now

inputs=[]
for name in ['data/processed/city/buildings.sqlite','data/processed/context/context.gpkg','data/raw/supporting/nyc_pluto_26v2_csv.zip','data/raw/supporting/nyc_3dmodel_mn01.zip']:
 p=ROOT/name;inputs.append({'path':name,'bytes':p.stat().st_size,'sha256':sha(p),'bundled_in_browser_zip':False})
atomic_json(ROOT/'data/manifests/large-inputs.json',{'at':now(),'files':inputs,'note':'Retained locally, ignored by source Git; raw source receipts and capture manifests identify provenance.'})
entries={}
browser=json.loads((ROOT/'reports/browser-report.json').read_text())
js_names=[p.name for p in(ROOT/'dist/assets').glob('*.js')]
assert js_names and all(any(url.endswith('/assets/'+name)for url in browser['requests'])for name in js_names),'release JS differs from browser-tested JS'
for p in sorted((ROOT/'dist').rglob('*')):
 if p.is_file():entries['app/'+str(p.relative_to(ROOT/'dist'))]=p.read_bytes()
entries['sample-preview.html']=(ROOT/'reports/nyc-real-sample-preview.html').read_bytes()
for p in sorted((ROOT/'docs').glob('*.md')):entries[str(p.relative_to(ROOT))]=p.read_bytes()
for name in ['README.md','THIRD_PARTY_NOTICES.md','docs/ACCURACY.md','docs/KNOWN_GAPS.md','docs/NEXT_STEPS.md','reports/VALIDATION.md','data/manifests/sources.json','data/manifests/coverage.json','data/manifests/large-inputs.json']:
 entries[name]=(ROOT/name).read_bytes()
for name in ['reports/asset-audit.json','reports/ASSET_AUDIT.md','reports/data-quality.json','reports/borough-coverage.csv','data/manifests/files.jsonl','reports/browser-report.json','reports/single-preview-report.json']:
 entries[name]=(ROOT/name).read_bytes()
entries['START.txt']='''NYC measured footprints — stage 1/2 browser release
Run from the extracted directory, without needing internet or npm:
  python3 -m http.server 8000 --bind 127.0.0.1 --directory app
Open http://localhost:8000

app: 6 real sample areas, 3026 non-placeholder footprint outlines.
sample-preview.html: 2 Manhattan areas, 1110 outlines, all resources inline.
file:// was blocked by this environment's browser policy; HTML content was
actually tested fully offline. Normal-browser double-click remains untested.

This is NOT a complete NYC 3D city model. No generated heights, roofs,
facades or interiors. Full-city evidence database and raw archives stay
in the workspace and are NOT included in this small browser package.
See README, sources, coverage, accuracy and limitations.
'''.encode()
checks={name:hashlib.sha256(data).hexdigest()for name,data in entries.items()};entries['CHECKSUMS.json']=json.dumps(checks,indent=2).encode()
target=ROOT/'reports/nyc-stage2-browser.zip'
with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for name,data in entries.items():z.writestr(name,data)
with zipfile.ZipFile(target)as z:
 assert z.testzip()is None
 for name,digest in checks.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest
assert 'app/index.html'in entries and 'app/licenses/cesium.md'in entries
atomic_json(ROOT/'reports/release.json',{'at':now(),'archive':str(target.relative_to(ROOT)),'bytes':target.stat().st_size,'sha256':sha(target),'entries':len(entries),'checksums_verified_by_readback':True,'browser_js_matches_tested_requests':True,'full_city_database_in_archive':False,'large_inputs_manifest':'data/manifests/large-inputs.json'})
print('RELEASE',target.stat().st_size,'bytes',len(entries),'entries; readback checksums valid')
