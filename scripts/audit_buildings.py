"""Audit actual published resources, source identities and a >=200 real-object set.

No independent field surveys, current roof crosswalk or LiDAR is available.
Numerical/model-source comparisons must not be called real-world accuracy.
"""
import json,sqlite3,struct,csv,math,hashlib
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from shapely.geometry import shape,Polygon,MultiLineString
from shapely.ops import unary_union,transform
from pyproj import Transformer
from nyc.normalize import esri_polygon
from nyc.coordinates import ecef_to_geographic,geographic_to_metric
from nyc.buildings import triangulate
from nyc.download import ROOT,atomic_json,sha,now

def read_glb(path):
 raw=path.read_bytes();magic,v,total=struct.unpack_from('<4sII',raw)
 if(magic,v,total)!=(b'glTF',2,len(raw)):raise ValueError('invalid GLB')
 n,kind=struct.unpack_from('<II',raw,12)
 if kind!=0x4e4f534a:raise ValueError('missing JSON chunk')
 obj=json.loads(raw[20:20+n]);return obj,raw[28+n:]
def array(obj,data,index):
 a=obj['accessors'][index];v=obj['bufferViews'][a['bufferView']];w={'VEC3':3,'SCALAR':1}[a['type']];t={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]
 return np.frombuffer(data,dtype=t,count=a['count']*w,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape((-1,w))

def main():
 out=ROOT/'assets/buildings-city';manifest=json.loads((out/'manifest.json').read_text());work=ROOT/'data/processed/building-stage4/city';db=sqlite3.connect(f'file:{work}/associations.sqlite?mode=ro',uri=True)
 source=sqlite3.connect(f'file:{ROOT}/data/processed/city/buildings.sqlite?mode=ro',uri=True)
 tiles_by_id={};full=Counter();allids=set();files=[];reasons=Counter();duplicate_pairs=[]
 for b in manifest['boroughs']:
  items=json.loads((out/b['index']).read_text());count=0
  for tile in items:
   prefix=out/b['id'];ids=tile['feature_ids']
   if len(ids)!=len(set(ids))or allids.intersection(ids):raise ValueError('duplicate published source object')
   allids.update(ids);count+=len(ids)
   for id in ids:tiles_by_id[id]=(b['id'],tile['id'])
   receipt=prefix/(tile['id']+'.receipt.json');r=json.loads(receipt.read_text())
   for name,digest in r['files'].items():
    path=prefix/name;actual=sha(path)
    if actual!=digest:raise ValueError('corrupt published resource: '+str(path))
    files.append({'path':str(path.relative_to(ROOT)),'sha256':actual,'bytes':path.stat().st_size})
  if count!=b['outlines']:raise ValueError('manifest count does not match actual IDs')
  full[b['id']]=count;print('RESOURCE_AUDIT',b['id'],count,flush=True)
 expected=db.execute("select count(*) from objects where state!='excluded_placeholder'").fetchone()[0]
 if expected!=len(allids):raise ValueError('source to output entity coverage mismatch')
 placeholders={id for(id,)in db.execute("select id from objects where state='excluded_placeholder'")}
 if allids.intersection(placeholders):raise ValueError('placeholder rendered as building')
 # Same-byte geometry duplicates are flagged, NEVER merged into one building.
 for digest,count in db.execute("select json_extract(metadata,'$.geometry_sha256'),count(*) from objects group by json_extract(metadata,'$.geometry_sha256') having count(*)>1"):
  ids=[id for(id,)in db.execute("select id from objects where json_extract(metadata,'$.geometry_sha256')=?",(digest,))]
  duplicate_pairs.append({'kind':'identical_serialized_source_geometry','geometry_sha256':digest,'ids':ids,'action':'retained distinct source identities; physical duplicate requires investigation'})
 selection=json.loads((ROOT/'data/processed/building-stage4/review-selection.json').read_text());reviews=[];overlaps=[];raw_cache={};geometry_max=0.;height_max=0.;raw_projection_max=0.;roof_area_max=0.
 for entry in selection['records']:
  r=entry['record'];id=r['id'];borrow,tileid=tiles_by_id[id];prefix=out/borrow;tilemeta=json.loads((prefix/(tileid+'.json')).read_text());meta=next(m for m in tilemeta['objects']if m['id']==id)
  stored=json.loads(db.execute('select geometry from objects where id=?',(id,)).fetchone()[0])
  if stored!=r['geometry']:raise ValueError('standard source footprint was replaced')
  sourcepath=ROOT/r['raw_record']['path']
  if str(sourcepath)not in raw_cache:
   if sha(sourcepath)!=r['raw_record']['sha256']:raise ValueError('raw checksum mismatch')
   raw_cache[str(sourcepath)]=json.loads(sourcepath.read_text())
  page=raw_cache[str(sourcepath)];actual=next((f for f in page['features']if f['attributes']['OBJECTID']==r['source_object_id']),None)
  if actual is None:raise ValueError('raw source reference missing')
  sr=actual['geometry'].get('spatialReference')or page['spatialReference'];wkid=sr.get('latestWkid')or sr['wkid']
  _,raw_fixed,_=esri_polygon(actual['geometry']['rings']);raw_metric=transform(Transformer.from_crs(wkid,32118,always_xy=True).transform,raw_fixed)
  raw_error=raw_metric.hausdorff_distance(shape(r['geometry']));raw_projection_max=max(raw_projection_max,raw_error)
  if raw_error>.10:raise ValueError('source transformation deviates > .10m')
  g=shape(r['geometry']);ps=[g]if g.geom_type=='Polygon'else list(g.geoms);area_delta=0.
  # A mathematical cap test verifies the triangulator; those caps are NOT roofs
  # and are NOT published without reliable roof evidence.
  for p in ps:
   triangles=triangulate(p);area_delta=max(area_delta,abs(sum(Polygon(t).area for t in triangles)-p.area))
  roof_area_max=max(roof_area_max,area_delta);review={'id':id,'borough':borrow,'selection_category':entry['selection_category'],'source_raw':r['raw_record'],'source_parts':len(ps),'source_holes':sum(len(p.interiors)for p in ps),'output_parts':len(meta['part_ids']),'source_height_raw_ft':r['height_raw_ft'],'canonical_height_m':None,'source_geometry_preserved_exactly':True,'triangulation_test_area_delta_m2':area_delta,'roof_test_is_not_a_published_roof':True,'reliable_roof':False,'verified_facade':False,'actual_ground_contact':'unresolved; no ground placement asserted','source_current_demolished_status':'unknown','parcel_context':entry.get('parcel_context')}
  review['raw_to_normalized_pipeline_deviation_m']=raw_error
  if review['source_parts']!=review['output_parts']:raise ValueError('lost component identity')
  for mode in ['strict','hypothesis']:
   obj,data=read_glb(prefix/f'{tileid}-{mode}.glb');feature=obj['extras']['feature_ids'].index(id);mat=np.array(obj['extras']['local_frame']['enu_to_ecef_column_major']).reshape((4,4),order='F');verts=[];heights=[];triangle_count=0
   for prim in obj['meshes'][0]['primitives']:
    pos=array(obj,data,prim['attributes']['POSITION']);ids=array(obj,data,prim['attributes']['_FEATURE_ID_0']).flatten();ix=array(obj,data,prim['indices']).flatten()
    if ix.max()>=len(pos):raise ValueError('invalid face index')
    subset=pos[ids==feature]
    if not len(subset):continue
    enu=subset[:,[0,2,1]]*np.array([1,-1,1]);ecef=(mat[:3,:3]@enu.T).T+mat[:3,3]
    xyz=[]
    for world in ecef:
     lon,lat,h=ecef_to_geographic(*world);x,y=geographic_to_metric(lon,lat);xyz.append((x,y));heights.append(h)
    if prim['mode']==1:verts=xyz
    else:
     tris=pos[ix].reshape((-1,3,3));face_ids=ids[ix].reshape((-1,3));selected=face_ids[:,0]==feature;tris=tris[selected];triangle_count+=len(tris)
     norm=array(obj,data,prim['attributes']['NORMAL'])[ix].reshape((-1,3,3))[selected,0]
     face=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0])
     if np.any(np.sum(face*norm,axis=1)<=0):raise ValueError('inverted/degenerate published triangle')
     if np.any(np.abs(norm[:,1])>.01):raise ValueError('unknown roof unexpectedly capped')
   lines=MultiLineString([verts[i:i+2]for i in range(0,len(verts),2)]);delta=lines.hausdorff_distance(g.boundary);geometry_max=max(geometry_max,delta)
   if delta>.10:raise ValueError('GPU geometry deviates from saved source > .10m')
   expected_height=meta['height_hypothesis_m']if mode=='hypothesis'and meta['height_hypothesis_m']is not None else 0
   dh=abs((max(heights)-min(heights))-expected_height);height_max=max(height_max,dh)
   if dh>.01:raise ValueError('hypothesis height not equal to stated assumption')
   review[mode]={'source_outline_deviation_m':delta,'height_span_error_vs_explicit_hypothesis_m':dh,'triangles':triangle_count,'roof_triangles':0}
  # Exact source intersections around reviewed records, including neighbouring
  # owner cells. Touching/shared walls are not treated as area overlap.
  x1,y1,x2,y2=g.bounds
  neighbours=source.execute('select b.id,b.payload from spatial s join buildings b on b.rowid=s.row_id where s.minx<=? and s.maxx>=? and s.miny<=? and s.maxy>=? and b.capture like ? and b.id!=?',(x2,x1,y2,y1,'2026-10-27-city:%',id))
  for other,payload in neighbours:
   ng=shape(json.loads(payload)['geometry']);area=g.intersection(ng).area
   if area>max(.01,min(g.area,ng.area)*1e-6):overlaps.append({'id':id,'other_id':other,'overlap_area_m2':area,'bounds_metric_m':list(g.bounds),'source_version':'2026-10-27-city','action':'review source footprints/temporal parts; do not merge or invent setbacks'})
  reviews.append(review)
  if len(reviews)%40==0:print('OBJECT_REVIEW',len(reviews),flush=True)
 report={'at':now(),'source_version':'2026-10-27-city','scope':'all captured source identities, not independently enumerated physical buildings','raw_source_records':sum(b['records']for b in manifest['boroughs']),'source_defined_entities':db.execute('select count(*) from objects').fetchone()[0],'geometry_parts':manifest['counts']['geometry_parts'],'published_outline_entities':len(allids),'published_outline_parts':manifest['counts']['published_outline_parts'],'excluded_placeholders':len(placeholders),'canonical_valid_height':0,'source_numeric_height_values':manifest['counts']['source_height_numeric_valid'],'reliable_roof_models':0,'verified_facades':0,'independent_real_world_verifications':0,'canonical_building_solids':0,'hypothesis_envelope_entities':manifest['counts']['hypothesis_eligible'],'ratios_denominator':'all 1,082,964 captured source records; also explicit nonplaceholder denominator below','ratios':{'source_outline_published':len(allids)/sum(b['records']for b in manifest['boroughs']),'canonical_valid_height':0,'reliable_roof':0,'verified_facade':0},'nonplaceholder_denominator':len(allids),'nonplaceholder_outline_coverage':1,'boroughs':manifest['borough_counts'],'reviewed_actual_objects':len(reviews),'review_counts':selection['selection_counts'],'review_actual_courtyard_candidates':selection['actual_courtyard_candidates'],'verified_complex_roofs_reviewed':0,'industrial_scope':'LandUse06 parcel-context candidates, not independently verified building use','source_outline_gpu_max_deviation_m':geometry_max,'hypothesis_height_span_max_error_m':height_max,'triangulation_area_max_error_m2':roof_area_max,'real_world_position_height_error':None,'source_geometry_exact_byte_duplicates':duplicate_pairs,'overlap_scope':'reviewed actual objects against exact source neighbours; NOT exhaustive all-city overlap audit','overlap_pairs_flagged':len(overlaps),'output_resource_files_verified':len(files),'ground_contact_floating_sinking':'not verified, global height/base unresolved','missing_inputs':['resolved height foot subtype','ground wall boundary and component heights','matched current roof/old-model crosswalk','acquired LAS/LAZ','current façade sources','world vertical registration'],'status':'five-borough outlines and explicit hypotheses published; verified building bodies/roof/facade delivery remains blocked'}
 report['raw_to_normalized_pipeline_max_deviation_m']=raw_projection_max
 atomic_json(ROOT/'reports/stage4/quality-report.json',report);atomic_json(out/'quality-report.json',report);atomic_json(ROOT/'reports/stage4/object-review.json',reviews);atomic_json(ROOT/'reports/stage4/overlaps.json',overlaps)
 with(ROOT/'reports/stage4/object-review.csv').open('w',newline='')as f:
  writer=csv.DictWriter(f,fieldnames=['id','borough','selection_category','source_parts','output_parts','source_holes','source_height_raw_ft','canonical_height_m','source_geometry_preserved_exactly','actual_ground_contact']);writer.writeheader();writer.writerows({k:r[k]for k in writer.fieldnames}for r in reviews)
 with(ROOT/'data/manifests/stage4/generated-files.jsonl').open('w')as f:
  for r in files:f.write(json.dumps(r)+'\n')
 print('QUALITY_AUDIT_COMPLETE',len(reviews),len(files),flush=True)
if __name__=='__main__':main()
