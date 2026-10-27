"""Six labelled directions for an OFF-by-default diagnostic layer; never city geometry."""
import json,struct
from .coordinates import enu_to_gltf

DIRECTIONS={'E':(100,0,0),'W':(-100,0,0),'N':(0,100,0),'S':(0,-100,0),'U':(0,0,100),'D':(0,0,-100)}
COLORS={'E':[1,.25,.25,1],'W':[.7,.15,.35,1],'N':[.2,.8,1,1],'S':[.2,.3,1,1],'U':[1,.8,.15,1],'D':[.7,.3,1,1]}
def axes_glb():
 positions=[];colors=[];ids=[]
 for i,(name,end)in enumerate(DIRECTIONS.items()):
  axis=next(j for j,v in enumerate(end)if v);j,k=(axis+1)%3,(axis+2)%3
  def square(distance,radius):
   corners=[]
   for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]:
    q=[0.,0.,0.];q[axis]=distance;q[j]=a*radius;q[k]=b*radius;corners.append(q)
   return corners
  vertices=square(0,2)+square(end[axis]*.86,2);triangles=[]
  for face in [(0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:triangles.extend([[vertices[face[0]],vertices[face[1]],vertices[face[2]]],[vertices[face[0]],vertices[face[2]],vertices[face[3]]]])
  base=square(end[axis]*.86,5)
  for a in range(4):triangles.append([base[a],base[(a+1)%4],end])
  for triangle in triangles:
   for p in triangle:positions.extend(enu_to_gltf(*p));colors.extend(COLORS[name]);ids.append(i)
 blob=bytearray();views=[]
 def put(data,target=None):
  blob.extend(b'\0'*((-len(blob))%4));v={'buffer':0,'byteOffset':len(blob),'byteLength':len(data)}
  if target:v['target']=target
  views.append(v);blob.extend(data);return len(views)-1
 pv=put(struct.pack('<'+'f'*len(positions),*positions),34962);cv=put(struct.pack('<'+'f'*len(colors),*colors),34962);iv=put(struct.pack('<'+'H'*len(ids),*ids),34962);text=b'';offsets=[0]
 for name in DIRECTIONS:text+=('diagnostic:'+name).encode();offsets.append(len(text))
 sv=put(text);ov=put(struct.pack('<7I',*offsets))
 g={'asset':{'version':'2.0','generator':'NYC stage3 axis diagnostic, NOT a city object'},'extensionsUsed':['KHR_materials_unlit','EXT_mesh_features','EXT_structural_metadata'],'extensions':{'EXT_structural_metadata':{'schema':{'id':'directions','classes':{'axis':{'properties':{'id':{'type':'STRING'}}}}},'propertyTables':[{'class':'axis','count':6,'properties':{'id':{'values':sv,'stringOffsets':ov,'stringOffsetType':'UINT32'}}}]}},'buffers':[{'byteLength':len(blob)}],'bufferViews':views,'accessors':[{'bufferView':pv,'componentType':5126,'count':len(ids),'type':'VEC3','min':[-100,-100,-100],'max':[100,100,100]},{'bufferView':cv,'componentType':5126,'count':len(ids),'type':'VEC4'},{'bufferView':iv,'componentType':5123,'count':len(ids),'type':'SCALAR'}],'materials':[{'doubleSided':True,'extensions':{'KHR_materials_unlit':{}},'pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'metallicFactor':0,'roughnessFactor':1}}],'meshes':[{'primitives':[{'attributes':{'POSITION':0,'COLOR_0':1,'_FEATURE_ID_0':2},'mode':4,'material':0,'extensions':{'EXT_mesh_features':{'featureIds':[{'featureCount':6,'attribute':0,'propertyTable':0}]}}}]}],'nodes':[{'mesh':0}],'scenes':[{'nodes':[0]}],'scene':0,'extras':{'diagnostic_only':True,'synthetic_city_geometry':False,'units':'metre','axis_endpoints_enu_m':DIRECTIONS,'gltf_axes':'East,Up,-North','representation':'six 100m diagnostic arrows, not buildings or landmarks','expected_engine_y_to_z_up_rotations':1}}
 j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);blob.extend(b'\0'*((-len(blob))%4));return struct.pack('<4sII',b'glTF',2,28+len(j)+len(blob))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(blob),0x004e4942)+blob
