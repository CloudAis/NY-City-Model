"""Actual source-based stratified review selection; no invented roof labels.

Industrial labels remain PARCEL context (PLUTO LandUse 06), not an assertion
that each building on that parcel is an industrial structure.
"""
import csv,sqlite3,json
from collections import Counter
from nyc.download import ROOT,atomic_json,sha,now
from nyc.buildings import BOROUGHS,classify
out=ROOT/'data/processed/building-stage4';out.mkdir(parents=True,exist_ok=True)
db=sqlite3.connect(f'file:{ROOT}/data/processed/city/buildings.sqlite?mode=ro',uri=True)
db.execute('create temp table industrial_parcels(bbl text primary key,landuse text,bldgclass text,numbldgs text)')
path=ROOT/'data/intermediate/extracted/nyc_pluto_26v2_csv/pluto_26v2.csv'
rows=[]
with path.open(newline='')as f:
 for r in csv.DictReader(f):
  if r['landuse'].strip()in ['6','06']:
   bbl=r['bbl'].split('.')[0];rows.append((bbl,r['landuse'],r['bldgclass'],r['numbldgs']))
db.executemany('insert or ignore into industrial_parcels values(?,?,?,?)',rows)
selected=[];counts=Counter()
for borough in BOROUGHS:
 common="b.capture=? and b.borough=? and not json_extract(b.payload,'$.placeholder')";params=['2026-10-27-city:'+borough,borough]
 queries=[
 ('high_source_height',f'select b.payload from buildings b where {common} and height_m is not null order by height_m desc,b.id limit 100'),
 ('low_source_height',f'select b.payload from buildings b where {common} and height_m>0 order by height_m,b.id limit 100'),
 ('complex_outline_NOT_verified_complex_roof',f"select b.payload from buildings b where {common} order by json_array_length(json_extract(b.payload,'$.geometry.coordinates[0]')) desc,b.id limit 100"),
 ('large_footprint',f"select b.payload from buildings b where {common} order by json_extract(b.payload,'$.area_m2') desc,b.id limit 100"),
 ('industrial_parcel_context_ONLY',f'select b.payload from buildings b join industrial_parcels p on p.bbl=b.bbl where {common} order by height_m desc,b.id limit 100')]
 seen=set()
 for label,sql in queries:
  taken=0
  for (payload,)in db.execute(sql,params):
   r=json.loads(payload)
   if r['id']in seen:continue
   m=classify(r)
   if label in ['high_source_height','low_source_height']and m['height_hypothesis_m']is None:continue
   seen.add(r['id']);entry={'selection_category':label,'record':r}
   if label=='industrial_parcel_context_ONLY':entry['parcel_context']=dict(zip(['landuse','bldgclass','numbldgs'],db.execute('select landuse,bldgclass,numbldgs from industrial_parcels where bbl=?',(r['base_bbl'],)).fetchone()))
   selected.append(entry);counts[borough+':'+label]+=1;taken+=1
   if taken==8:break
  if taken<8:raise ValueError(f'actual candidates insufficient: {borough} {label} {taken}')
 print('REVIEW_SELECTION',borough,len(seen),flush=True)
# Additional actual courtyard objects if they exist: explicitly report none otherwise.
holes=[]
for (payload,)in db.execute("select payload from buildings where capture like '2026-10-27-city:%' and json_array_length(json_extract(payload,'$.geometry.coordinates'))>1 limit 20"):
 r=json.loads(payload);g=r['geometry'];rings=sum(len(p)-1 for p in(g['coordinates']if g['type']=='MultiPolygon'else[g['coordinates']]))
 if rings>0:holes.append({'selection_category':'actual_courtyard','record':r})
known={e['record']['id']for e in selected}
selected.extend(e for e in holes if e['record']['id']not in known)
atomic_json(out/'review-selection.json',{'at':now(),'source_version':'2026-10-27-city','selection_counts':dict(counts),'records':selected,'actual_courtyard_candidates':len(holes),'complex_roof_verified':0,'industrial_verified_building_count':0,'industrial_context_source':{'path':str(path.relative_to(ROOT)),'sha256':sha(path),'scope':'parcel LandUse06 and primary building class; NOT per-building use'},'no_complex_roof_evidence':'Complex outline is a geometry stress case, not evidence of roof form.'})
print('REVIEW_TOTAL',len(selected),flush=True)
