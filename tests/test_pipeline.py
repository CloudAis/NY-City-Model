import unittest,json,sys,struct,tempfile,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from nyc.normalize import numeric,esri_polygon,normalize
from nyc.tiles import make_glb,frame,local_point
from nyc.download import ROOT
from pyproj import Transformer
class PipelineTests(unittest.TestCase):
 def test_height_semantics_and_negative_ground(self):
  self.assertEqual(numeric(0,'height'),(None,'unknown_zero'));self.assertEqual(numeric(None,'height'),(None,'null'));self.assertIsNone(numeric(-1,'height')[0]);self.assertEqual(numeric(-12,'ground'),(-12,'valid'));self.assertEqual(numeric(300,'height')[0]*.3048,91.44)
 def test_holes_and_multipart_and_invalid(self):
  outer=[[0,0],[0,10],[10,10],[10,0],[0,0]];hole=[[2,2],[4,2],[4,4],[2,4],[2,2]];second=[[20,0],[20,2],[22,2],[22,0],[20,0]]
  before,after,_=esri_polygon([outer,hole,second]);self.assertTrue(after.is_valid);self.assertAlmostEqual(after.area,100);self.assertEqual(len(after.geoms),2)
  _,fixed,_=esri_polygon([[[0,0],[2,2],[0,2],[2,0],[0,0]]]);self.assertTrue(fixed.is_valid);self.assertGreater(fixed.area,0)
 def test_real_source_counts_and_geography(self):
  mf=json.loads((ROOT/'data/intermediate/lower-manhattan/manifest.json').read_text());rows=[json.loads(x)for x in(ROOT/'data/processed/lower-manhattan/buildings.jsonl').read_text().splitlines()];self.assertEqual(len(rows),mf['records_downloaded']);self.assertEqual(len(set(r['id']for r in rows)),len(rows));self.assertTrue(all(not r['evidence']['height']['independently_verified']for r in rows));self.assertTrue(any(r['height_m']is None for r in rows));self.assertTrue(all(r['evidence']['roof']['status']=='unknown'for r in rows))
  for r in rows:
   x,y=r['geometry_wgs84']['coordinates'][0][0];self.assertTrue(-74.03<x<-73.98 and 40.69<y<40.73);self.assertGreater(r['area_m2'],0)
 def test_real_normalization_is_repeatable(self):
  with tempfile.TemporaryDirectory()as d:
   normalize(ROOT/'data/intermediate/lower-manhattan/manifest.json',d);a=(Path(d)/'buildings.jsonl').read_bytes();normalize(ROOT/'data/intermediate/lower-manhattan/manifest.json',d);self.assertEqual(a,(Path(d)/'buildings.jsonl').read_bytes());self.assertEqual(a,(ROOT/'data/processed/lower-manhattan/buildings.jsonl').read_bytes())
 def test_glb_local_precision_axis_and_real_identity(self):
  r=json.loads((ROOT/'data/processed/lower-manhattan/buildings.jsonl').read_text().splitlines()[0]);x,y=r['geometry']['coordinates'][0][0];blob,matrix,box,ll=make_glb([r],x-215,y+315);magic,version,length=struct.unpack_from('<4sII',blob);self.assertEqual((magic,version,length),(b'glTF',2,len(blob)));jl,jt=struct.unpack_from('<II',blob,12);g=json.loads(blob[20:20+jl]);start=20+jl+8;v=g['bufferViews'][0];a=struct.unpack_from('<3f',blob,start+v['byteOffset']);enu=[a[0],-a[2],a[1]-.25];origin,basis,_,_=frame(x-215,y+315);reconstructed=[origin[i]+sum(enu[j]*basis[j][i]for j in range(3))for i in range(3)];lon,lat=Transformer.from_crs(32118,4326,always_xy=True).transform(x,y);expected=Transformer.from_crs(4979,4978,always_xy=True).transform(lon,lat,0);self.assertLess(math.dist(reconstructed,expected),.001);self.assertEqual(g['meshes'][0]['primitives'][0]['mode'],1);self.assertFalse(g['extras']['height_applied']);self.assertEqual(g['extras']['feature_ids'],[r['id']]);self.assertLess(max(abs(n)for n in box),2000)
 def test_real_placeholder_kept_in_records_but_excluded_from_scene(self):
  rows=[json.loads(x)for x in(ROOT/'data/processed/midtown/buildings.jsonl').read_text().splitlines()];placeholders={r['id']for r in rows if r['placeholder']};self.assertEqual(len(placeholders),1);published=[]
  for p in(ROOT/'assets/midtown').glob('*.glb'):
   blob=p.read_bytes();size=struct.unpack_from('<I',blob,12)[0];published.extend(json.loads(blob[20:20+size])['extras']['feature_ids'])
  self.assertTrue(placeholders.isdisjoint(published));self.assertEqual(len(published),811);self.assertEqual(len(set(published)),811)
class EvidenceTests(unittest.TestCase):
 def test_newer_null_never_replaces_old_valid_and_parcel_is_not_a_building(self):
  from nyc.evidence import resolve
  old={'source':'nyc-building-footprints','value':35.2,'status':'source_explicit','observation_date':'2022-01-01','record_id':'a'};new={'source':'nyc-building-footprints','value':None,'status':'unknown','observation_date':'2026-01-01','record_id':'b'};parcel={'source':'pluto-parcel','scope':'parcel','value':99,'status':'source_explicit','observation_date':'2026-01-01'}
  result=resolve('height',[old,new,parcel]);self.assertEqual(result['chosen'],old);self.assertEqual(len(result['conflicts']),2);self.assertEqual(len(result['candidates']),3)
 def test_true_zero_ground_and_bool_are_distinguished(self):
  self.assertEqual(numeric(0,'ground'),(0,'valid'));self.assertEqual(numeric(False,'height'),(None,'not_numeric'))

class LocalImportTests(unittest.TestCase):
 def test_unknown_source_is_quarantined_and_declared_license_cannot_publish(self):
  from nyc.tiles import publish
  unknown=ROOT/'data/intermediate/local-unknown';declared=ROOT/'data/intermediate/local-declared'
  self.assertFalse((unknown/'buildings.jsonl').exists());self.assertEqual(json.loads((unknown/'source.json').read_text())['provenance_status'],'unknown_pending_verification');before=(ROOT/'assets/catalog.json').read_bytes()
  with self.assertRaises(ValueError):publish([declared])
  self.assertEqual((ROOT/'assets/catalog.json').read_bytes(),before)

if __name__=='__main__':unittest.main()
