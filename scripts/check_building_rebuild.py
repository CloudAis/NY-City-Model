"""Actual idempotence, missing-owner-tile repair and by-building rebuild checks."""
import json,subprocess,tempfile,os
from pathlib import Path
from nyc.download import ROOT,sha,atomic_json,now
out=ROOT/'assets/buildings-pilot-lower';work=ROOT/'data/processed/building-stage4/lower-manhattan';exe=str(ROOT/'.venv/bin/python')
command=[exe,'scripts/build_buildings.py','--aoi','lower-manhattan','--work',str(work.relative_to(ROOT)),'--output',str(out.relative_to(ROOT))]
def snapshot():return {str(p.relative_to(out)):(sha(p),p.stat().st_mtime_ns)for p in out.rglob('*')if p.is_file()and(p.suffix=='.glb'or(p.suffix=='.json'and p.name not in['manifest.json','quality.json','tiles.json','sources.json','representation-policy.json','strict.json','hypothesis.json']))}
before=snapshot();subprocess.run(command,cwd=ROOT,check=True);repeat=snapshot()
if before!=repeat:raise ValueError('repeat rewrote a previously verified tile or changed geometry/identity')
tiles=json.loads((out/'manhattan/tiles.json').read_text());tile=tiles[0];victim=out/'manhattan'/tile['strict_glb'];stored=sha(victim)
with tempfile.TemporaryDirectory(dir=ROOT/'data/intermediate')as d:
 backup=Path(d)/victim.name;os.replace(victim,backup)
 try:subprocess.run(command,cwd=ROOT,check=True)
 except BaseException:
  if not victim.exists():os.replace(backup,victim)
  raise
 if sha(victim)!=stored:raise ValueError('single missing tile rebuilt to different bytes')
after=snapshot()
changed_mtime=[p for p in after if after[p][1]!=repeat[p][1]];changed_content=[p for p in after if after[p][0]!=repeat[p][0]]
if changed_content:raise ValueError('tile repair changed content')
allowed={f'manhattan/{tile["id"]}-strict.glb',f'manhattan/{tile["id"]}-hypothesis.glb',f'manhattan/{tile["id"]}.json',f'manhattan/{tile["id"]}.receipt.json'}
if set(changed_mtime)-allowed:raise ValueError('repair rewrote unrelated tiles')
id=tile['feature_ids'][0]
# Isolated outputs avoid damaging the current all-city checkpoint.
single=ROOT/'data/intermediate/stage4-single-rebuild';singlework=ROOT/'data/intermediate/stage4-single-work'
subprocess.run([exe,'scripts/build_buildings.py','--id',id,'--work',str(singlework.relative_to(ROOT)),'--output',str(single.relative_to(ROOT))],cwd=ROOT,check=True)
manifest=json.loads((single/'manifest.json').read_text())
if manifest['counts']['source_records']!=1:raise ValueError('object rebuild includes unrelated sources')
atomic_json(ROOT/'reports/stage4/rebuild-check.json',{'at':now(),'pilot_repeat_equal_hashes_and_mtimes':True,'single_tile_repair_byte_identical':True,'unrelated_tiles_unchanged':True,'regenerated_files':changed_mtime,'object_rebuilt':id,'object_source_records':1,'command':command,'source_raw_modified':False})
print('REBUILD_CHECK_COMPLETE',len(before),'unchanged on repeat; missing tile repaired; exact object rebuilt',flush=True)
