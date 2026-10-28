import json,sys,unittest,copy
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from nyc.download import ROOT,sha
from build_streaming_catalog import sphere


class StreamingTests(unittest.TestCase):
 def test_every_source_leaf_survives_with_identical_transform_bounds_request_volume_and_binary(self):
  m=json.loads((ROOT/'assets/performance/manifest.json').read_text());self.assertFalse(m['geometry_modified']);count=0
  for b in m['boroughs']:
   source=ROOT/b['source'];self.assertEqual(sha(source),b['source_sha256']);original=json.loads(source.read_text());before={t['content']['uri']:t for t in original['root']['children']};after={}
   for page in b['pages']:
    p=ROOT/page['path'];self.assertEqual(sha(p),page['sha256'])
    for leaf in json.loads(p.read_text())['root']['children']:
     uri=leaf['content']['uri'];actual=(p.parent/uri).resolve();self.assertEqual(actual.parent,source.parent.resolve());self.assertTrue(actual.is_file());self.assertNotIn(actual.name,after)
     leaf=copy.deepcopy(leaf);leaf['content']['uri']=actual.name;after[actual.name]=leaf
   self.assertEqual(before,after);self.assertEqual(len(after),b['published_leaf_count']);count+=len(after)
  self.assertEqual(count,7383)

 def test_hierarchy_conservatively_contains_all_original_obb_corners_and_never_clips_city(self):
  manifest=json.loads((ROOT/'assets/performance/manifest.json').read_text())
  for b in manifest['boroughs']:
   def visit(node,path,parent=None):
    bound=node['boundingVolume']
    if 'sphere'in bound:
     c=np.array(bound['sphere'][:3]);r=bound['sphere'][3]
     if parent:self.assertLessEqual(np.linalg.norm(c-parent[0])+r,parent[1]+1e-7)
     current=(c,r)
    else:
     c,r=sphere(node);self.assertLessEqual(np.linalg.norm(c-parent[0])+r,parent[1]+1e-7);return
    if 'content'in node:
     p=path.parent/node['content']['uri'];visit(json.loads(p.read_text())['root'],p,current)
    for n in node.get('children',[]):visit(n,path,current)
   root=ROOT/b['root'];visit(json.loads(root.read_text())['root'],root)


if __name__=='__main__':unittest.main()
