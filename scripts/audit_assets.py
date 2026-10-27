from pathlib import Path
import json,hashlib,zipfile,datetime
ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'node_modules','.git','.npm-cache','.venv','__pycache__','.codex','.agents','.aws'}
EXT={'.html','.htm','.js','.mjs','.ts','.glb','.gltf','.obj','.fbx','.3dm','.dae','.ply','.las','.laz','.tif','.tiff','.png','.jpg','.jpeg','.webp','.geojson','.json','.shp','.gpkg','.csv','.zip','.7z','.rar','.kml','.gml','.prj'}
rows=[]
for base in [Path('/workspace/Tinnis'),Path('/workspace/library-files'),Path('/workspace/shared'),Path('/workspace/scratch')]:
 for p in base.rglob('*'):
  if not p.is_file() or any(q in EXCLUDED for q in p.relative_to(base).parts) or p.suffix.lower() not in EXT:continue
  raw=p.read_bytes();r={'path':str(p),'format':p.suffix.lower(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'source':'existing Tinnis fictional railway project' if base.name=='Tinnis' else 'unknown','coverage':'fictional coastal-valley; not New York' if base.name=='Tinnis' else 'unknown','reusable':'UI/loading/picking concepts only, not geographic/model evidence' if base.name=='Tinnis' else 'pending verification'}
  if p.suffix.lower()=='.zip':
   try:
    with zipfile.ZipFile(p)as z:r['archive_entries']=[{'path':i.filename,'bytes':i.file_size} for i in z.infolist()][:10000]
   except Exception as e:r['archive_error']=str(e)
  rows.append(r)
(ROOT/'reports/asset-audit.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'search_roots':['/workspace/Tinnis','/workspace/library-files','/workspace/shared','/workspace/scratch'],'excluded':sorted(EXCLUDED),'old_manhattan_found':False,'items':rows},ensure_ascii=False,indent=2))
print('Audited assets',len(rows),'bytes',sum(r['bytes']for r in rows))
