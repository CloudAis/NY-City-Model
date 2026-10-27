"""Reproduce pilot-level parcel/building discrepancies without overwriting building evidence."""
import json
from nyc.download import ROOT,atomic_json
from nyc.evidence import PRIORITY,resolve

rows={}
for path in sorted((ROOT/'data/processed').glob('*/buildings.jsonl')):
 if path.parent.name.startswith('query-'):continue
 for line in path.read_text().splitlines():
  r=json.loads(line);rows[r['id']]=r
conflicts=[]
for lot in json.loads((ROOT/'data/processed/pluto-pilot-links.json').read_text()):
 raw=lot['parcel_attributes'].get('yearbuilt')
 try:year=int(float(raw))if raw else None
 except (TypeError,ValueError):year=None
 if not year:continue
 for id in lot['building_ids']:
  r=rows.get(id)
  if not r or r['construction_year']==year:continue
  candidates=[{'source':'nyc-building-footprints','scope':'building','value':r['construction_year'],'status':'source_explicit'if r['construction_year']is not None else'unknown','observation_date':None,'record_edit_date':r['last_edited_at'],'record_id':id},{'source':'pluto-parcel','scope':'parcel','value':year,'status':'source_explicit','observation_date':None,'data_date':'2026-08','record_id':lot['bbl']}]
  kind='noncomparable-parcel-vs-building-year'if r['construction_year']is not None else'parcel-cannot-fill-unknown-building-year'
  conflicts.append({'building_id':id,'bbl':lot['bbl'],'type':kind,'resolution':resolve('construction_year',candidates)})
conflicts.sort(key=lambda x:(x['building_id'],x['bbl']))
atomic_json(ROOT/'data/processed/field-conflicts.json',conflicts)
atomic_json(ROOT/'data/manifests/field-priorities.json',{'priorities':PRIORITY,'rule':'parcel fields do not override buildings; non-null old evidence survives newer null; independent verification is not inferred from source labels'})
print('NON_COMPARABLE_SCOPE_DISCREPANCIES',len(conflicts),'BUILDING_OVERRIDES',0)
