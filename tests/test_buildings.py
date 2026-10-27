import sys,json,struct,unittest,math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,shape
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from nyc.buildings import classify,triangulate,projected_shell,glb
from nyc.coordinates import LocalFrame,metric_to_geographic,projected_vertices_to_local,geographic_to_ecef
ROOT=Path(__file__).resolve().parents[1]

def read_glb(raw):
 magic,version,size=struct.unpack_from('<4sII',raw);assert(magic,version,size)==(b'glTF',2,len(raw))
 count,kind=struct.unpack_from('<II',raw,12);assert kind==0x4e4f534a
 obj=json.loads(raw[20:20+count]);n,kind=struct.unpack_from('<II',raw,20+count);assert kind==0x004e4942
 return obj,raw[28+count:28+count+n]
def accessor(obj,data,i):
 a=obj['accessors'][i];v=obj['bufferViews'][a['bufferView']];dtype={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']];w={'VEC3':3,'SCALAR':1}[a['type']]
 return np.frombuffer(data,dtype=dtype,count=a['count']*w,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape((-1,w))

class BuildingTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records=[json.loads(s)for s in(ROOT/'data/processed/lower-manhattan/buildings.jsonl').read_text().splitlines()]
 def test_strict_height_and_overhead_boundary_gate(self):
  for r in self.records:
   m=classify(r);self.assertIsNone(m['canonical_height_m']);self.assertEqual(m['semantic_level'],'outline_only');self.assertIn('overhead_outline_not_verified_wall_line',m['reasons'])
  r=dict(self.records[0]);r.update(height_raw_ft=None,height_status='unknown');self.assertIsNone(classify(r)['height_hypothesis_m'])
  for code in [1000,1001,1002,1003,1006,2110,5100]:
   r=dict(self.records[0]);r.update(feature_code=code);self.assertIsNone(classify(r)['height_hypothesis_m'])
 def test_complex_concavity_hole_and_shell_winding(self):
  p=Polygon([(0,0),(12,0),(12,4),(7,4),(7,12),(0,12)],holes=[[(1,1),(1,3),(3,3),(3,1)]])
  tris=triangulate(p);self.assertAlmostEqual(sum(Polygon(t).area for t in tris),p.area)
  self.assertTrue(all(p.covers(Polygon(t))for t in tris))
  shell=projected_shell(p,24,False);self.assertTrue(all(len(set(t[:,2]))==2 for t in shell))
  # Outward wall normals move away from solid even along courtyard walls.
  for t in shell:
   n=np.cross(t[1]-t[0],t[2]-t[0]);n/=np.linalg.norm(n);mid=t.mean(axis=0);outside=mid[:2]+n[:2]*1e-4
   from shapely.geometry import Point
   self.assertFalse(p.contains(Point(*outside)))
  capped=projected_shell(p,24,True);roof=[t for t in capped if np.all(t[:,2]==24)]
  self.assertAlmostEqual(sum(Polygon(t[:,:2]).area for t in roof),p.area)
  self.assertTrue(all(np.cross(t[1]-t[0],t[2]-t[0])[2]>0 for t in roof))
 def test_real_sample_footprints_triangulation_not_bounding_boxes(self):
  for r in self.records:
   g=shape(r['geometry']);ps=[g]if g.geom_type=='Polygon'else list(g.geoms)
   for p in ps:
    tris=triangulate(p);self.assertAlmostEqual(sum(Polygon(t).area for t in tris),p.area,delta=max(1e-6,p.area*1e-9))
 def test_batched_coordinates_match_shared_scalar_contract(self):
  r=self.records[0];xy=np.array(r['geometry']['coordinates'][0]);f=LocalFrame.at(*metric_to_geographic(*xy[0]),0)
  actual=projected_vertices_to_local(xy,0.25,f)
  expected=np.array([f.to_local(geographic_to_ecef(*metric_to_geographic(*p),.25))for p in xy])
  self.assertLess(np.abs(actual-expected).max(),1e-8)
 def test_real_glb_index_normals_features_bounds_and_no_fake_roof(self):
  r=self.records[0];m=classify(r);x,y=shape(r['geometry']).centroid.coords[0]
  strict,_,_,_=glb([(m,r['geometry'])],(x,y),'strict');hypo,_,box,_=glb([(m,r['geometry'])],(x,y),'hypothesis')
  s,_=read_glb(strict);self.assertEqual([p['mode']for p in s['meshes'][0]['primitives']],[1])
  obj,data=read_glb(hypo);self.assertEqual(obj['extras']['canonical_building_solids'],0);self.assertIn('NO cap',obj['extras']['roof'])
  self.assertEqual(obj['extras']['feature_ids'],[r['id']])
  for prim in obj['meshes'][0]['primitives']:
   pos=accessor(obj,data,prim['attributes']['POSITION']);ix=accessor(obj,data,prim['indices']).flatten()
   self.assertLess(ix.max(),len(pos));self.assertEqual(accessor(obj,data,prim['attributes']['_FEATURE_ID_0']).max(),0)
   enu=pos[:,[0,2,1]]*np.array([1,-1,1]);center=np.array(box[:3]);half=np.array([box[3],box[7],box[11]])
   self.assertTrue(np.all(np.abs(enu-center)<=half+1e-3))
   if prim['mode']==4:
    tris=pos[ix].reshape((-1,3,3));norm=accessor(obj,data,prim['attributes']['NORMAL']);self.assertTrue(np.allclose(np.linalg.norm(norm,axis=1),1,atol=1e-5))
    face=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0]);self.assertTrue(np.all(np.sum(face*norm[::3],axis=1)>0))
    self.assertTrue(np.all(np.abs(norm[:,1])<.01),'unknown roof must not get flat cap triangles')
if __name__=='__main__':unittest.main()
