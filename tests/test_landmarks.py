import unittest,json,struct,sys,math,hashlib
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from nyc.landmark_mesh import one_world,park432_grid
from nyc.download import ROOT
from nyc.coordinates import INTERNATIONAL_FOOT
from test_buildings import read_glb,accessor

class LandmarkTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.root=ROOT/'assets/landmarks';cls.manifest=json.loads((cls.root/'manifest.json').read_text())
 def test_research_count_never_becomes_completed_model_count(self):
  queue=json.loads((ROOT/'landmarks/queue.json').read_text());self.assertEqual(len(queue['landmarks']),29)
  self.assertEqual(self.manifest['published_representations'],2);self.assertEqual(self.manifest['fully_detailed_landmarks_completed'],0);self.assertEqual(self.manifest['facades_completed'],0)
  for item in queue['landmarks']:
   p=ROOT/'landmarks'/item['slug']
   for f in['dossier.json','references.json','dimensions.json','components.json','materials.json','validation.json']:self.assertTrue((p/f).exists())
 def test_all_emitted_parameters_trace_to_existing_primary_bytes(self):
  for e in self.manifest['landmarks']:
   dims=json.loads((self.root/e['slug']/'dimensions.json').read_text())
   for p in dims['parameters']:
    self.assertIsNone(p['uncertainty_m']);self.assertIn('project_review_tolerance_m',p)
    ev=p['evidence'];self.assertTrue((ROOT/ev['path']).exists());self.assertEqual(hashlib.sha256((ROOT/ev['path']).read_bytes()).hexdigest(),ev['sha256']);self.assertFalse(ev['independently_verified'])
    if p['source_unit']=='international_foot':self.assertAlmostEqual(p['value_m'],p['source_value']*INTERNATIONAL_FOOT)
 def test_wtc_roof_spire_and_total_are_distinct(self):
  dims=json.loads((self.root/'one-world-trade-center/dimensions.json').read_text());p={p['id']:p['value_m']for p in dims['parameters']}
  self.assertAlmostEqual(p['roof_height_m'],416.9664);self.assertAlmostEqual(p['total_height_m'],541.3248);self.assertAlmostEqual(p['roof_height_m']+p['spire_above_roof_m'],p['total_height_m'])
  m=one_world(p,'test-only');facets=next(c for c in m.components if c['name']=='eight-triangular-facets');self.assertEqual(len(facets['positions'])//3,8);self.assertEqual(float(facets['positions'][:,2].max()),p['roof_height_m'])
  self.assertTrue(any(c['mode']==1 for c in m.components));self.assertTrue(all(c['positions'][:,2].max()<=p['roof_height_m']for c in m.components if c['mode']==4))
  # Independently check all wall normals point away from the building centre.
  # Comparing stored normals to their own cross products alone misses inversions.
  for component in m.components:
   if component['mode']!=4 or 'roof-plane'in component['name']:continue
   t=component['positions'].reshape((-1,3,3));n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);radial=t.mean(axis=1);self.assertTrue(np.all(np.sum(n[:,:2]*radial[:,:2],axis=1)>0))
 def test_generated_normals_indices_bounds_and_original_stable_id(self):
  for item in self.manifest['landmarks']:
   g,b=read_glb((self.root/item['slug']/'model.glb').read_bytes());self.assertEqual(g['extras']['stable_building_id'],item['building_id']);self.assertTrue(g['extras']['base_is_not_world_altitude'])
   tiles=json.loads((self.root/item['slug']/'tileset.json').read_text());self.assertEqual(tiles['root']['children'][0]['geometricError'],0);self.assertNotIn('transform',tiles['root']['children'][0]);box=tiles['root']['boundingVolume']['box'];center=np.array(box[:3]);half=np.array([box[3],box[7],box[11]])
   for prim in g['meshes'][0]['primitives']:
    pos=accessor(g,b,prim['attributes']['POSITION']);ix=accessor(g,b,prim['indices']).flatten();self.assertLess(ix.max(),len(pos));enu=pos[:,[0,2,1]]*np.array([1,-1,1]);self.assertTrue(np.all(np.abs(enu-center)<=half+1e-4))
    if prim['mode']==4:
     t=pos[ix].reshape((-1,3,3));normal=accessor(g,b,prim['attributes']['NORMAL'])[ix][::3];face=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);self.assertTrue(np.all(np.sum(face*normal,axis=1)>0))
 def test_432_unknown_mechanical_floors_never_receive_fabricated_glazing(self):
  g,b=read_glb((self.root/'432-park-avenue/model.glb').read_bytes());self.assertTrue(all(p['mode']==1 for p in g['meshes'][0]['primitives']))
  dims=json.loads((self.root/'432-park-avenue/dimensions.json').read_text());self.assertEqual(dims['open_mechanical_bands']['count'],5);self.assertIsNone(dims['open_mechanical_bands']['absolute_elevations_m'])
  d=json.loads((self.root/'432-park-avenue/dossier.json').read_text());self.assertFalse(d['replacement_eligible_in_reference_inspector'])
 def test_replacement_maps_cover_exact_source_part_and_no_neighbour(self):
  maps=json.loads((ROOT/'data/manifests/stage5/replacement-map.json').read_text())
  for m in maps:
   self.assertFalse(m['physical_world_replacement_allowed'])
   if m['eligible']:self.assertEqual(m['hide_source_building_ids'],[m['building_id']]);self.assertEqual(len(m['source_part_ids']),1)
   else:self.assertEqual(m['hide_source_building_ids'],[])
 def test_neutral_materials_do_not_turn_all_glass_into_transparency_or_mirrors(self):
  for e in self.manifest['landmarks']:
   g,_=read_glb((self.root/e['slug']/'model.glb').read_bytes())
   for m in g['materials']:
    p=m['pbrMetallicRoughness'];self.assertEqual(p['baseColorFactor'][3],1);self.assertGreaterEqual(p['roughnessFactor'],.4)
 def test_footprint_and_roof_conflicts_remain_visible(self):
  w=json.loads((self.root/'one-world-trade-center/dimensions.json').read_text());self.assertGreaterEqual(len(w['conflicts']),3)
  p=json.loads((self.root/'432-park-avenue/dimensions.json').read_text());self.assertTrue(any(c['field']=='architect_map'for c in p['conflicts']))
if __name__=='__main__':unittest.main()
