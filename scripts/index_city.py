"""Bounded-memory city normalization into a restartable, versioned SQLite evidence store."""
import argparse,json,sqlite3,time,shutil,hashlib
from pathlib import Path
from nyc.download import ROOT,atomic_json,sha,now
from nyc.normalize import normalize
BOROUGHS=['manhattan','bronx','brooklyn','queens','staten-island']
p=argparse.ArgumentParser();p.add_argument('--wait',action='store_true');p.add_argument('--output',default=str(ROOT/'data/processed/city'));p.add_argument('--borough',choices=BOROUGHS);a=p.parse_args();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True);db=sqlite3.connect(out/'buildings.sqlite');db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA synchronous=FULL')
db.executescript('''CREATE TABLE IF NOT EXISTS buildings(capture TEXT,id TEXT,source_id TEXT,bin TEXT,bbl TEXT,borough TEXT,height_m REAL,ground_m REAL,parts INTEGER,payload TEXT,payload_sha TEXT,PRIMARY KEY(capture,id));
CREATE TABLE IF NOT EXISTS pages(capture TEXT,page TEXT,sha TEXT,records INTEGER,PRIMARY KEY(capture,page));
CREATE TABLE IF NOT EXISTS quarantine(capture TEXT,object_id INTEGER,error TEXT,raw_path TEXT,PRIMARY KEY(capture,object_id));
CREATE INDEX IF NOT EXISTS idx_bin ON buildings(bin);CREATE INDEX IF NOT EXISTS idx_bbl ON buildings(bbl);''')
processor=sha(ROOT/'scripts/nyc/normalize.py')
db.execute('CREATE TABLE IF NOT EXISTS processor_meta(key TEXT PRIMARY KEY,value TEXT)')
previous=db.execute("SELECT value FROM processor_meta WHERE key='normalizer_sha256'").fetchone()
if previous and previous[0]!=processor:raise ValueError('processor changed: use a new --output; do not silently reuse normalized pages')
if not previous and db.execute('SELECT count(*) FROM buildings').fetchone()[0]:
 old_report=ROOT/'reports/city-quality.json'
 if not old_report.exists()or json.loads(old_report.read_text()).get('processor_sha256')!=processor:raise ValueError('unversioned existing cache cannot be trusted with this processor')
with db:db.execute("INSERT OR REPLACE INTO processor_meta VALUES('normalizer_sha256',?)",(processor,))
summary=[];start=time.monotonic()
for borough in [a.borough]if a.borough else BOROUGHS:
 mp=ROOT/f'data/intermediate/city-{borough}/manifest.json'
 while not mp.exists():
  if not a.wait:raise FileNotFoundError(mp)
  if time.monotonic()-start>7200:raise TimeoutError('city source capture not complete: '+borough)
  time.sleep(5)
 mf=json.loads(mp.read_text());capture=mf['version']+':'+borough;work=ROOT/'data/intermediate/city-normalize-work';work.mkdir(exist_ok=True)
 for i,page in enumerate(mf['pages']):
  if sha(ROOT/page['path'])!=page['sha256']:raise ValueError('immutable source bytes changed after capture')
  existing=db.execute('SELECT sha FROM pages WHERE capture=? AND page=?',(capture,page['id'])).fetchone()
  if existing:
   if existing[0]!=page['sha256']:raise ValueError('raw page changed within immutable capture')
   continue
  if shutil.disk_usage(out).free<2*1024**3:raise ValueError('stop before disk reserve exhausted; source/DB checkpoints retained')
  mini={**mf,'pages':[page],'records_downloaded':page['records'],'partition_only':True};atomic_json(work/'manifest.json',mini);report=normalize(work/'manifest.json',work/'normalized');rows=[json.loads(x)for x in(work/'normalized/buildings.jsonl').read_text().splitlines()];fail=json.loads((work/'normalized/failures.json').read_text());values=[]
  for r in rows:
   encoded=json.dumps(r,ensure_ascii=False,separators=(',',':'));values.append((capture,r['id'],r['source_id'],r['bin'],r['base_bbl'],borough,r['height_m'],r['ground_elevation_m'],len(r['parts']),encoded,hashlib.sha256(encoded.encode()).hexdigest()))
  with db:
   db.executemany('INSERT INTO buildings VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(capture,id) DO UPDATE SET source_id=excluded.source_id,bin=excluded.bin,bbl=excluded.bbl,borough=excluded.borough,height_m=excluded.height_m,ground_m=excluded.ground_m,parts=excluded.parts,payload=excluded.payload,payload_sha=excluded.payload_sha',values)
   db.executemany('INSERT OR REPLACE INTO quarantine VALUES(?,?,?,?)',[(capture,r['object_id'],r['error'],r['raw_path'])for r in fail]);db.execute('INSERT INTO pages VALUES(?,?,?,?)',(capture,page['id'],page['sha256'],page['records']))
  if i%20==0 or i==len(mf['pages'])-1:print(borough,'normalized',i+1,'/',len(mf['pages']),flush=True)
 row=db.execute('SELECT count(*),count(DISTINCT source_id),coalesce(sum(parts),0),count(height_m),sum(ground_m<0) FROM buildings WHERE capture=?',(capture,)).fetchone();bad=db.execute('SELECT count(*) FROM quarantine WHERE capture=?',(capture,)).fetchone()[0];processed=db.execute('SELECT sum(records) FROM pages WHERE capture=?',(capture,)).fetchone()[0]
 if processed!=mf['records_downloaded']or row[0]+bad!=mf['records_downloaded']:raise ValueError('normalized+quarantine coverage mismatch')
 item={'borough':borough,'source_manifest':str(mp.relative_to(ROOT)),'capture':capture,'raw_records':mf['records_downloaded'],'normalized_records':row[0],'source_defined_entities':row[1],'geometry_parts':row[2],'valid_source_height_records':row[3],'independently_verified_heights':0,'negative_ground_records_preserved':row[4],'failed_geometries':bad,'unknown_roof_geometry_records':row[0],'unknown_facade_records':row[0],'matched_legacy_models':0,'acquired_legacy_model_archives':1 if borough=='manhattan'else 0,'complete_for_source_bbl_partition':not mf['consistency']['service_changed_during_window'],'partition_basis':'source BASE_BBL first digit, not independent spatial borough validation'};summary.append(item);atomic_json(ROOT/f'reports/city-{borough}-quality.json',item);print('BOROUGH_COMPLETE',json.dumps(item),flush=True)
h=hashlib.sha256()
for capture,id,digest in db.execute('SELECT capture,id,payload_sha FROM buildings ORDER BY capture,id'):h.update((capture+'|'+id+'|'+digest+'\n').encode())
report={'at':now(),'db':str(out/'buildings.sqlite'),'rows':db.execute('SELECT count(*) FROM buildings').fetchone()[0],'semantic_sha256':h.hexdigest(),'boroughs':summary,'unassigned_source_records':'city total comparison in coverage report; not assumed zero','model_entity_count':'unresolved; 3dm surface/object counts must not be reported as building count','processor_sha256':sha(ROOT/'scripts/nyc/normalize.py')};db.execute('PRAGMA wal_checkpoint(TRUNCATE)');db.close();atomic_json(ROOT/'reports/city-quality.json',report);print('CITY_NORMALIZATION_COMPLETE',report['rows'],flush=True)
