"""Restartable RTree broad-phase index; original coordinate precision remains in payloads."""
import sqlite3,json
from pathlib import Path
from nyc.download import ROOT,atomic_json,now
from nyc.tiles import rings
path=ROOT/'data/processed/city/buildings.sqlite';db=sqlite3.connect(path);db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA user_version=1');db.executescript('CREATE VIRTUAL TABLE IF NOT EXISTS spatial USING rtree(row_id,minx,maxx,miny,maxy);CREATE TABLE IF NOT EXISTS spatial_progress(key TEXT PRIMARY KEY,value INTEGER);');last=db.execute("SELECT value FROM spatial_progress WHERE key='last_rowid'").fetchone();last=last[0]if last else 0
while True:
 rows=db.execute('SELECT rowid,payload FROM buildings WHERE rowid>? ORDER BY rowid LIMIT 1000',(last,)).fetchall()
 if not rows:break
 entries=[]
 for row_id,text in rows:
  r=json.loads(text);pts=[p for ring in rings(r['geometry'])for p in ring];entries.append((row_id,min(p[0]for p in pts),max(p[0]for p in pts),min(p[1]for p in pts),max(p[1]for p in pts)))
 with db:
  db.executemany('INSERT OR REPLACE INTO spatial VALUES(?,?,?,?,?)',entries);last=rows[-1][0];db.execute("INSERT OR REPLACE INTO spatial_progress VALUES('last_rowid',?)",(last,))
 if last%50000==0:print('spatial',last,flush=True)
count=db.execute('SELECT count(*) FROM spatial').fetchone()[0];expected=db.execute('SELECT count(*) FROM buildings').fetchone()[0]
if count!=expected:raise ValueError('spatial index coverage mismatch')
db.execute('PRAGMA wal_checkpoint(TRUNCATE)');db.close();atomic_json(ROOT/'reports/spatial-index.json',{'at':now(),'indexed_records':count,'crs':'EPSG:32118','units':'metre','index_precision':'SQLite RTree outward-rounded float32 bounds, broad phase only','record_coordinate_precision':'float64 geometry unchanged; exact polygon intersection follows candidate retrieval'});print('SPATIAL_COMPLETE',count,flush=True)
