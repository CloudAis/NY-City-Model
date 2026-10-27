"""Measured footprint line GLB: no walls, roofs, inferred heights or interiors."""
import json,math,struct
from pathlib import Path
from collections import defaultdict
from .coordinates import LocalFrame,metric_to_geographic,geographic_to_ecef
from .download import ROOT,atomic_json,sha
from . import PIPELINE_VERSION
def frame(x,y):
 lon,lat=metric_to_geographic(x,y);f=LocalFrame.at(lon,lat,0)
 return f.origin_ecef_m,f.basis_enu,list(f.matrix_enu_to_ecef),[lon,lat]
def local_point(x,y,origin,basis):
 lon,lat=metric_to_geographic(x,y);p=geographic_to_ecef(lon,lat,0);delta=[p[i]-origin[i]for i in range(3)];return [sum(delta[i]*v[i]for i in range(3))for v in basis]
def rings(g):
 return g['coordinates']if g['type']=='Polygon'else[r for polygon in g['coordinates']for r in polygon]
def make_glb(records,x,y):
 origin,basis,matrix,ll=frame(x,y);points=[];featureids=[];n=len(records)
 for i,r in enumerate(records):
  for ring in rings(r['geometry']):
   for a,b in zip(ring,ring[1:]):
    for q in [a,b]:
     e,north,up=local_point(*q[:2],origin,basis);points.extend([e,up+.25,-north]);featureids.append(i)
 if not featureids:raise ValueError('no real footprint line vertices')
 binary=bytearray();views=[]
 def buf(data,target=None):
  while len(binary)%4:binary.append(0)
  offset=len(binary);binary.extend(data);view={'buffer':0,'byteOffset':offset,'byteLength':len(data)}
  if target:view['target']=target
  views.append(view);return len(views)-1
 pos=buf(struct.pack('<'+'f'*len(points),*points),34962);fid=buf(struct.pack('<'+'H'*len(featureids),*featureids),34962)
 mins=[min(points[i::3])for i in range(3)];maxs=[max(points[i::3])for i in range(3)]
 props={};schema={}
 for key,field in [('id','id'),('name','name'),('bin','bin'),('bbl','base_bbl'),('relative_height_raw_ft','height_raw_ft'),('legacy_stage2_height_m','height_m')]:
  values=bytearray();offsets=[0]
  for r in records:
   v=r.get(field);values.extend((''if v is None else str(v)).encode());offsets.append(len(values))
  props[key]={'values':buf(bytes(values)),'stringOffsets':buf(struct.pack('<'+'I'*len(offsets),*offsets)),'stringOffsetType':'UINT32'};schema[key]={'type':'STRING'}
 gltf={'asset':{'version':'2.0','generator':'NYC genuine footprint pipeline '+PIPELINE_VERSION},'extensionsUsed':['EXT_mesh_features','EXT_structural_metadata','KHR_materials_unlit'],'extensions':{'EXT_structural_metadata':{'schema':{'id':'nyc-footprints','classes':{'building':{'properties':schema}}},'propertyTables':[{'class':'building','count':len(records),'properties':props}]}},'buffers':[{'byteLength':len(binary)}],'bufferViews':views,'accessors':[{'bufferView':pos,'componentType':5126,'count':len(featureids),'type':'VEC3','min':mins,'max':maxs},{'bufferView':fid,'componentType':5123,'count':len(featureids),'type':'SCALAR','min':[0],'max':[len(records)-1]}],'materials':[{'name':'survey-outline-only','pbrMetallicRoughness':{'baseColorFactor':[.15,.82,.9,1],'metallicFactor':0,'roughnessFactor':1},'extensions':{'KHR_materials_unlit':{}},'doubleSided':True}],'meshes':[{'primitives':[{'attributes':{'POSITION':0,'_FEATURE_ID_0':1},'mode':1,'material':0,'extensions':{'EXT_mesh_features':{'featureIds':[{'featureCount':len(records),'attribute':0,'propertyTable':0,'label':'building'}]}}}]}],'nodes':[{'mesh':0,'name':'Official measured outlines; reference ellipsoid + 0.25m; not ground or buildings'}],'scenes':[{'nodes':[0]}],'scene':0,'extras':{'coordinate_units':'metre','geometry_representation':'source-footprint-lines-only','height_applied':False,'reference_lift_m':.25,'origin_wgs84':ll,'origin_ecef_m':origin,'external_enu_to_ecef_column_major':matrix,'height_metadata':'raw feet subtype unresolved; stage2 metre values explicitly legacy, never used as geometry','feature_ids':[r['id']for r in records]}}
 j=json.dumps(gltf,separators=(',',':')).encode();j+=b' '*((-len(j))%4);binary.extend(b'\0'*((-len(binary))%4));glb=struct.pack('<4sII',b'glTF',2,12+8+len(j)+8+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary
 # glTF Y-up to 3D Tiles Z-up: (x,y,z) -> (x,-z,y).
 enu_min=[mins[0],-maxs[2],mins[1]];enu_max=[maxs[0],-mins[2],maxs[1]];center=[(a+b)/2 for a,b in zip(enu_min,enu_max)];half=[max(.01,(b-a)/2)for a,b in zip(enu_min,enu_max)];box=center+[half[0],0,0,0,half[1],0,0,0,half[2]]
 return glb,matrix,box,ll

def publish(dataset_paths):
 for candidate in dataset_paths:
  quality=json.loads((Path(candidate)/'quality.json').read_text())
  if quality.get('publication_allowed')is False:raise ValueError('dataset source/license is quarantined; refusing scene publication: '+str(candidate))
 out=ROOT/'assets';out.mkdir(exist_ok=True);catalog={'schema_version':1,'pipeline_version':PIPELINE_VERSION,'representation':'real official footprint linework; no building solids','datasets':[],'source_url':'https://github.com/CityOfNewYork/nyc-geo-metadata/blob/main/Metadata/Metadata_BuildingFootprints.md','height_note':'HEIGHT_ROOF source feet subtype unresolved; canonical height unknown; null/zero unknown; legacy metres never drive geometry','ground_note':'World view is an ellipsoid reference; masked NAVD88 terrain has a separate inspector pending global vertical registration. Lines lifted 0.25m only for visibility.'}
 for path in dataset_paths:
  path=Path(path);name=path.name;records=[json.loads(s)for s in(path/'buildings.jsonl').read_text().splitlines()if s];groups=defaultdict(list)
  for r in records:
   if r['placeholder']:continue
   xs=[p[0]for ring in rings(r['geometry'])for p in ring];ys=[p[1]for ring in rings(r['geometry'])for p in ring];gx=math.floor((min(xs)+max(xs))/2/500);gy=math.floor((min(ys)+max(ys))/2/500);groups[(gx,gy)].append(r)
  dest=out/name;dest.mkdir(parents=True,exist_ok=True);children=[];local_index=[]
  for (gx,gy),features in sorted(groups.items()):
   tile_id=f'{gx}_{gy}';glb,matrix,box,ll=make_glb(features,(gx+.5)*500,(gy+.5)*500);p=dest/(tile_id+'.glb');p.write_bytes(glb);children.append({'boundingVolume':{'box':box},'geometricError':0,'transform':matrix,'content':{'uri':p.name}});local_index.append({'id':tile_id,'feature_ids':[r['id']for r in features],'sha256':sha(p),'bytes':len(glb),'origin_wgs84':ll,'origin_ecef_m':matrix[12:15],'enu_to_ecef_column_major':matrix,'gltf_axes':'East,Up,-North; engine Y-up to Z-up exactly once','box_local_m':box})
  coords=[p for r in records if not r['placeholder']for ring in rings(r['geometry_wgs84'])for p in ring];bounds=[min(p[0]for p in coords),min(p[1]for p in coords),max(p[0]for p in coords),max(p[1]for p in coords)]
  region=[math.radians(bounds[0]),math.radians(bounds[1]),math.radians(bounds[2]),math.radians(bounds[3]),-1,2]
  tileset={'asset':{'version':'1.1','extras':{'geometry':'footprint linework, NOT reconstructed building models'}},'geometricError':1000,'root':{'boundingVolume':{'region':region},'geometricError':500,'refine':'ADD','children':children}}
  atomic_json(dest/'tileset.json',tileset);atomic_json(dest/'tiles.json',local_index);atomic_json(dest/'buildings.json',records);quality=json.loads((path/'quality.json').read_text());atomic_json(dest/'quality.json',quality)
  catalog['datasets'].append({'id':name,'title':name.replace('-',' ').title(),'records':len(records),'published_real_outlines':sum(not r['placeholder']for r in records),'tiles':len(children),'bounds_wgs84':bounds,'tileset':f'{name}/tileset.json','buildings':f'{name}/buildings.json','quality':f'{name}/quality.json'})
 atomic_json(out/'catalog.json',catalog);return catalog
