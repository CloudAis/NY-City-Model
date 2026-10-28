import json
import math
import sys
import hashlib
import unittest
from pathlib import Path
import numpy as np
from shapely.geometry import shape, Polygon, Point
from shapely.strtree import STRtree
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from nyc.download import ROOT
from nyc.buildings import triangulate
from test_buildings import read_glb, accessor


class EnvironmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=ROOT/"assets/environment"
        cls.m=json.loads((cls.root/"manifest.json").read_text())

    def test_twentyfive_real_coordinate_presets_cover_all_requested_types_and_boroughs(self):
        points=self.m["observations"]
        self.assertEqual(len(points),25);self.assertEqual(len({p["borough"]for p in points}),5)
        self.assertTrue({"cross-river","bridgehead","pier","interchange","park-boundary","slope"} <= {p["kind"]for p in points})
        self.assertTrue(all(-74.3<p["lon"]<-73.7 and 40.45<p["lat"]<40.95 for p in points))

    def test_actual_geometry_and_reference_only_height_do_not_become_physical_bridge_decks(self):
        for id in ["brooklyn-span","central-reservoir","grove-street","verrazzano-head"]:
            p=next(p for p in self.m["observations"]if p["id"]==id)
            context=json.loads((self.root/p["context"]).read_text())
            self.assertFalse(context["global_terrain_registered"])
            self.assertEqual(context["physical_road_bridge_surfaces"],0)
            for key in ["roads","water","sidewalk","transport","piers"]:
                info=p["layers"][key]
                if "tileset"not in info:continue
                gltf,data=read_glb((self.root/info["tileset"]).with_suffix(".glb").read_bytes())
                self.assertFalse(gltf["extras"]["physical_world_surface"])
                self.assertIsNone(gltf["extras"]["canonical_height_m"])
                self.assertTrue(gltf["extras"]["lift_is_only_draw_order"])
                self.assertTrue(all(shape(f["geometry"]).is_valid for f in context["features"][key]))

    def test_hidden_or_unknown_underground_rail_records_are_never_emitted_as_ground_tracks(self):
        seen=0
        for p in self.m["observations"]:
            context=json.loads((self.root/p["context"]).read_text())
            rails=context["features"]["rail"]
            self.assertTrue(all(f["render_as_ground_track"]is False for f in rails))
            ambiguous=sum(f["possible_hidden_underground"]for f in rails);seen+=ambiguous
            self.assertEqual(p["layers"]["rail"]["features"],len(rails)-ambiguous)
        self.assertGreater(seen,0)

    def test_true_central_and_prospect_park_boundaries_are_not_rectangles(self):
        parks=json.loads((self.root/"parks-source.json").read_text())["features"]
        self.assertEqual(len(parks),2)
        self.assertEqual({p["name"].upper()for p in parks},{"CENTRAL PARK","PROSPECT PARK"})
        for f in parks:
            p=shape(f["geometry"]);self.assertTrue(p.is_valid)
            self.assertNotAlmostEqual(p.area,p.envelope.area,places=10)

    def test_five_primary_bridge_dossiers_keep_clearance_separate_from_unresolved_absolute_height(self):
        bridges=json.loads((self.root/"bridges.json").read_text())["bridges"]
        self.assertEqual(len(bridges),5)
        for b in bridges:
            self.assertIsNone(b["deck_absolute_elevation_m"]);self.assertIsNone(b["deck_vertical_datum"])
            self.assertFalse(b["physical_world_placement_allowed"])
            self.assertTrue(b["source_values"])
            for value in b["source_values"]:
                self.assertEqual(hashlib.sha256((ROOT/value["path"]).read_bytes()).hexdigest(),value["sha256"])
                self.assertAlmostEqual(value["value_m"],value["source_value"]*.3048)

    def test_collision_uses_valid_actual_mesh_triangles_and_blocks_unknown_layers(self):
        for spec in self.m["walks"]:
            c=json.loads((self.root/spec["collision"]).read_text())
            source=ROOT/"assets/foundation"/c["terrain"]
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),c["terrain_source_sha256"])
            scene=json.loads(source.read_text());t=scene["terrain"]
            self.assertEqual(c["layer_id"],"ground");self.assertEqual(c["bridge_decks"],[])
            self.assertEqual(c["tunnel_interiors"],[]);self.assertFalse(c["building_interiors"])
            self.assertTrue(c["allowed_triangle_offsets"]);self.assertIsNotNone(c["spawn"])
            for offset in c["allowed_triangle_offsets"]:
                self.assertEqual(offset%3,0);self.assertLess(offset+2,len(t["indices"]))
                self.assertTrue(all(t["heights"][i]is not None for i in t["indices"][offset:offset+3]))

    def test_source_tree_positions_are_dated_points_not_invented_canopies(self):
        sources=json.loads((ROOT/"data/manifests/stage7/vector-sources.json").read_text())
        trees=next(s for s in sources if s["name"]=="trees")
        self.assertEqual(trees["unique_rows"],24164);self.assertFalse(trees["citywide_complete"])
        p=next(p for p in self.m["observations"]if p["id"]=="grove-street")
        g,_=read_glb((self.root/p["layers"]["trees"]["tileset"]).with_suffix(".glb").read_bytes())
        self.assertTrue(all(primitive["mode"]==0 for primitive in g["meshes"][0]["primitives"]))
        context=json.loads((self.root/p["context"]).read_text())
        self.assertTrue(all(f["source_period"]=="2015–2016 census"for f in context["features"]["trees"]))

    def test_two_real_park_dem_crops_keep_masks_dates_and_unresolved_world_registration(self):
        specs=json.loads((ROOT/'data/manifests/stage7/park-dem.json').read_text())
        self.assertEqual({s['id'] for s in specs},{'central-park','prospect-park'})
        for s in specs:
            self.assertEqual(hashlib.sha256((ROOT/s['masked_raster']).read_bytes()).hexdigest(),s['masked_sha256'])
            scene=json.loads((self.root/'terrain'/(s['id']+'.json')).read_text())
            self.assertFalse(scene['world_placement_allowed']);self.assertEqual(s['source_capture_period'][0],'2017-05-03')
            self.assertEqual(scene['terrain']['height_datum'],'NAVD88')
            self.assertIsNone(scene['terrain']['ecef_placement'])
            self.assertGreater(len(scene['terrain']['indices']),3000)
            self.assertEqual(scene['water'],[]) # Unknown lake levels are not filled at zero.

    def test_source_overlap_conflicts_remain_locatable_and_never_cut_buildings(self):
        rows=json.loads((ROOT/"reports/stage7/road-building-conflicts.json").read_text())
        self.assertTrue(rows)
        for r in rows:
            self.assertTrue(r["building_id"].startswith("nyc:footprints:"))
            self.assertIn("sha256",r["building_raw"]);self.assertGreater(r["area_m2"],.5)
            self.assertFalse(r["geometry_modified"])


if __name__=="__main__":
    unittest.main()
