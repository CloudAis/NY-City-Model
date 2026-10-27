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
  mf=json.load(open(ROOT/'data/intermediate/lower-manhattan/manifest.json'));rows=[json.loads(x)for x in(ROOT/'data/processed/lower-manhattan/buildings.jsonl').read_text().splitlines()];self.assertEqual(len(rows),mf['records_downloaded']);self.assertEqual(len(set(r['id']for r in rows)),len(rows));self.assertTrue(all(not r['evidence']['height']['independently_verified']for r in rows));self.assertTrue(any(r['height_m']is None for r in rows));self.assertTrue(all(r['evidence']['roof']['status']=='unknown'for r in rows))
  for r in rows:
   x,y=r['geometry_wgs84']['coordinates'][0][0];self.assertTrue(-74.03<x<-73.98 and 40.69<y<40.73);self.assertGreater(r['area_m2'],0)
 def test_real_normalization_is_repeatable(self):
  with tempfile.TemporaryDirectory()as d:
   normalize(ROOT/'data/intermediate/lower-manhattan/manifest.json',d);a=(Path(d)/'buildings.jsonl').read_bytes();normalize(ROOT/'data/intermediate/lower-manhattan/manifest.json',d);self.assertEqual(a,(Path(d)/'buildings.jsonl').read_bytes());self.assertEqual(a,(ROOT/'data/processed/lower-manhattan/buildings.jsonl').read_bytes())
 def test_glb_local_precision_axis_and_real_identity(self):
  r=json.loads((ROOT/'data/processed/lower-manhattan/buildings.jsonl').read_text().splitlines()[0]);x,y=r['geometry']['coordinates'][0][0];blob,matrix,box,ll=make_glb([r],x,y);magic,version,length=struct.unpack_from('<4sII',blob);self.assertEqual((magic,version,length),(b'glTF',2,len(blob)));jl,jt=struct.unpack_from('<II',blob,12);g=json.loads(blob[20:20+jl]);start=20+jl+8;v=g['bufferViews'][0];a=struct.unpack_from('<3f',blob,start+v['byteOffset']);enu=[a[0],-a[2],a[1]-.25];origin,basis,_,_=frame(x,y);reconstructed=[origin[i]+sum(enu[j]*basis[j][i]for j in range(3))for i in range(3)];lon,lat=Transformer.from_crs(32118,4326,always_xy=True).transform(x,y);expected=Transformer.from_crs(4979,4978,always_xy=True).transform(lon,lat,0);self.assertLess(math.dist(reconstructed,expected),.001);self.assertEqual(g['meshes'][0]['primitives'][0]['mode'],1);self.assertFalse(g['extras']['height_applied']);self.assertEqual(g['extras']['feature_ids'],[r['id']]);self.assertLess(max(abs(n)for n in box),2000)
if __name__=='__main__':unittest.main()
