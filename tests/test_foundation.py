import json,math,struct,sys,tempfile,unittest,warnings
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from nyc.download import ROOT
from nyc.coordinates import metres,US_SURVEY_FOOT,INTERNATIONAL_FOOT,LocalFrame,UnresolvedReference
from nyc.elevations import Elevation,absolute_roof,GeoidConversion
from nyc.terrain import BareEarthRaster
from nyc.diagnostic_gltf import DIRECTIONS

class FoundationTests(unittest.TestCase):
 def test_us_and_international_feet_are_distinct_and_unknown_foot_is_blocked(self):
  self.assertEqual(metres(1,'us_survey_foot'),1200/3937);self.assertEqual(metres(1,'international_foot'),.3048)
  self.assertAlmostEqual(metres(1000000,'us_survey_foot')-metres(1000000,'international_foot'),.6096012192,places=8)
  with self.assertRaises(UnresolvedReference):metres(100,'foot_unspecified')
  self.assertEqual(metres(-2,'metre'),-2)

 def test_relative_height_only_and_same_base_are_required(self):
  ground=Elevation(-3,'metre','ground_orthometric','NAVD88','NAD83(2011)','same-base')
  relative=Elevation(10,'international_foot','building_relative',None,None,'same-base')
  roof=absolute_roof(ground,relative);self.assertAlmostEqual(roof.metric(),.048)
  with self.assertRaises(ValueError):absolute_roof(ground,roof)
  with self.assertRaises(UnresolvedReference):absolute_roof(ground,Elevation(10,'metre','building_relative',None,None,'other-base'))
  with self.assertRaises(UnresolvedReference):absolute_roof(Elevation(0,'metre','ground_orthometric',None,None,'same-base'),relative)
  with self.assertRaises(ValueError):absolute_roof(ground,Elevation(-1,'metre','building_relative',None,None,'same-base'))

 def test_geoid_matches_registered_operation_and_blocks_wrong_frame(self):
  from pyproj.transformer import TransformerGroup
  from pyproj import Transformer
  path=ROOT/'data/raw/stage3/geoid/us_noaa_g2012bu0.tif';conversion=GeoidConversion(path)
  with self.assertRaises(UnresolvedReference):conversion.orthometric_to_ellipsoid(-74,40.7,Elevation(10,'metre','ground_orthometric','NAVD88','NAD83'))
  with self.assertRaises(UnresolvedReference):GeoidConversion(path.with_name('does-not-exist.tif'))
  with warnings.catch_warnings():
   warnings.simplefilter('ignore');group=TransformerGroup('EPSG:6349','EPSG:6319',always_xy=True,allow_ballpark=False,allow_superseded=True)
  op=next(o for o in group.unavailable_operations if any(g.short_name==path.name for g in o.grids))
  official=Transformer.from_pipeline(op.to_proj4().replace(path.name,str(path)));values=[]
  for lon,lat in [(-74.01,40.71),(-73.8,40.85)]:
   value=conversion.orthometric_to_ellipsoid(lon,lat,Elevation(10,'metre','ground_orthometric','NAVD88','NAD83(2011)','known-base'))
   # The EPSG operation itself uses native latitude/longitude axes; our public API is explicitly lon/lat.
   self.assertEqual(value.horizontal_frame,'NAD83(2011)');self.assertAlmostEqual(value.metric(),official.transform(lat,lon,10,errcheck=True)[2],places=7);values.append(value.metric())
  self.assertGreater(abs(values[0]-values[1]),.1) # A real spatial grid, not one fixed city offset.

 def test_actual_glb_axes_are_right_handed_and_engine_rotation_is_single(self):
  blob=(ROOT/'assets/foundation/axes-diagnostic.glb').read_bytes();size=struct.unpack_from('<I',blob,12)[0];g=json.loads(blob[20:20+size]);binary_start=20+size+8;count=g['accessors'][0]['count'];pos=struct.unpack_from('<'+'f'*(count*3),blob,binary_start+g['bufferViews'][0]['byteOffset']);ids=struct.unpack_from('<'+'H'*count,blob,binary_start+g['bufferViews'][2]['byteOffset'])
  self.assertEqual(g['meshes'][0]['primitives'][0]['mode'],4)
  for i,(component,extreme)in enumerate([(0,100),(0,-100),(2,-100),(2,100),(1,100),(1,-100)]):
   values=[pos[j*3+component]for j in range(count)if ids[j]==i];self.assertEqual(max(values)if extreme>0 else min(values),extreme)
  f=LocalFrame.at(-74,40.7,200);e,n,u=f.basis_enu;cross=(e[1]*n[2]-e[2]*n[1],e[2]*n[0]-e[0]*n[2],e[0]*n[1]-e[1]*n[0]);self.assertLess(math.dist(cross,u),1e-12)

 def test_thirty_source_correspondences_are_not_labelled_field_surveys(self):
  r=json.loads((ROOT/'reports/stage3/registration.json').read_text());self.assertEqual(r['source_correspondence_points'],30);self.assertEqual(r['independently_surveyed_control_points'],0);self.assertTrue(all(v==6 for v in r['borough_counts'].values()));self.assertLess(r['maximum_gpu_pipeline_m'],.1)
  self.assertTrue(all(p['relative_reality_measurement_error_m']is None for p in r['checkpoints']));self.assertEqual(len({p['building_id']for p in r['checkpoints']}),30);self.assertLess(r['single_city_tangent_plane_assessment']['min_up_m'],-1)

 def test_nodata_and_outside_are_unknown_and_zero_is_a_valid_ground_value(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);arr=np.zeros((5,5),np.float32);arr[2,2]=np.nan;np.save(p/'r.npy',arr);(p/'r.json').write_text(json.dumps({'authority':['EPSG','32118'],'numpy_file':str(p/'r.npy'),'geotransform':[0,1,0,5,0,-1]}));s={'vertical_units':'metre','vertical_datum':'NAVD88','surface_kind':'bare_earth_dem'};r=BareEarthRaster(p/'r.json',s)
   self.assertEqual(r.sample(.5,4.5),0);self.assertIsNone(r.sample(-.5,4.5));self.assertIsNone(r.sample(2.5,2.5));self.assertEqual(r.lod(4)['indices'],[]) # Fine-grid void must not be hidden by coarse known corners.
   with self.assertRaises(ValueError):BareEarthRaster(p/'r.json',{**s,'surface_kind':'dsm'})
   with self.assertRaises(ValueError):BareEarthRaster(p/'r.json',{**s,'masked_raster':'required-real-mask.lerc'})

 def test_actual_tiff_false_zero_is_nodata_by_both_lerc_and_official_identify(self):
  info=json.loads((ROOT/'data/intermediate/stage3/dem/staten-st-george.json').read_text());arr=np.load(info['numpy_file']);identify=json.loads((ROOT/'data/raw/stage3/dem/zero-mask-identify.json').read_text())
  self.assertEqual(identify['value'],'NoData');self.assertTrue(np.isnan(arr[128,200]));self.assertEqual(info['missing_cells'],34738);self.assertEqual(info['tiff_zero_but_lerc_missing'],34738);self.assertLess(info['maximum_valid_tiff_lerc_difference_m'],.1)

 def test_real_dem_tiles_have_metric_z_separate_datums_and_no_cracks(self):
  manifest=json.loads((ROOT/'assets/foundation/manifest.json').read_text());self.assertFalse(manifest['global_terrain_registered'])
  for d in manifest['datasets']:
   data=json.loads((ROOT/'assets/foundation'/d['terrain']).read_text());t=data['terrain'];self.assertFalse(data['world_placement_allowed']);self.assertEqual(t['height_datum'],'NAVD88');self.assertEqual(t['vertical_exaggeration'],1);self.assertIsNone(t['ecef_placement']);self.assertEqual(len(t['tiles']),4);self.assertEqual(sum(len(x['indices'])for x in t['tiles']),len(t['indices']));self.assertLess(t['tile_seam_max_m'],.1)
   source=json.loads((ROOT/f"data/intermediate/stage3/dem/{d['id']}.json").read_text());arr=np.load(source['numpy_file']);index=t['indices'][0];self.assertAlmostEqual(t['heights'][index],float(arr[(index//65)*4,(index%65)*4]),places=6)
   self.assertTrue(source['lerc_mask_applied']);self.assertGreater(source['missing_cells'],0);self.assertTrue(all(t['heights'][i]is not None for i in t['indices']))
   self.assertTrue(all(tile['ecef_transform']is None for tile in t['tiles']))

 def test_real_water_hole_is_not_filled_by_triangles(self):
  from shapely.geometry import shape
  from shapely import constrained_delaunay_triangles
  r=json.loads((ROOT/'data/processed/foundation/shoreline-hole-proof.json').read_text());water=shape(r['clipped_water_geometry_metric']);hole=shape(r['real_source_hole_geometry_metric']);triangles=constrained_delaunay_triangles(water)
  self.assertGreater(hole.area,10000);self.assertLess(sum(t.intersection(hole).area for t in triangles.geoms),1e-6);self.assertAlmostEqual(sum(t.area for t in triangles.geoms),water.area,places=5)

 def test_unresolved_legacy_heights_and_road_decks_are_not_published_as_real_z(self):
  records=json.loads((ROOT/'assets/foundation/building-elevations.json').read_text());self.assertEqual(len(records),3027)
  for r in records:self.assertIsNone(r['ground']['value_m']);self.assertIsNone(r['building_relative']['value_m']);self.assertIsNone(r['roof_absolute']['value']);self.assertIsNone(r['antenna_height']['value']);self.assertFalse(r['world_placement_allowed'])
  d=json.loads((ROOT/'assets/foundation/lower-manhattan-overlays.json').read_text());self.assertTrue(all(r['elevation']is None and r['deck_height']is None for r in d['roads']));self.assertTrue(all(p['ecef_height_m']is None for p in d['ground_samples']))
  path=next((ROOT/'assets/lower-manhattan').glob('*.glb'));blob=path.read_bytes();size=struct.unpack_from('<I',blob,12)[0];g=json.loads(blob[20:20+size]);properties=g['extensions']['EXT_structural_metadata']['schema']['classes']['building']['properties'];self.assertNotIn('height_m',properties);self.assertIn('relative_height_raw_ft',properties);self.assertIn('legacy_stage2_height_m',properties)

if __name__=='__main__':unittest.main()
