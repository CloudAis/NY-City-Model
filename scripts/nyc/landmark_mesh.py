"""Per-landmark evidence geometry, not a reusable generic skyscraper template."""
import json,math,struct
import numpy as np

class Mesh:
 def __init__(self,building_id):self.id=building_id;self.components=[]
 def add(self,name,positions,material,mode=4):
  p=np.asarray(positions,dtype=np.float64).reshape((-1,3))
  if not len(p)or not np.isfinite(p).all():raise ValueError('finite nonempty geometry required')
  self.components.append({'name':name,'positions':p,'material':material,'mode':mode})
 def triangles(self,name,triangles,material):self.add(name,np.asarray(triangles).reshape((-1,3)),material)
 def glb(self,heading,provenance):
  blob=bytearray();views=[];accessors=[];primitives=[];bounds=[];c,s=math.cos(heading),math.sin(heading)
  def buf(data,target=None):
   blob.extend(b'\0'*((-len(blob))%4));offset=len(blob);blob.extend(data);views.append({'buffer':0,'byteOffset':offset,'byteLength':len(data),**({'target':target}if target else{})});return len(views)-1
  def attr(a,kind,dtype,component):
   a=np.asarray(a,dtype=dtype);v=buf(a.tobytes(),34962);entry={'bufferView':v,'componentType':component,'count':len(a),'type':kind}
   if kind=='VEC3':entry.update(min=a.min(axis=0).tolist(),max=a.max(axis=0).tolist())
   accessors.append(entry);return len(accessors)-1
  for index,component in enumerate(self.components):
   p=component['positions'].copy();x=p[:,0].copy();y=p[:,1].copy();p[:,0]=x*c-y*s;p[:,1]=x*s+y*c
   p=p[:,[0,2,1]]*np.array([1,1,-1]);p=p.astype('<f4');bounds.append(p)
   attrs={'POSITION':attr(p,'VEC3','<f4',5126),'_FEATURE_ID_0':attr(np.full(len(p),index),'SCALAR','<u4',5125)}
   if component['mode']==4:
    t=p.reshape((-1,3,3));n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);length=np.linalg.norm(n,axis=1)
    if np.any(length<1e-8):raise ValueError('degenerate landmark face')
    attrs['NORMAL']=attr(np.repeat(n/length[:,None],3,axis=0),'VEC3','<f4',5126)
   ix=np.arange(len(p),dtype='<u4');view=buf(ix.tobytes(),34963);accessors.append({'bufferView':view,'componentType':5125,'count':len(p),'type':'SCALAR','min':[0],'max':[len(p)-1]})
   primitives.append({'attributes':attrs,'indices':len(accessors)-1,'mode':component['mode'],'material':component['material'],'extensions':{'EXT_mesh_features':{'featureIds':[{'attribute':0,'featureCount':len(self.components),'propertyTable':0,'label':'component'}]}}})
  props={};schema={}
  for field,values in [('id',[self.id]*len(self.components)),('component_id',[self.id+':landmark:'+v['name']for v in self.components]),('component_name',[v['name']for v in self.components])]:
   raw=bytearray();offsets=[0]
   for v in values:raw.extend(v.encode());offsets.append(len(raw))
   props[field]={'values':buf(bytes(raw)),'stringOffsets':buf(np.array(offsets,dtype='<u4').tobytes()),'stringOffsetType':'UINT32'};schema[field]={'type':'STRING'}
  materials=[
   {'name':'glass-neutral-opaque-inspection','pbrMetallicRoughness':{'baseColorFactor':[.37,.48,.54,1],'roughnessFactor':.42,'metallicFactor':.05},'doubleSided':False},
   {'name':'podium-glass-neutral','pbrMetallicRoughness':{'baseColorFactor':[.53,.58,.6,1],'roughnessFactor':.65,'metallicFactor':.05}},
   {'name':'metal-axis-diameter-unknown','pbrMetallicRoughness':{'baseColorFactor':[.54,.56,.58,1],'roughnessFactor':.6,'metallicFactor':.5}},
   {'name':'concrete-grid-centrelines-NOT-member-volumes','pbrMetallicRoughness':{'baseColorFactor':[.36,.38,.39,1],'roughnessFactor':.9,'metallicFactor':0},'extensions':{'KHR_materials_unlit':{}}},
   {'name':'unknown-roof-surface-neutral-reference-NOT-glass','pbrMetallicRoughness':{'baseColorFactor':[.55,.56,.56,1],'roughnessFactor':.9,'metallicFactor':0}}
  ]
  g={'asset':{'version':'2.0','generator':'NYC stage5 evidence-bound landmark geometry'},'extensionsUsed':['EXT_mesh_features','EXT_structural_metadata','KHR_materials_unlit'],'extensions':{'EXT_structural_metadata':{'schema':{'id':'landmark-components','classes':{'component':{'properties':schema}}},'propertyTables':[{'class':'component','count':len(self.components),'properties':props}]}},'buffers':[{'byteLength':len(blob)}],'bufferViews':views,'accessors':accessors,'materials':materials,'meshes':[{'primitives':primitives}],'nodes':[{'mesh':0}],'scenes':[{'nodes':[0]}],'scene':0,'extras':{'stable_building_id':self.id,'units':'metre','axes':'East,Up,-North; one engine Y-up rotation','local_base_m':0,'base_is_not_world_altitude':True,'components':[v['name']for v in self.components],'provenance':provenance,'no_interiors':True,'neutral_material_colors':'display choices, not measured albedo'}}
  j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);blob.extend(b'\0'*((-len(blob))%4));raw=struct.pack('<4sII',b'glTF',2,28+len(j)+len(blob))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(blob),0x004e4942)+blob
  p=np.vstack(bounds);lo=p.min(axis=0);hi=p.max(axis=0);a=np.array([lo[0],-hi[2],lo[1]]);b=np.array([hi[0],-lo[2],hi[1]]);center=(a+b)/2;half=np.maximum((b-a)/2,.01);box=[float(v)for v in center]+[float(half[0]),0,0,0,float(half[1]),0,0,0,float(half[2])]
  return raw,box,{'vertices':sum(len(v['positions'])for v in self.components),'components':len(self.components),'triangles':sum(len(v['positions'])//3 for v in self.components if v['mode']==4),'lines':sum(len(v['positions'])//2 for v in self.components if v['mode']==1)}

def one_world(parameters,building_id):
 p=parameters;mesh=Mesh(building_id);a=p['base_width_m']/2;b=p['roof_width_m']/math.sqrt(2);z=p['podium_top_m'];top=p['roof_height_m']
 base=[(-a,-a,0),(a,-a,0),(a,a,0),(-a,a,0)];lower=[(x,y,z)for x,y,_ in base];upper=[(0,-b,top),(b,0,top),(0,b,top),(-b,0,top)]
 podium=[]
 for i in range(4):
  j=(i+1)%4;podium.extend([[base[i],base[j],lower[j]],[base[i],lower[j],lower[i]]])
 mesh.triangles('podium',podium,1)
 facets=[]
 for i in range(4):
  j=(i+1)%4;facets.extend([[lower[i],lower[j],upper[i]],[upper[i],lower[j],upper[j]]])
 mesh.triangles('eight-triangular-facets',facets,0)
 mesh.triangles('roof-plane-45-degree-square',[[upper[0],upper[1],upper[2]],[upper[0],upper[2],upper[3]]],4)
 mesh.add('spire-axis-only-diameter-unknown',[(0,0,top),(0,0,p['total_height_m'])],2,1)
 return mesh

def park432_grid(parameters,building_id):
 """Only evidenced structural centrelines. NO unknown glazing/mechanical bands.

 A line fragment is never counted as a massing-complete or facade-complete model.
 """
 p=parameters;mesh=Mesh(building_id);a=p['width_m']/2;pitch=p['grid_pitch_m'];h=p['roof_height_m'];lines=[]
 # Six bays per face follow 93.5ft outer width and 15.5ft column grid;
 # grid spans 93ft, outer-face half-foot difference is explicitly retained.
 values=[(i-3)*pitch for i in range(7)]
 for side in range(4):
  def point(t,z):
   return [(t,-a,z),(a,t,z),(-t,a,z),(-a,-t,z)][side]
  for t in values:lines.extend([point(t,0),point(t,h)])
  for k in range(math.floor(h/pitch)+1):lines.extend([point(-a,k*pitch),point(a,k*pitch)])
  lines.extend([point(-a,h),point(a,h)])
 mesh.add('exposed-concrete-grid-centrelines-only',lines,3,1)
 return mesh
