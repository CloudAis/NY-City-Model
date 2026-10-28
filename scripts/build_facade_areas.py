"""Read-only city query -> 12 explicit AOIs and per-edge evidence inventories."""
import argparse
import json
import sqlite3
from pathlib import Path
from shapely.geometry import shape, box, mapping
from nyc.download import ROOT, atomic_json, sha, now
from nyc.coordinates import geographic_to_metric
from nyc.facades import facade_candidates, coverage
from nyc.buildings import classify, glb


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--area", help="Rebuild one configured AOI; default all")
    args = parser.parse_args()
    configuration = json.loads((ROOT / "config/facade-areas.json").read_text())
    db = sqlite3.connect(f"file:{ROOT}/data/processed/city/buildings.sqlite?mode=ro", uri=True)
    root = ROOT / "assets/facades"
    root.mkdir(parents=True, exist_ok=True)
    summaries = []
    for area in configuration["areas"]:
        folder = root / area["id"]
        if args.area and area["id"] != args.area:
            if not (folder / "area.json").exists():
                raise ValueError("Run complete initial AOI build before individual rebuild")
            previous = json.loads((folder / "area.json").read_text())
            summaries.append(previous["summary"])
            continue
        w, s, e, n = area["bbox"]
        xy = [geographic_to_metric(x, y) for x, y in [(w, s), (w, n), (e, s), (e, n)]]
        xs, ys = zip(*xy)
        rows = db.execute("""SELECT b.payload FROM spatial r JOIN buildings b ON b.rowid=r.row_id
            WHERE r.minx<=? AND r.maxx>=? AND r.miny<=? AND r.maxy>=?
            AND b.borough=? AND b.capture=? ORDER BY b.id""",
            [max(xs)+1, min(xs)-1, max(ys)+1, min(ys)-1, area["borough"],
             configuration["source_capture"]+":"+area["borough"]])
        records = [json.loads(row[0]) for row in rows]
        records = [r for r in records if not r["placeholder"] and
                   shape(r["geometry_wgs84"]).intersects(box(w, s, e, n))]
        if not records or len(records) > 2000:
            raise ValueError("Empty/excessive AOI: " + area["id"])
        buildings = []
        for r in records:
            buildings.append({
                "id": r["id"], "source_id": r["source_id"], "bin": r["bin"],
                "base_bbl": r["base_bbl"], "name": r["name"], "raw_record": r["raw_record"],
                "geometry_wgs84": r["geometry_wgs84"], "source_version": r["source_version"],
                "outline_type": "overhead, wall baseline unverified", "height_m": None,
                "wall_shape_verified": False, "roof_status": "unknown", "facades": facade_candidates(r),
                "reference_coverage": "no current per-facade photograph survey",
                "missing": ["dated current views", "wall geometry", "height/base datum", "material/components"],
                "use_classification": "area research theme only; no automatic parcel-to-building attribution",
            })
        origin = [(min(xs)+max(xs))/2, (min(ys)+max(ys))/2]
        payload, matrix, bounds, _ = glb([(classify(r), r["geometry"]) for r in records], origin, "strict")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "outline.glb").write_bytes(payload)
        atomic_json(folder / "tileset.json", {"asset": {"version": "1.1"}, "geometricError": 100,
            "root": {"boundingVolume": {"box": bounds}, "transform": matrix, "geometricError": 100,
            "refine": "REPLACE", "children": [{"boundingVolume": {"box": bounds}, "geometricError": 0,
                "content": {"uri": "outline.glb"}}]}})
        cameras = [
            {"id": "north", "label": "北侧街墙", "azimuth_deg": 0, "pitch_deg": -22, "range_m": 220},
            {"id": "east", "label": "东侧检查", "azimuth_deg": 90, "pitch_deg": -22, "range_m": 220},
            {"id": "south", "label": "南侧检查", "azimuth_deg": 180, "pitch_deg": -22, "range_m": 220},
            {"id": "west", "label": "西侧检查", "azimuth_deg": 270, "pitch_deg": -22, "range_m": 220},
            {"id": "overview", "label": "边界俯视", "azimuth_deg": 0, "pitch_deg": -75, "range_m": 380},
        ]
        summary = {**area, **coverage(buildings), "tileset": area["id"]+"/tileset.json",
                   "details": area["id"]+"/area.json", "source_building_ids": [r["id"] for r in records],
                   "complete_street": False, "category_status": "research_theme_NOT_verified_individual_use"}
        atomic_json(folder / "area.json", {"summary": summary,
            "boundary": mapping(box(w, s, e, n)), "boundary_crs": "EPSG:4326 longitude,latitude degrees",
            "selection_rule": "full source object intersects explicit boundary; never clip buildings or merge neighbours",
            "origin_metric_m": origin, "fixed_observation_path": cameras,
            "light": "fixed neutral day; no fog/bloom", "buildings": buildings})
        summaries.append(summary)
        print("AOI", area["id"], len(buildings), summary["facade_candidate_denominator"], flush=True)
    db.close()
    ids = {b for a in summaries for b in a["source_building_ids"]}
    atomic_json(root / "manifest.json", {"schema_version": 6, "created_at_utc": now(),
        "source_capture": configuration["source_capture"], "areas": summaries, "area_count": len(summaries),
        "unique_source_buildings": len(ids), "area_memberships": sum(a["building_denominator"] for a in summaries),
        "current_complete_streets": 0, "current_verified_facades": 0, "procedural_facades": 0,
        "default_mode": "evidence", "random_completion_implemented": False,
        "history": "grove-1936/street.json", "history_tileset": "grove-1936/tileset.json",
        "config_sha256": sha(ROOT / "config/facade-areas.json"),
        "processor_sha256": sha(Path(__file__)),
        "coverage_note": "AOI coverage is NOT completed appearance coverage; facade candidates are source edges"})
    atomic_json(ROOT / "data/manifests/stage6/areas.json", json.loads((root / "manifest.json").read_text()))


if __name__ == "__main__":
    main()
