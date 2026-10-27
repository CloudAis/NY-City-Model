"""Source inventory and honest, independent research/massing/facade/check status."""
import json,math,struct,csv
from pathlib import Path
import numpy as np
from shapely.geometry import shape,MultiPoint
from nyc.download import ROOT,atomic_json,sha,now
from nyc.coordinates import ecef_to_geographic,geographic_to_metric

def glb_data(path):
 raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];return json.loads(raw[20:20+n]),raw[28+n:]
def positions(g,b,primitive):
 a=g['accessors'][primitive['attributes']['POSITION']];v=g['bufferViews'][a['bufferView']];return np.frombuffer(b,dtype='<f4',offset=v['byteOffset'],count=a['count']*3).reshape((-1,3))

def main():
 browser=json.loads((ROOT/'reports/stage5/browser.json').read_text());tests=(ROOT/'reports/stage5/tests.log').read_text()
 if browser['errors']or len(browser['checks'])<6 or 'Ran 36 tests'not in tests or not tests.rstrip().endswith('OK'):raise ValueError('actual checks not complete')
 root=ROOT/'assets/landmarks';manifest=json.loads((root/'manifest.json').read_text());registry=[];raw=ROOT/'data/raw/stage5/research'
 for receipt in sorted(raw.glob('*.receipt.json')):
  meta=json.loads(receipt.read_text());p=receipt.with_name(receipt.name.removesuffix('.receipt.json'))
  if sha(p)!=meta['sha256']:raise ValueError('retained source changed')
  is_discovery=(p.name.startswith('discovery-')or p.name.endswith('-home.html')or p.name in ['som-projects.html','vinoly-works.html'])and p.name!='432-home.html'
  registry.append({'id':p.stem,'path':str(p.relative_to(ROOT)),'url':meta['final_url'],'sha256':meta['sha256'],'bytes':p.stat().st_size,'downloaded_at':meta['download_completed_at'],'publication_date':None,'observation_date':None,'source_version_label':'2026-09-16 filename, not verified release/observation date'if'2026-09-16'in p.name else None,'role':'discovery only, not dimension evidence'if is_discovery else'primary/engineering reference; per-parameter attribution in dossier','license':'reference-only; original private photos/PDF/HTML are not redistributed in runtime/source package','runtime_texture':False,'horizontal_units':'source-specific; no CRS inferred from extension','model_units':'metre, shared module','vertical_reference':'local building reference, NOT approved world ground'})
 atomic_json(ROOT/'data/manifests/stage5/sources.json',{'schema_version':5,'at_utc':now(),'target_date':'2026-10-28 Asia/Singapore','raw_originals_preserved':True,'sources':registry,'date_rule':'Filename, copyright, web crawl and publication/observation dates are distinct. No dated current four-side photo survey was obtained.'})
 records=[];max_gpu_error=0
 for item in manifest['landmarks']:
  slug=item['slug'];folder=ROOT/'landmarks'/slug;dims=json.loads((folder/'dimensions.json').read_text());p={p['id']:p['value_m']for p in dims['parameters']};g,b=glb_data(root/slug/'model.glb')
  clouds=[positions(g,b,c)for c in g['meshes'][0]['primitives']];h=max(float(a[:,1].max())for a in clouds);expected=p.get('total_height_m',p['roof_height_m']);error=abs(h-expected);max_gpu_error=max(max_gpu_error,error)
  if error>.01:raise ValueError('serialized model height differs from explicit parameters')
  view_records=[v for v in browser['generatedViews']if v['slug']==slug]
  if len(view_records)!=6:raise ValueError('missing actual generated view')
  validation={'research_complete':False,'massing_complete':False,'facade_complete':False,'validation_complete':False,'runtime_geometry_checks_passed':True,'generated_views':view_records,'calibrated_reference_images':0,'source_reference_coverage':{k:'missing dated/calibrated direction reference'for k in['north','east','south','west','high','street']},'key_dimensions':{'model_top_m':h,'selected_source_top_m':expected,'gpu_numeric_height_error_m':error,'independent_reality_error_m':None},'checks':['36 actual Python checks','six actual rendered directions','stable source ID retained','true north/ECEF/ENU frame kept','neutral fixed light, no fog/bloom','explicit source conflicts and missing components preserved'],'pixel_error_is_dimension_error':False,'original_ground_datum_resolved':False,'uncompleted':'source conflicts, actual wall/ground contact, full facade/crown and all dated direction evidence'}
  if slug=='one-world-trade-center':
   # Compare actual serialized model-base vertices against the retained source
   # overhead outline. This is not evidence that the outline is a ground wall.
   bottom=clouds[0][abs(clouds[0][:,1])<1e-6];enu=bottom[:,[0,2,1]]*np.array([1,-1,1]);matrix=np.array(item['frame']['enu_to_ecef_column_major']).reshape((4,4),order='F');world=enu@matrix[:3,:3].T+matrix[:3,3];xy=[]
   for vertex in world:
    lon,lat,_=ecef_to_geographic(*vertex);xy.append(geographic_to_metric(lon,lat))
   base=MultiPoint(xy).convex_hull;source=shape(json.loads((folder/'source-building.json').read_text())['geometry'])
   validation['source_overhead_outline_comparison']={'model_base_area_m2':base.area,'source_overhead_area_m2':source.area,'hausdorff_deviation_m':base.boundary.hausdorff_distance(source.boundary),'meaning':'source overhead outline vs evidence-selected square base, NOT a real wall-line survey; competing205/200ft source widths remain explicit'}
  atomic_json(folder/'validation.json',validation);atomic_json(root/slug/'validation.json',validation)
  dossier=json.loads((folder/'dossier.json').read_text());dossier['statuses']['validation']='source_geometry_runtime_checked_reality_open';atomic_json(folder/'dossier.json',dossier);atomic_json(root/slug/'dossier.json',dossier)
  refs=json.loads((folder/'references.json').read_text())
  for entry in refs['sources']:
   if entry['id']=='wtc-owner-2026-plan':entry['source_version_label']='2026-09-16 filename';entry['publication_date']=None;entry['date_basis']='filename is not actual publication or observation date'
  # Inventory actually acquired photographs without inventing azimuth/date.
  photos=[]
  for image in sorted(raw.glob('1wtc-view-*.jpg'if slug=='one-world-trade-center'else'432-*.jpg')):
   receipt=json.loads(image.with_name(image.name+'.receipt.json').read_text());photos.append({'path':str(image.relative_to(ROOT)),'url':receipt['final_url'],'sha256':receipt['sha256'],'observation_date':None,'camera_calibrated':False,'azimuth':None,'use':'qualitative only; sketches and retouched images not metric survey'})
  refs['unoriented_reference_images']=photos
  for direction in refs['views']:
   refs['views'][direction]={'reference':None,'capture_date':None,'calibrated':False,'status':'No dated/calibrated direction-specific reference; available photos separately inventoried for qualitative review.'}
  if slug=='one-world-trade-center':
   refs['views']['high']={'reference':'data/raw/stage5/research/1wtc-view-2.jpg','capture_date':None,'calibrated':False,'status':'acquired oblique roof photograph; camera/date unknown, qualitative only'}
   refs['views']['street']={'reference':'data/raw/stage5/research/1wtc-view-3.jpg','capture_date':None,'calibrated':False,'status':'acquired podium/street photograph; camera/date unknown, qualitative only'}
  else:
   refs['views']['north']={'reference':'data/raw/stage5/research/432-full-tower.jpg','capture_date':None,'calibrated':False,'status':'north/northwest sector inferred from Central Park foreground; exact azimuth/date unverified; retouched-sky filename; qualitative only'}
   refs['views']['street']={'reference':'data/raw/stage5/research/432-exterior.jpg','capture_date':None,'calibrated':False,'status':'retail-cube/site reference, NOT tower facade; camera/date unknown'}
  validation['source_reference_coverage']=refs['views']
  atomic_json(folder/'validation.json',validation);atomic_json(root/slug/'validation.json',validation)
  atomic_json(folder/'references.json',refs);atomic_json(root/slug/'references.json',refs)
  records.append({'slug':slug,'building_id':item['building_id'],'representation':item['representation'],'model_sha256':sha(root/slug/'model.glb'),'height_numeric_error_m':error,'generated_view_count':6,'fine_model_complete':False,'conflicts':dims.get('conflicts',[]),'missing':json.loads((folder/'components.json').read_text())['missing']})
 # Sources actually acquired for the two next research entries.
 for slug,names in [('empire-state-building',['esb-history.html','esb-facts.html','esb-design.html']),('111-west-57th-street',['111-shop.html'])]:
  folder=ROOT/'landmarks'/slug;refs=json.loads((folder/'references.json').read_text());refs['sources']=[r for r in registry if Path(r['path']).name in names];atomic_json(folder/'references.json',refs)
 report={'at_utc':now(),'requested_dossiers':29,'partially_researched':4,'research_complete':0,'published_partial_representations':2,'main_body_volume_representations':1,'structural_grid_fragments':1,'massing_complete':0,'facade_complete':0,'fine_model_complete':0,'complete_validation':0,'actual_rendered_views':12,'calibrated_reference_images':0,'gpu_numeric_max_height_error_m':max_gpu_error,'independent_reality_error_m':None,'world_ground_registered':False,'replacement_actual_test':'one target hidden,19 neighbours retained, restored when model off;432 fragment replacement refused','source_records':len(registry),'records':records,'legacy_model_candidates':1288,'legacy_reused_models':0,'legacy_reason':'2014 geometry candidates include duplicate representations; unit/datum/current identity/ground not reconciled; bbox count is NOT building count','checks':{'python':36,'browser_groups':len(browser['checks']),'local_requests_only':True}}
 atomic_json(ROOT/'reports/stage5/quality.json',report);atomic_json(root/'quality.json',report)
 with(ROOT/'reports/stage5/dimensions.csv').open('w',newline='')as f:
  writer=csv.writer(f,lineterminator='\n');writer.writerow(['landmark','parameter','selected_m','source_value','source_unit','source','uncertainty_m','independent_reality_verified'])
  for item in manifest['landmarks']:
   for p in json.loads((ROOT/'landmarks'/item['slug']/'dimensions.json').read_text())['parameters']:writer.writerow([item['slug'],p['id'],p['value_m'],p['source_value'],p['source_unit'],p['evidence']['url'],p['uncertainty_m'],False])
 print('LANDMARK_REPORT',json.dumps({k:v for k,v in report.items()if k not in['records']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
