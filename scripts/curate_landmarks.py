"""Curated parameter evidence, checked against actually retained primary text.

No search snippet is a parameter source; no private reference image is a texture.
"""
import json,re,sqlite3,math
from pathlib import Path
from shapely.geometry import shape
from nyc.download import ROOT,atomic_json,sha,now
from nyc.coordinates import metric_to_geographic,LocalFrame,projected_vertices_to_local,INTERNATIONAL_FOOT

FILES={
 'wtc-engineer':'1wtc-structure-engineers.html','wtc-engineer-2012':'1wtc-2012-engineering.pdf',
 'wtc-architect':'1wtc-som.html','wtc-architect-zh':'1wtc-som-zh.html','wtc-owner':'1wtc-wtc.html',
 'wtc-owner-2026-plan':'OneWTC_StackingPlan_2026-09-16.pdf',
 'park-engineer':'432-structure-engineers.html','park-architect':'432-vinoly.html','park-owner':'432-home.html',
 'park-architect-pdf':'432-vinoly-brochure.pdf','nist-unit':'nist-foot.html',
 'esb-owner-facts':'esb-facts.html','esb-owner-design':'esb-design.html','steinway-architect':'111-shop.html'}

def evidence(source,quote,status='source_explicit',note=''):
 p=ROOT/'data/raw/stage5/research'/FILES[source]
 if not p.exists():raise ValueError('source not actually acquired: '+str(p))
 if p.suffix=='.html':
  text=re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',p.read_text()))
  if quote not in text:raise ValueError('claimed quote absent: '+source+' '+quote)
 receipt=json.loads(p.with_name(p.name+'.receipt.json').read_text())
 return {'source':source,'path':str(p.relative_to(ROOT)),'sha256':sha(p),'url':receipt['final_url'],'quote':quote,'status':status,'note':note,'independently_verified':False,'observation_date':None,'downloaded_at':receipt['download_completed_at'],'reuse':'reference-only; no original photos/PDF redistributed as model textures'}

def parameter(name,value_m,source,quote,quantity='length',note='',source_value=None,source_unit='metre',uncertainty=None):
 return {'id':name,'value_m':value_m,'quantity':quantity,'source_value':value_m if source_value is None else source_value,'source_unit':source_unit,'evidence':evidence(source,quote,note=note),'uncertainty_m':None,'project_review_tolerance_m':uncertainty,'uncertainty_note':'Publisher parameter-specific accuracy unknown. Project review tolerances are modelling choices, NOT measured source/reality uncertainty. Source conflicts are separately retained.','unit_conversion':'international foot * 0.3048 exactly per NIST, structural architecture NOT geodetic surveying'if source_unit=='international_foot'else'none'}

def set_dossier(slug,fields):
 p=ROOT/'landmarks'/slug/'dossier.json';d=json.loads(p.read_text());d.update(fields);atomic_json(p,d);return d

def identity(id):
 db=sqlite3.connect(f'file:{ROOT}/data/processed/city/buildings.sqlite?mode=ro',uri=True)
 rows=list(db.execute('select payload from buildings where id=?',(id,)));db.close()
 if len(rows)!=1:raise ValueError('not unique source identity')
 r=json.loads(rows[0][0]);g=shape(r['geometry']);cx,cy=g.centroid.coords[0];lon,lat=metric_to_geographic(cx,cy);frame=LocalFrame.at(lon,lat,0)
 ring=list(g.exterior.coords);edge=max(zip(ring,ring[1:]),key=lambda v:math.dist(*v));enu=projected_vertices_to_local(edge,0,frame);v=enu[1]-enu[0];heading=math.atan2(v[1],v[0])
 return r,frame,heading

def main():
 e_unit=evidence('nist-unit','exclusively for geodetic surveying',note='1959 international foot is legally binding for industry; this does not resolve unspecified legacy GIS height fields')
 foot=INTERNATIONAL_FOOT
 wtc=[
 parameter('base_width_m',205*foot,'wtc-engineer-2012','205-foot (62.5-meter) square plan',source_value=205,source_unit='international_foot',uncertainty=.7,note='2012 construction-design source; current source footprint ~62m supports this better than 2014 prose 200ft. Conflict retained, NOT resolved by choosing newer page.'),
 parameter('podium_top_m',190*foot,'wtc-engineer-2012','office levels start 190 feet (58meters)',source_value=190,source_unit='international_foot',uncertainty=.5),
 parameter('roof_width_m',150*foot,'wtc-architect','150-foot-by-150-foot square',source_value=150,source_unit='international_foot',uncertainty=1.524,note='Current architect page selected; 2012 engineer gives145ft. Roof dimension conflict remains unresolved; model is evidence-bound partial massing.'),
 parameter('roof_height_m',1368*foot,'wtc-engineer','main roof at 1368 feet (417m)',source_value=1368,source_unit='international_foot',uncertainty=.5,quantity='height_above_ground'),
 parameter('spire_above_roof_m',408*foot,'wtc-engineer','408 feet (124m) tall spire',source_value=408,source_unit='international_foot',uncertainty=.5,quantity='spire_extent_above_roof',note='Axis only; diameter, ring radii, beacon and cable attachments unknown. SOM441ft includes a different described extent; do not subtract it from total to get roof.'),
 parameter('total_height_m',1776*foot,'wtc-engineer','1,776 feet (541 m)',source_value=1776,source_unit='international_foot',uncertainty=.5,quantity='architectural_top_above_ground')
 ]
 r,frame,heading=identity('nyc:footprints:doitt:1114961')
 p=ROOT/'landmarks/one-world-trade-center'
 d=set_dossier(p.name,{'address':'285 Fulton St, New York, NY, 10007','address_source':'wtc-owner','stable_building_id':r['id'],'bin':r['bin'],'longitude_latitude_degrees':[frame.longitude_deg,frame.latitude_deg],'identity_evidence':{'source_name':r['name'],'raw_record':r['raw_record'],'method':'unique named source entity + owner address and Lower Manhattan location; no nearest-neighbour replacement of other WTC buildings'},'statuses':{'research':'partial_conflicts_and_missing_views','massing':'partial_evidence_bound_main_volume','facade':'not_completed','validation':'pending_runtime_and_geometry'},'heading_radians_enu':heading,'frame':frame.manifest(),'model_kind':'eight-facet main volume + roof + spire axis; not complete detailed landmark','ground_placement':'local zero reference only; physical world ground unresolved','replacement_eligible_in_reference_inspector':True})
 atomic_json(p/'dimensions.json',{'parameters':wtc,'unit_evidence':e_unit,'antenna_tip_height':None,'roof_not_total_height':True,'conflicts':[{'parameter':'base_width','candidates':[{'source':'wtc-engineer-2012','feet':205},{'source':'wtc-engineer','feet':200}],'selection':'2012 engineering geometry, supported by current saved source outline; independent wall-line survey missing'},{'parameter':'roof_width','candidates':[{'source':'wtc-engineer-2012','feet':145},{'source':'wtc-architect','feet':150}],'selection':'architect webpage describes completed building; no independent roof survey, 5ft uncertainty retained'},{'parameter':'spire_extent','candidates':[{'source':'wtc-engineer','above_roof_feet':408},{'source':'wtc-architect','extent_feet':441}],'selection':'408 explicitly above main roof;441 description includes communication assembly in steel paper; not silently treated as same base'}]})
 atomic_json(p/'components.json',{'components':[{'id':k,'evidence_parameters':v}for k,v in [('podium',['base_width_m','podium_top_m']),('eight-triangular-facets',['base_width_m','podium_top_m','roof_width_m','roof_height_m']),('roof-plane-45-degree-square',['roof_width_m','roof_height_m']),('spire-axis-only-diameter-unknown',['roof_height_m','total_height_m'])]],'missing':['entrance widths/canopies','glass fin spacing','curtain-wall counts/layout','communications ring diameters/heights','spire diameter/cables/beacon','ground datum'],'geometry_sources_not_one_era':'2012 design baseline + completed architect description + 2026 owner qualitative diagram; all conflicts explicit'})
 # Preserve real source outline for comparison, not for deforming the model.
 atomic_json(p/'source-building.json',r)
 park=[
 parameter('width_m',93.5*foot,'park-engineer','width and length of 93.5 feet',source_value=93.5,source_unit='international_foot',uncertainty=.15),
 parameter('grid_pitch_m',15.5*foot,'park-engineer','15.5-foot by 15.5-foot grid',source_value=15.5,source_unit='international_foot',uncertainty=.05),
 parameter('roof_height_m',1396*foot,'park-engineer','1,396 feet high',source_value=1396,source_unit='international_foot',quantity='height_above_ground',uncertainty=.1),
 parameter('window_edge_m',10*foot,'park-owner',"""10'x10' insulated glass windows""",source_value=10,source_unit='international_foot',uncertainty=.15,note='NOT emitted: engineer mechanical-floor elevations unknown; architect approximate10m² differs from owner100ft².')
 ]
 r,frame,heading=identity('nyc:footprints:doitt:1119374');p=ROOT/'landmarks/432-park-avenue'
 set_dossier(p.name,{'address':'432 Park Avenue, New York, NY10022','address_source':'park-owner','stable_building_id':r['id'],'bin':r['bin'],'longitude_latitude_degrees':None,'project_entity_reference_longitude_latitude_degrees':[frame.longitude_deg,frame.latitude_deg],'heading_radians_enu':heading,'frame':frame.manifest(),'identity_evidence':{'raw_record':r['raw_record'],'scope':'source project entity includes larger podium; exact tower centre is NOT established'},'statuses':{'research':'partial_missing_mechanical_elevations','massing':'structural_grid_fragment_only','facade':'not_completed','validation':'pending_runtime_and_dimensions'},'model_kind':'line-only structural grid study, no concrete member volumes or glazing','replacement_eligible_in_reference_inspector':False,'replacement_block':'source polygon includes tower + podium; frame fragment must not erase them or adjoining BIN1035787','ground_placement':'local inspection only; no tower position assertion'})
 atomic_json(p/'dimensions.json',{'parameters':park,'unit_evidence':e_unit,'open_mechanical_bands':{'count':5,'stories_each':2,'evidence':evidence('park-engineer','five two-story open floors'),'absolute_elevations_m':None},'spire_height':None,'antenna_height':None,'grid_phase':'local zero for pitch study only, not verified floor elevation','conflicts':[{'field':'architect_map','raw_longitude_latitude':[-73.40133438300779,40.65330897450164],'action':'reject as NYC tower location; retained original page'},{'field':'window_area','architect_approx_m2':10,'owner_10ft_square_m2':(10*foot)**2,'action':'record disagreement; do not claim facade geometry complete'},{'field':'residence_counts','architect_intro':104,'architect_body':106,'action':'not used for geometry'}]})
 atomic_json(p/'components.json',{'components':[{'id':'exposed-concrete-grid-centrelines-only','evidence_parameters':['width_m','grid_pitch_m','roof_height_m'],'representation':'LINES, no member thickness inferred'}],'missing':['retail podiums','tower exact site position','five open-floor absolute levels','concrete section dimensions','window/door distribution','entrance and crown details'],'no_filled_unknown_mechanical_bands':True})
 atomic_json(p/'source-building.json',r)
 for slug,sources in [('one-world-trade-center',['wtc-engineer','wtc-engineer-2012','wtc-architect','wtc-architect-zh','wtc-owner','wtc-owner-2026-plan','nist-unit']),('432-park-avenue',['park-engineer','park-architect','park-owner','park-architect-pdf','nist-unit'])]:
  p=ROOT/'landmarks'/slug;refs=json.loads((p/'references.json').read_text());refs['sources']=[]
  for key in sources:
   path=ROOT/'data/raw/stage5/research'/FILES[key];receipt=json.loads(path.with_name(path.name+'.receipt.json').read_text());refs['sources'].append({'id':key,'path':str(path.relative_to(ROOT)),'sha256':sha(path),'url':receipt['final_url'],'downloaded_at':receipt['download_completed_at'],'observation_date':None,'publication_date':'2026-09-16'if key=='wtc-owner-2026-plan'else'2012-11'if key=='wtc-engineer-2012'else'2014-04'if key=='wtc-engineer'else None,'license':'reference-only; redistribution permission not established','primary':True})
  refs['views']['high'].update({'status':'qualitative owner/architect reference available; no calibrated camera','calibrated':False})
  refs['views']['street'].update({'status':'partial photographs/description, widths/camera not calibrated','calibrated':False})
  atomic_json(p/'references.json',refs)
  names=['glass','metal']if slug=='one-world-trade-center'else['white exposed concrete','glass']
  atomic_json(p/'materials.json',{'materials':[{'material':m,'source':'wtc-architect'if slug=='one-world-trade-center'else'park-engineer','status':'source_explicit material class, display color/roughness estimated, not measured albedo'}for m in names],'runtime':'neutral opaque glass/metal for WTC; structural line colour for432; no copied photos or fictitious interiors'})
 # Actual research for other obtained primary sources is recorded separately.
 set_dossier('empire-state-building',{'stable_building_id':'nyc:footprints:doitt:778052','statuses':{'research':'partial_owner_sources_acquired','massing':'not_started','facade':'not_started','validation':'not_started'},'known_height_caution':'owner1,250ft highest occupied/380m and1,454ft antenna/443m; main-body/setback/roof split still unverified; no model generated'})
 set_dossier('111-west-57th-street',{'statuses':{'research':'partial_architect_source_acquired','massing':'not_started','facade':'not_started','validation':'not_started'},'known_height_caution':'architect1428ft total is not an entire uniform tower extrusion; terra-cotta finials/setbacks need dimensions'})
 print('CURATED_WTC_AND_432_WITH_EXPLICIT_GAPS')
if __name__=='__main__':main()
