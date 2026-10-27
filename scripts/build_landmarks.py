"""Build only researched landmark representations; preserve all original city data."""
import json,math,os
from pathlib import Path
from nyc.download import ROOT,atomic_json,sha,now
from nyc.landmark_mesh import one_world,park432_grid

def main():
 out=ROOT/'assets/landmarks';out.mkdir(parents=True,exist_ok=True);entries=[];maps=[]
 for slug,make in [('one-world-trade-center',one_world),('432-park-avenue',park432_grid)]:
  source=ROOT/'landmarks'/slug;d=json.loads((source/'dossier.json').read_text());dims=json.loads((source/'dimensions.json').read_text());params={p['id']:p['value_m']for p in dims['parameters']}
  if any(p['evidence']['status']!='source_explicit'or not(ROOT/p['evidence']['path']).exists()for p in dims['parameters']):raise ValueError('unsupported model parameter')
  model=make(params,d['stable_building_id']);provenance={'dossier':f'landmarks/{slug}','dimension_evidence':dims,'kind':d['model_kind'],'reference_base_only':True,'world_ground_registered':False}
  raw,box,stats=model.glb(d['heading_radians_enu'],provenance);dest=out/slug;dest.mkdir(parents=True,exist_ok=True)
  tmp=dest/'model.glb.tmp';tmp.write_bytes(raw);os.replace(tmp,dest/'model.glb')
  # Dossier model is an ordinary copy: original source data is never overwritten.
  (source/'models/model.glb').write_bytes(raw)
  matrix=d['frame']['enu_to_ecef_column_major']
  tileset={'asset':{'version':'1.1','extras':{'local_metre_reference_inspection':True,'physical_world_ground_registered':False}},'geometricError':100,'root':{'boundingVolume':{'box':box},'transform':matrix,'geometricError':100,'refine':'ADD','children':[{'boundingVolume':{'box':box},'geometricError':0,'content':{'uri':'model.glb'}}]}}
  atomic_json(dest/'tileset.json',tileset)
  r=json.loads((source/'source-building.json').read_text());outline={'id':r['id'],'geometry_wgs84':r['geometry_wgs84'],'raw_record':r['raw_record'],'not_ground_wall_line':True}
  atomic_json(dest/'source-outline.json',outline)
  mapping={'landmark':slug,'building_id':d['stable_building_id'],'source_part_ids':[p['part_id']for p in r['parts']],'generated_components':[c['name']for c in model.components],'eligible':d['replacement_eligible_in_reference_inspector'],'hide_source_building_ids':[r['id']]if d['replacement_eligible_in_reference_inspector']else[],'physical_world_replacement_allowed':False,'scope':'explicit local reference inspector only; global datum not resolved','reason':d.get('replacement_block','One source part/one named entity only; never suppress adjacent WTC buildings')}
  if mapping['eligible']:
   if len(r['parts'])!=1:raise ValueError('cannot suppress multipart city object using single-part model')
   tiles=json.loads((ROOT/'assets/buildings-city/manhattan/tiles.json').read_text());tile=next(t for t in tiles if r['id']in t['feature_ids'])
   context_box=tile['box_local_enu_m']['strict']
   atomic_json(dest/'context.json',{'asset':{'version':'1.1'},'geometricError':100,'root':{'boundingVolume':{'box':context_box},'transform':tile['enu_to_ecef_column_major'],'geometricError':100,'refine':'ADD','children':[{'boundingVolume':{'box':context_box},'geometricError':0,'content':{'uri':'../../buildings-city/manhattan/'+tile['strict_glb']}}]}})
   mapping['context_source']={'content':'buildings-city/manhattan/'+tile['strict_glb'],'metadata':'buildings-city/manhattan/'+tile['metadata'],'expected_feature_ids':tile['feature_ids'],'source_sha256':sha(ROOT/'assets/buildings-city/manhattan'/tile['strict_glb'])}
  maps.append(mapping)
  d['model']='models/model.glb';d['model_sha256']=sha(dest/'model.glb');d['model_stats']=stats;d['statuses']['validation']='geometry_built_browser_pending';atomic_json(source/'dossier.json',d)
  for name in ['dossier.json','dimensions.json','references.json','materials.json','components.json']:
   atomic_json(dest/name,json.loads((source/name).read_text()))
  picks=[];c,s=math.cos(d['heading_radians_enu']),math.sin(d['heading_radians_enu'])
  for component in model.components:
   if component['mode']!=4:continue
   for tri in component['positions'].reshape((-1,3,3)):
    x,y,z=tri.mean(axis=0);picks.append([float(x*c-y*s),float(x*s+y*c),float(z)])
  entries.append({'slug':slug,'name':d['name'],'building_id':d['stable_building_id'],'tileset':slug+'/tileset.json','dossier':slug+'/dossier.json','dimensions':slug+'/dimensions.json','frame':d['frame'],'height_m':params['total_height_m']if slug=='one-world-trade-center'else params['roof_height_m'],'roof_height_m':params['roof_height_m'],'representation':d['model_kind'],'replacement':mapping,'stats':stats,'sha256':d['model_sha256'],'pick_points_local_enu_m':picks})
  print('LANDMARK_BUILT',slug,stats,flush=True)
 manifest={'schema_version':5,'created_at':now(),'requested_dossiers':29,'published_representations':len(entries),'fully_detailed_landmarks_completed':0,'research_completed':0,'massing_completed':0,'facades_completed':0,'validation_completed':0,'model_kind_counts':{'partial_faceted_massing':1,'structural_grid_fragment':1},'no_generic_named_boxes':True,'physical_world_base_registered':False,'neutral_fixed_light':True,'references_not_distributed':'Original photos/PDF retained only under local raw; public links/checksums and small factual quotes in dossiers.','landmarks':entries}
 queue=json.loads((ROOT/'landmarks/queue.json').read_text())
 for e in queue['landmarks']:e['statuses']=json.loads((ROOT/'landmarks'/e['slug']/'dossier.json').read_text())['statuses']
 atomic_json(out/'research-queue.json',queue)
 atomic_json(out/'manifest.json',manifest);atomic_json(ROOT/'data/manifests/stage5/replacement-map.json',maps);atomic_json(ROOT/'data/manifests/stage5/models.json',manifest);print('PARTIAL_REPRESENTATIONS',len(entries),'COMPLETED_DETAILED_MODELS',0)
if __name__=='__main__':main()
