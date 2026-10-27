"""Offline stage3 browser package; source/checkpoint data stay in the existing project."""
import json,zipfile,hashlib
from pathlib import Path
from nyc.download import ROOT,sha,atomic_json,now

browser=json.loads((ROOT/'reports/stage3/browser.json').read_text());tests=(ROOT/'reports/stage3/tests.log').read_text();summary=json.loads((ROOT/'reports/stage3/summary.json').read_text())
if browser['errors']or not tests.rstrip().endswith('OK')or not summary['python_tests_passed']:raise ValueError('candidate has failing checks; refuse release')
js=[p for p in(ROOT/'dist/assets').glob('*.js')]
if not js or not all(any(url.endswith('/assets/'+p.name)for url in browser['requests'])for p in js):raise ValueError('current build JavaScript differs from actual browser candidate')
entries={}
for p in sorted((ROOT/'dist').rglob('*')):
 if p.is_file():entries['app/'+str(p.relative_to(ROOT/'dist'))]=p.read_bytes()
entries['sample-preview.html']=(ROOT/'reports/nyc-real-sample-preview.html').read_bytes()
for p in sorted((ROOT/'docs').glob('*.md')):entries[str(p.relative_to(ROOT))]=p.read_bytes()
for name in ['README.md','THIRD_PARTY_NOTICES.md','reports/GEOGRAPHIC_REGISTRATION.md','reports/stage3/summary.json','reports/stage3/registration.json','reports/stage3/terrain-quality.json','reports/stage3/browser.json','reports/stage3/tests.log','reports/stage3/stage2-input-integrity.json','data/processed/foundation/checkpoints.csv','data/manifests/stage3/sources.json','data/manifests/stage3/file-coordinate-audit.jsonl']:
 entries[name]=(ROOT/name).read_bytes()
# Small modular source is included for review; dependencies and bulk GIS source inputs are not bundled.
for directory in ['src','scripts','tests']:
 for p in sorted((ROOT/directory).rglob('*')):
  if p.is_file()and'__pycache__'not in p.parts and p.suffix in ['.py','.ts','.mjs','.css','.html']:entries['source/'+str(p.relative_to(ROOT))]=p.read_bytes()
for name in ['AGENTS.md','package.json','package-lock.json','requirements-lock.txt','vite.config.ts','tsconfig.json','index.html','terrain.html']:entries['source/'+name]=(ROOT/name).read_bytes()
entries['START.txt']='''NYC coordinate/elevation foundation — stage 3
Unzip, then run without Internet or npm:
  python3 -m http.server 8000 --bind 127.0.0.1 --directory app
Open http://localhost:8000 for geographic reference layers.
Open http://localhost:8000/terrain.html for real NAVD88 terrain inspection.

Six real 2017 masked DEM crops; 24 local terrain tiles. Missing cells are
holes, never filled as zero. Water follows retained official polygons and
holes; H=0 NAVD88 is a chosen display level, not observed tide.

Global DEM ECEF placement is BLOCKED by generic-NAD83 / NAD83(2011)
source conflict. Building foot units and bridge decks remain unresolved.
30 source-correspondence checkpoints; ZERO independent surveyed controls.
No fabricated buildings, heights, streets, roofs, facades or interiors.

sample-preview.html is only Lower Manhattan/Midtown footprint linework.
file:// was blocked by environment policy; offline HTML content was tested.

source/ contains reviewable modular source. Full city SQLite, original 3dm,
PLUTO, geoid and other bulk GIS inputs remain in /workspace/nyc-3d-html;
not all processing can run from this small browser package alone.
See the geographic registration report, sources and known gaps.
'''.encode()
checks={name:hashlib.sha256(data).hexdigest()for name,data in entries.items()};entries['CHECKSUMS.json']=json.dumps(checks,indent=2).encode();target=ROOT/'reports/nyc-stage3-foundation.zip'
with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for name,data in entries.items():z.writestr(name,data)
with zipfile.ZipFile(target)as z:
 if z.testzip()is not None:raise ValueError('archive CRC failed')
 for name,digest in checks.items():
  if hashlib.sha256(z.read(name)).hexdigest()!=digest:raise ValueError('archive checksum mismatch: '+name)
atomic_json(ROOT/'reports/stage3/release.json',{'at_utc':now(),'archive':str(target.relative_to(ROOT)),'bytes':target.stat().st_size,'sha256':sha(target),'entries':len(entries),'readback_checksums_passed':True,'actual_browser_js_matches_build':True,'global_vertical_registration_completed':False,'modular_source_included':True,'bulk_inputs_included':False})
print('STAGE3_RELEASE',target.stat().st_size,'bytes',len(entries),'entries; all readback checksums passed')
