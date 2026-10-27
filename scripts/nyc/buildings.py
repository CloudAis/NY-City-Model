"""Evidence-gated building geometry. An envelope is NOT a verified building.

Full source polygons, including holes and multipart identities, are retained.
No parcel floors, random heights, invented setbacks or historical models are used.
"""
import json,math,struct
import numpy as np
from shapely import constrained_delaunay_triangles
from shapely.geometry import shape,Polygon
from shapely.geometry.polygon import orient
from .coordinates import LocalFrame,metric_to_geographic,projected_vertices_to_local,INTERNATIONAL_FOOT,US_SURVEY_FOOT

VERSION='0.4.0-evidence-gated'
BOROUGHS=['manhattan','bronx','brooklyn','queens','staten-island']
NON_BODY_CODES={1000:'parking',1001:'gas_station_canopy',1002:'storage_tank',1006:'cantilever_base_unknown',2110:'skybridge_deck_unknown',5100:'under_construction'}

def polygons(geometry):
 g=shape(geometry)
 if g.is_empty or not g.is_valid or g.geom_type not in ('Polygon','MultiPolygon'):raise ValueError('damaged/nonpolygon source geometry')
 return list(g.geoms)if g.geom_type=='MultiPolygon'else[g]

def classify(r):
 ps=polygons(r['geometry']);raw=r.get('height_raw_ft');valid_height=isinstance(raw,(int,float))and not isinstance(raw,bool)and math.isfinite(raw)and 0<raw<=2500 and r.get('height_status')=='valid'
 code=int(r.get('feature_code')or 0);placeholder=r.get('placeholder')or code==1003
 reasons=['foot_subtype_unresolved','base_elevation_datum_unresolved','overhead_outline_not_verified_wall_line','roof_components_unknown','observation_date_unknown']
 if placeholder:reasons=['official_placeholder_triangle']
 elif code in NON_BODY_CODES:reasons.append(NON_BODY_CODES[code])
 if not valid_height:reasons.append('anomalous_height'if r.get('height_status')=='anomalous_range'else'missing_height')
 b=[p.bounds for p in ps];bounds=[min(x[0]for x in b),min(x[1]for x in b),max(x[2]for x in b),max(x[3]for x in b)]
 if not(270000<=bounds[0]<=bounds[2]<=340000 and 35000<=bounds[1]<=bounds[3]<=90000):reasons.append('outside_expected_city_bounds')
 eligible=not placeholder and valid_height and code not in NON_BODY_CODES and 'outside_expected_city_bounds'not in reasons
 geo=r['geometry_wgs84'];first=geo['coordinates'][0]if geo['type']=='Polygon'else geo['coordinates'][0][0]
 pick=[[(a[k]+b[k])/2 for k in range(2)]for a,b in list(zip(first,first[1:]))[:6]]
 return {'id':r['id'],'source_id':r['source_id'],'source_object_id':r['source_object_id'],'bin':r.get('bin'),'base_bbl':r.get('base_bbl'),'name':r.get('name'),'borough':r['borough'],'source_version':r['source_version'],'raw_record':r['raw_record'],'feature_code':code,'placeholder':bool(placeholder),'state':'excluded_placeholder'if placeholder else'source_outline_only','reasons':reasons,'semantic_level':'outline_only','render_lod':'full_source_outline_no_simplification','source_outline_kind':'overhead_outer_perimeter; not verified ground-wall intersection','canonical_height_m':None,'relative_height_raw_ft':raw,'height_evidence_status':'source_explicit_unit_unresolved'if valid_height else'unknown_or_anomalous','height_hypothesis_m':raw*INTERNATIONAL_FOOT if eligible else None,'height_hypothesis_interval_m':[raw*INTERNATIONAL_FOOT,raw*US_SURVEY_FOOT]if valid_height else None,'hypothesis_status':'estimated_unit_and_vertical_envelope_NOT_verified_building'if eligible else'not_eligible','ground_ellipsoid_m':None,'roof_status':'unknown','facade_status':'unknown','observation_date':r.get('observation_date'),'last_edited_at':r.get('last_edited_at'),'historical_model_match':None,'part_ids':[p['part_id']for p in r['parts']],'polygon_parts':len(ps),'interior_rings':sum(len(p.interiors)for p in ps),'vertices':sum(len(r.coords)-1 for p in ps for r in[p.exterior,*p.interiors]),'area_m2':sum(p.area for p in ps),'bounds_metric_m':bounds,'reference_pick_points':pick,'repair':r.get('repair'),'geometry_sha256':__import__('hashlib').sha256(json.dumps(r['geometry'],separators=(',',':')).encode()).hexdigest()}

def triangulate(poly):
 """Constrained triangles preserve concavities/holes; never unconstrained hull."""
 if not isinstance(poly,Polygon)or not poly.is_valid:raise ValueError('valid polygon required')
 triangles=list(constrained_delaunay_triangles(poly).geoms)
 if abs(sum(t.area for t in triangles)-poly.area)>max(1e-7,poly.area*1e-9):raise ValueError('triangulation area mismatch')
 if any(not poly.covers(t)for t in triangles):raise ValueError('triangle escapes source or seals courtyard')
 return [list(orient(t,sign=1).exterior.coords)[:3]for t in triangles]

def projected_shell(poly,height,cap_evidence=False):
 """Isolated structural mesh; cap_evidence must be explicit.

 Published source-height hypotheses use NO caps: unknown roofs remain open.
 Real components must each have their own footprint/base/height evidence.
 """
 if not math.isfinite(height)or height<=0:raise ValueError('positive evidenced/explicit hypothesis height required')
 p=orient(poly,sign=1);triangles=[]
 for ring in[p.exterior,*p.interiors]:
  for a,b in zip(ring.coords, list(ring.coords)[1:]):
   if a==b:continue
   # Exterior CCW and hole CW both put solid on the left, exterior normal right.
   a0=(*a[:2],0);b0=(*b[:2],0);a1=(*a[:2],height);b1=(*b[:2],height)
   triangles.extend([[a0,b0,b1],[a0,b1,a1]])
 if cap_evidence:
  for t in triangulate(p):
   triangles.append([(*v[:2],height)for v in t])
   triangles.append([(*v[:2],0)for v in reversed(t)])
 return np.asarray(triangles,dtype=np.float64)

def glb(records,origin_xy,mode='strict'):
 """One owner tile per complete source object. No geometry clipping at edges."""
 if mode not in ('strict','hypothesis'):raise ValueError('unknown representation')
 f=LocalFrame.at(*metric_to_geographic(*origin_xy),0);lines=[];line_ids=[];triangles=[];tri_ids=[];parts=[]
 for feature,(meta,geometry)in enumerate(records):
  part_stats=[]
  for i,p in enumerate(polygons(geometry)):
   xy=[] 
   for ring in[p.exterior,*p.interiors]:
    for a,b in zip(ring.coords,list(ring.coords)[1:]):xy.extend([a[:2],b[:2]])
   xyz=projected_vertices_to_local(xy,.25,f);lines.extend(xyz[:,[0,2,1]]*np.array([1,1,-1]));line_ids.extend([feature]*len(xyz))
   count=0
   if mode=='hypothesis'and meta['height_hypothesis_m']is not None:
    mesh=projected_shell(p,meta['height_hypothesis_m'],False);flat=mesh.reshape((-1,3));enu=projected_vertices_to_local(flat[:,:2],flat[:,2]+.25,f)
    triangles.extend(enu[:,[0,2,1]]*np.array([1,1,-1]));tri_ids.extend([feature]*len(enu));count=len(mesh)
   part_stats.append({'part_id':meta['part_ids'][i],'triangles':count,'interior_rings':len(p.interiors),'roof_triangles':0})
  parts.append({'id':meta['id'],'parts':part_stats})
 if not lines:raise ValueError('empty tile')
 binary=bytearray();views=[];accessors=[];primitives=[]
 def buf(raw,target=None):
  binary.extend(b'\0'*((-len(binary))%4));offset=len(binary);binary.extend(raw);v={'buffer':0,'byteOffset':offset,'byteLength':len(raw)}
  if target:v['target']=target
  views.append(v);return len(views)-1
 def attribute(array,kind,component):
  v=buf(array.tobytes(),34962);entry={'bufferView':v,'componentType':component,'count':len(array),'type':kind}
  if kind=='VEC3':entry.update(min=array.min(axis=0).tolist(),max=array.max(axis=0).tolist())
  accessors.append(entry);return len(accessors)-1
 def primitive(vertices,ids,mode,material):
  pos=np.asarray(vertices,dtype='<f4').reshape((-1,3));fid=np.asarray(ids,dtype='<u4');attrs={'POSITION':attribute(pos,'VEC3',5126),'_FEATURE_ID_0':attribute(fid,'SCALAR',5125)}
  if mode==4:
   v=pos.reshape((-1,3,3));norm=np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]);length=np.linalg.norm(norm,axis=1)
   if np.any(length<1e-9):raise ValueError('degenerate triangle')
   norm=np.repeat(norm/length[:,None],3,axis=0).astype('<f4');attrs['NORMAL']=attribute(norm,'VEC3',5126)
  # Explicit indexed primitives, including >65535 vertex cases.
  ix=np.arange(len(pos),dtype='<u4');view=buf(ix.tobytes(),34963);accessors.append({'bufferView':view,'componentType':5125,'count':len(ix),'type':'SCALAR','min':[0],'max':[len(pos)-1]})
  primitives.append({'attributes':attrs,'indices':len(accessors)-1,'mode':mode,'material':material,'extensions':{'EXT_mesh_features':{'featureIds':[{'featureCount':len(records),'attribute':0,'propertyTable':0,'label':'building'}]}}})
  return pos
 allpoints=[primitive(lines,line_ids,1,0)]
 if triangles:allpoints.append(primitive(triangles,tri_ids,4,1))
 props={};schema={}
 for field in['id','source_id','bin','borough','semantic_level','state','relative_height_raw_ft','canonical_height_m','hypothesis_status']:
  raw=bytearray();offsets=[0]
  for meta,_ in records:raw.extend(str(meta.get(field)if meta.get(field)is not None else'unknown').encode());offsets.append(len(raw))
  props[field]={'values':buf(bytes(raw)),'stringOffsets':buf(np.array(offsets,dtype='<u4').tobytes()),'stringOffsetType':'UINT32'};schema[field]={'type':'STRING'}
 lo=np.vstack(allpoints).min(axis=0);hi=np.vstack(allpoints).max(axis=0);mn=[float(lo[0]),float(-hi[2]),float(lo[1])];mx=[float(hi[0]),float(-lo[2]),float(hi[1])];center=[(a+b)/2 for a,b in zip(mn,mx)];half=[max(.01,(b-a)/2)for a,b in zip(mn,mx)];box=center+[half[0],0,0,0,half[1],0,0,0,half[2]]
 obj={'asset':{'version':'2.0','generator':VERSION},'extensionsUsed':['EXT_mesh_features','EXT_structural_metadata','KHR_materials_unlit'],'extensions':{'EXT_structural_metadata':{'schema':{'id':'nyc-building-evidence','classes':{'building':{'properties':schema}}},'propertyTables':[{'class':'building','count':len(records),'properties':props}]}},'buffers':[{'byteLength':len(binary)}],'bufferViews':views,'accessors':accessors,'materials':[{'name':'source-outline-neutral','pbrMetallicRoughness':{'baseColorFactor':[.62,.7,.73,1],'metallicFactor':0,'roughnessFactor':1},'extensions':{'KHR_materials_unlit':{}}},{'name':'EXPLICIT_HYPOTHESIS_open_vertical_envelope_NOT_roof_or_wall_evidence','pbrMetallicRoughness':{'baseColorFactor':[.58,.6,.61,1],'metallicFactor':0,'roughnessFactor':1},'doubleSided':False}],'meshes':[{'primitives':primitives}],'nodes':[{'mesh':0}],'scenes':[{'nodes':[0]}],'scene':0,'extras':{'mode':mode,'canonical_building_solids':0,'hypothesis_not_verified':mode=='hypothesis','source_version':records[0][0]['source_version'],'ground':'WGS84 ellipsoid display reference +0.25m; NOT physical ground','roof':'unknown: NO cap triangles published','wall':'overhead footprint envelope; NOT ground wall boundary','height':'canonical=null; optional envelope explicitly assumes international foot for source relative height','local_frame':f.manifest(),'feature_ids':[m['id']for m,_ in records],'parts':parts,'render_lod':'full_outline; semantic evidence recorded separately'}}
 j=json.dumps(obj,separators=(',',':')).encode();j+=b' '*((-len(j))%4);binary.extend(b'\0'*((-len(binary))%4));payload=struct.pack('<4sII',b'glTF',2,28+len(j)+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary
 return payload,list(f.matrix_enu_to_ecef),box,parts
