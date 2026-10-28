import hashlib
import json
import math
import sqlite3
import subprocess
import sys
import unittest
from pathlib import Path
import numpy as np
from test_buildings import read_glb, accessor
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from nyc.download import ROOT
from nyc.facades import facade_candidates, ELEMENTS
from nyc.facade_math import homography


class FacadeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ROOT/"assets/facades"
        cls.manifest = json.loads((cls.root/"manifest.json").read_text())
        cls.street = json.loads((cls.root/"grove-1936/street.json").read_text())

    def test_twelve_explicit_areas_use_real_unique_city_objects_across_five_boroughs(self):
        areas = self.manifest["areas"]
        self.assertEqual(len(areas), 12)
        self.assertEqual(len({a["borough"] for a in areas}), 5)
        ids = set()
        for area in areas:
            actual = json.loads((self.root/area["details"]).read_text())
            self.assertEqual(actual["boundary_crs"], "EPSG:4326 longitude,latitude degrees")
            self.assertEqual(len(actual["buildings"]), area["building_denominator"])
            ids.update(b["id"] for b in actual["buildings"])
            self.assertTrue(all(b["raw_record"]["path"].startswith("data/raw/footprints/") for b in actual["buildings"]))
        self.assertEqual(len(ids), self.manifest["unique_source_buildings"])
        self.assertEqual(len(ids), 918)

    def test_source_edges_never_become_verified_walls_or_default_height_material(self):
        for area in self.manifest["areas"]:
            actual = json.loads((self.root/area["details"]).read_text())
            for b in actual["buildings"]:
                self.assertIsNone(b["height_m"])
                for f in b["facades"]:
                    self.assertEqual(set(f["components"]), set(ELEMENTS))
                    self.assertIsNone(f["height_m"])
                    self.assertEqual(f["exposure"], "unknown_may_be_party_wall")
                    self.assertTrue(0 <= f["outward_azimuth_degrees"] < 360)
                    self.assertFalse(f["current_complete"])
                    self.assertFalse(f["procedural"])
                    self.assertIsNone(f["generalized_material"])

    def test_face_ids_repeat_for_the_same_source_without_merging_neighbours(self):
        area = json.loads((self.root/"manhattan-grove/area.json").read_text())
        with sqlite3.connect(f"file:{ROOT}/data/processed/city/buildings.sqlite?mode=ro",uri=True) as db:
            for b in area["buildings"]:
                record=json.loads(db.execute("select payload from buildings where id=?",(b["id"],)).fetchone()[0])
                regenerated=facade_candidates(record)
                self.assertEqual([f["id"]for f in regenerated],[f["id"]for f in b["facades"]])
                self.assertTrue(all(f["building_id"] == b["id"] for f in regenerated))
                self.assertEqual(len({f["id"]for f in regenerated}),len(regenerated))

    def test_real_homography_controls_round_trip_and_degenerate_input_is_rejected(self):
        controls = self.street["fronts"]
        for f in controls:
            h = np.array(f["image_to_texture_homography"])
            p = np.column_stack([f["source_quad_native_px"], np.ones(4)])
            q = p@h.T;q=q[:,:2]/q[:,2:]
            restored=np.column_stack([q,np.ones(4)])@np.linalg.inv(h).T
            restored=restored[:,:2]/restored[:,2:]
            self.assertLess(float(np.max(np.abs(restored-p[:,:2]))),1e-7)
            self.assertLess(f["control_reprojection_error_pixels"],1e-7)
        with self.assertRaises(ValueError):
            homography([[0,0],[1,0],[2,0],[3,0]],[[0,0],[1,0],[1,1],[0,1]])

    def test_public_domain_scope_is_individual_and_original_bytes_are_preserved(self):
        self.assertIn("original measured drawings", self.street["rights"]["114_habs.html"])
        self.assertIn("public domain", self.street["rights"]["482_high.html"])
        self.assertEqual(hashlib.sha256((ROOT/self.street["photo_source"]).read_bytes()).hexdigest(),self.street["photo_sha256"])
        self.assertEqual(len({f["texture_sha256"]for f in self.street["fronts"]}),4)
        for f in self.street["fronts"]:
            self.assertEqual(f["observation_date"],"1936-08-25")
            self.assertFalse(f["current_wall_match_verified"])
            self.assertFalse(f["inpainting"])
            self.assertGreater(f["unknown_pixel_fraction"],.25)
        self.assertFalse(self.street["physical_world_replacement_allowed"])

    def test_actual_unknown_pixels_are_opaque_neutral_not_inpainted(self):
        result=subprocess.run(["/usr/bin/python3","-c", """
import json,numpy as np
from PIL import Image
from pathlib import Path
p=Path('assets/facades/grove-1936')
m=json.loads((p/'texture-processing.json').read_text())
for f in m['fronts']:
 a=np.array(Image.open(p/f['texture']));mask=np.array(Image.open(p/f['mask']))
 assert a.shape[2]==3
 assert np.all(a[mask==0]==[148,151,152])
 assert abs(float((mask>0).mean())-f['known_pixel_fraction'])<1e-9
print('actual four neutral masks checked')
"""],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_distinct_metric_uvs_clamp_and_opaque_fragments_keep_original_ids(self):
        g,b=read_glb((self.root/"grove-1936/model.glb").read_bytes())
        self.assertTrue(g["extras"]["historical_reference_only"])
        self.assertFalse(g["extras"]["current_replacement_allowed"])
        self.assertEqual(len(g["images"]),4)
        self.assertEqual(g["samplers"][0]["wrapS"],33071)
        self.assertEqual(g["samplers"][0]["wrapT"],33071)
        primitives=g["meshes"][0]["primitives"];self.assertEqual(len(primitives),4)
        for i,p in enumerate(primitives):
            self.assertRegex(p["extensions"]["EXT_mesh_features"]["featureIds"][0]["label"],
                             r"^[A-Za-z_][A-Za-z_0-9]*$")
            item=g["accessors"][p["attributes"]["TEXCOORD_0"]]
            view=g["bufferViews"][item["bufferView"]]
            uv=np.frombuffer(b,dtype="<f4",offset=view.get("byteOffset",0)+item.get("byteOffset",0),
                             count=item["count"]*2).reshape((-1,2))
            self.assertTrue(np.all((uv>=0)&(uv<=1)))
            self.assertEqual(uv[:,0].tolist(),[1,0,0,1]) # photograph east is on its left
            self.assertEqual(p["material"],i)
            self.assertEqual(g["materials"][i]["alphaMode"],"OPAQUE")
            self.assertFalse(g["materials"][i]["doubleSided"])
            v=accessor(g,b,p["attributes"]["POSITION"])
            self.assertAlmostEqual(float(v[:,1].max()-v[:,1].min()),self.street["fronts"][i]["historical_plane_height_m"],places=3)
        self.assertEqual(g["extras"]["complete_buildings"],0)

    def test_registration_conflict_and_front_only_coverage_do_not_become_completed_street(self):
        self.assertTrue(any(abs(f["width_conflict_m"])>.1 for f in self.street["fronts"]))
        self.assertEqual(self.street["photo_direction_evidence"]["image_order_left_to_right"],["10","8","6","4"])
        self.assertEqual(self.manifest["current_verified_facades"],0)
        self.assertEqual(self.manifest["current_complete_streets"],0)
        self.assertEqual(self.manifest["procedural_facades"],0)
        self.assertEqual(self.manifest["default_mode"],"evidence")
        self.assertEqual(self.street["complete_historical_facades"],0)
        self.assertEqual(self.street["geometry_count"]["facade_fragments"],4)


if __name__ == "__main__":
    unittest.main()
