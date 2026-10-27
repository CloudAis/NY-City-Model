"""Review alternative retained evidence for actual missing/anomalous HEIGHT_ROOF.

PLUTO highest-building floors remain parcel scope; no assumed storey height.
Unavailable/unmatched sources are explicitly not numerical alternatives.
"""
import json,csv,sqlite3
from nyc.download import ROOT,sha,atomic_json,now
db=sqlite3.connect(f'file:{ROOT}/data/processed/city/buildings.sqlite?mode=ro',uri=True)
records=[json.loads(t)for(t,)in db.execute("select payload from buildings where capture like '2026-10-27-city:%' and height_m is null order by id")]
wanted={r['base_bbl']for r in records};parcels={}
p=ROOT/'data/intermediate/extracted/nyc_pluto_26v2_csv/pluto_26v2.csv'
with p.open(newline='')as f:
 for row in csv.DictReader(f):
  bbl=row['bbl'].split('.')[0]
  if bbl in wanted:parcels[bbl]={k:row[k]for k in['bbl','numfloors','numbldgs','bldgclass','landuse','yearbuilt']}
entries=[]
for r in records:
 entries.append({'id':r['id'],'borough':r['borough'],'raw_record':r['raw_record'],'height_raw_ft':r['height_raw_ft'],'height_status':r['height_status'],'canonical_height_m':None,'pluto_parcel_candidate':parcels.get(r['base_bbl']),'pluto_decision':'NOT a building height; highest parcel building floors cannot be multiplied by invented storey height','legacy_model_decision':'0 verified GUID/current-building crosswalk; Feet and epoch conflict unresolved; no height assigned','lidar_decision':'0 acquired LAS/LAZ files, cannot extract roof points','outcome':'source outline only; no default height'})
report={'at':now(),'source_version':'2026-10-27-city','unknown_or_anomalous_source_records':len(entries),'matched_parcel_candidates':sum(e['pluto_parcel_candidate']is not None for e in entries),'resolved_heights':0,'canonical_unit_gaps':'All otherwise numeric HEIGHT_ROOF records also have unresolved foot subtype; this list is specifically numeric missing/anomalous records.','pluto_source':{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'scope':'parcel'},'entries':entries}
atomic_json(ROOT/'reports/stage4/height-gaps.json',report);print('HEIGHT_GAP_REVIEW',len(entries),'no invented heights',flush=True)
