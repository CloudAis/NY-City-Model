"""Reproduce version-specific city dimensions and preserve per-record repair/anomaly evidence."""
import argparse,json,sqlite3
from pathlib import Path
from nyc.download import ROOT,atomic_json,now

p=argparse.ArgumentParser();p.add_argument('--database',default='data/processed/city/buildings.sqlite');p.add_argument('--version',default='2026-10-27-city');p.add_argument('--output',default='reports/city-dimensions.json');a=p.parse_args()
db=sqlite3.connect(f'file:{Path(a.database).resolve()}?mode=ro',uri=True);pattern=a.version+':%';rows=[];issues=[]
query="SELECT borough,count(*),sum(height_m IS NULL),sum(json_extract(payload,'$.placeholder')),sum(json_extract(payload,'$.repair') IS NOT NULL),sum(json_extract(payload,'$.height_status')='anomalous_range'),count(DISTINCT bin) FROM buildings WHERE capture LIKE ? GROUP BY borough"
for borough,raw,unknown,placeholder,repairs,anomalies,bins in db.execute(query,(pattern,)):
 bounds=db.execute('SELECT min(s.minx),min(s.miny),max(s.maxx),max(s.maxy) FROM spatial s JOIN buildings b ON b.rowid=s.row_id WHERE b.borough=? AND b.capture LIKE ?',(borough,pattern)).fetchone()
 rows.append(dict(borough=borough,raw_records=raw,unknown_heights=unknown,placeholders=placeholder,geometry_repairs=repairs,anomalous_height_values=anomalies,unique_bin_values=bins,bounds_32118_index=bounds));print(borough,raw,'unknown',unknown,'placeholder',placeholder,'repairs',repairs,flush=True)
for id,payload in db.execute("SELECT id,payload FROM buildings WHERE capture LIKE ? AND (json_extract(payload,'$.repair') IS NOT NULL OR json_extract(payload,'$.height_status')='anomalous_range')",(pattern,)):
 r=json.loads(payload);issues.append({'building_id':id,'raw_record':r['raw_record'],'repair':r['repair'],'height_raw_ft':r['height_raw_ft'],'height_status':r['height_status'],'height_m':r['height_m']})
if not rows:raise ValueError('no matching version')
atomic_json(Path(a.output),{'at':now(),'version':a.version,'boroughs':rows,'bounds_basis':'SQLite outward-rounded float32 metric RTree envelopes; exact float64 geometry in payload','bin_count_note':'Includes placeholders; BIN is not assumed unique or one-to-one'})
atomic_json(ROOT/'reports/city-record-issues.json',{'version':a.version,'records':issues});print('ISSUE_RECORDS',len(issues),flush=True)
