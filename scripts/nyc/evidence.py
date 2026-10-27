"""Field-level resolution that never lets a recent null erase older valid evidence."""
PRIORITY={
 'footprint':['nyc-building-footprints','nyc-3d-model-2014','osm'],
 'position':['nyc-building-footprints','nyc-3d-model-2014','osm'],
 'height':['nyc-building-footprints','nyc-nys-lidar-2017','nyc-3d-model-2014','osm'],
 'roof':['nyc-3d-model-2014','nyc-nys-lidar-2017'],
 'facade':[], 'construction_year':['nyc-building-footprints','pluto-parcel']}
STATUS={'source_explicit':3,'derived':2,'estimated':1,'unknown':0}
def resolve(field,candidates):
 eligible=[c for c in candidates if c.get('value')is not None and c.get('status')in STATUS and c.get('status')!='unknown'and c.get('scope','building')=='building']
 priority=PRIORITY.get(field,[])
 def key(c):return (int(c.get('independently_verified',False)),len(priority)-priority.index(c['source'])if c.get('source')in priority else 0,STATUS[c['status']],c.get('observation_date')or'',c.get('source',''),c.get('record_id',''))
 chosen=max(eligible,key=key)if eligible else None
 conflicts=[{'candidate':c,'selected':chosen,'reason':'parcel attributes are non-comparable building evidence'if c.get('scope')=='parcel'else'null/unknown never overwrites a valid observation'if c.get('value')is None else'field-specific source priority, verification and observation date; all candidates retained'}for c in candidates if c is not chosen and (chosen is None or c.get('value')!=chosen.get('value'))]
 return {'field':field,'chosen':chosen,'candidates':candidates,'conflicts':conflicts,'selection_rule':'independent verification, field source priority, evidence status, observation date, stable source/record tie-break; edits are not observations'}
