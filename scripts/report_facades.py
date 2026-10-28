"""Coverage, conflicts and a locatable acquisition queue; never inflate appearance completion."""
import csv
import json
from pathlib import Path
from nyc.download import ROOT, atomic_json, now, sha


def main():
    manifest = json.loads((ROOT/"assets/facades/manifest.json").read_text())
    street = json.loads((ROOT/"assets/facades/grove-1936/street.json").read_text())
    browser = json.loads((ROOT/"reports/stage6/browser.json").read_text())
    foundation = json.loads((ROOT/"reports/stage6/foundation/browser.json").read_text())
    tests = (ROOT/"reports/stage6/tests.log").read_text()
    if browser["errors"] or len(browser["checks"]) != 8 or foundation["errors"] or len(foundation["checks"]) != 8 or "Ran 44 tests" not in tests or not tests.rstrip().endswith("OK"):
        raise ValueError("Actual stage6 validation incomplete")
    folder = ROOT/"reports/stage6"
    queue = []
    facade_rows = []
    buildings_with_archive = set()
    archived_edges = 0
    for area in manifest["areas"]:
        details = json.loads((ROOT/"assets/facades"/area["details"]).read_text())
        for building in details["buildings"]:
            if building.get("archival_front"):
                buildings_with_archive.add(building["id"])
            queue.append({"area": area["id"], "building_id": building["id"],
                "source_version": building["source_version"], "raw_record": building["raw_record"],
                "geometry": building["geometry_wgs84"], "current_state": "current exterior unverified",
                "historical_front": building.get("archival_front"),
                "needed": building["missing"],
                "priority": 1 if building.get("archival_front") else 2,
                "complete": False})
            for face in building["facades"]:
                archived_edges += bool(face.get("historical_evidence"))
                facade_rows.append([area["id"],building["id"],face["id"],face["part_id"],
                    face["outward_azimuth_degrees"],face["width_projected_m"],"",
                    "source-edge candidate, exposure unknown", "unknown",
                    "1936-08-25 partial" if face.get("historical_evidence") else "",
                    False,False])
    fields = ["area","building_id","facade_candidate_id","part_id","azimuth_deg","source_edge_width_m",
              "current_height_m","shape","current_evidence","historical_reference","current_complete","procedural"]
    with (folder/"facade-inventory.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(fields);w.writerows(facade_rows)
    with (folder/"area-coverage.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(["area","borough","theme_NOT_verified_use","source_buildings","facade_candidates","current_verified_facades","complete_current_streets"])
        for area in manifest["areas"]:
            w.writerow([area["id"],area["borough"],area["category"],area["building_denominator"],
                        area["facade_candidate_denominator"],0,0])
    conflicts = [{"building_id":f["building_id"],"address":f["address"],
        "historical_photo_plane_width_m":f["historical_plane_width_m"],
        "current_source_edge_width_m":f["current_source_front_width_m"],
        "difference_m":f["width_conflict_m"], "scope":"1936 common-plane manual projection vs retained overhead outline",
        "selection":"Keep values and separate dated reference; never stretch to fit or promote current truth",
        "independent_reality_error_m":None} for f in street["fronts"]]
    atomic_json(folder/"conflicts.json", conflicts)
    atomic_json(folder/"acquisition-queue.json", {"scope":"918 source objects in12 explicit areas, not city complete",
        "entries":queue, "no_random_replacement":True})
    atomic_json(folder/"texture-audit.json", {"source":street["photo_source"],
        "source_sha256":street["photo_sha256"], "date":"1936-08-25",
        "rights":street["rights"], "fronts":[{k:f[k]for k in [
            "address","building_id","texture","texture_sha256","size_px","unknown_pixel_fraction",
            "control_reprojection_error_pixels","width_conflict_m","current_complete"]} for f in street["fronts"]],
        "source_quality_unknown":True,"pixel_error_not_metric_accuracy":True,"inpainting":False,
        "colour_matching":"none, monochrome source; no physical albedo claim",
        "near_silhouette_geometry":"uncompleted: stairs, railings, cornice depths and roofs",
        "front_to_back_copy":False})
    quality = {
        "at_utc":now(), "areas":len(manifest["areas"]), "boroughs":5,
        "unique_source_buildings":manifest["unique_source_buildings"],
        "area_memberships":manifest["area_memberships"],"facade_candidate_edges":len(facade_rows),
        "physical_facade_denominator":None, "candidate_denominator_note":"source overhead segments, may include party walls or collinear fragments",
        "current_verified_buildings":0, "current_verified_building_fraction":0,
        "current_verified_facades":0,"current_verified_candidate_fraction":0,
        "current_complete_streets":0, "historical_fragments":4,
        "source_buildings_with_historical_fragment":len(buildings_with_archive),
        "historical_fragment_building_presence_fraction":len(buildings_with_archive)/manifest["unique_source_buildings"],
        "candidate_edges_with_partial_historical_reference":archived_edges,
        "complete_historical_facades":0,"procedural_facades":0,
        "mode":"default evidence; optional dated historical reference, removable in full",
        "raw_registry":"data/manifests/stage6/sources.json",
        "source_capture":"2026-10-27-city; observation date per current building unknown",
        "history_observation":"1936-08-25; drawing date unresolved",
        "street_processing":"all four distinct fronts processed, full street exterior acceptance remains incomplete",
        "checks":{"python":44,"facade_browser":8,"actual_areas_loaded":12,"fixed_views":5,
                  "foundation_browser":len(foundation["checks"]),"local_only":True},
        "render_limits":"opaque photo planes only; no invented roofs, stoops, back facades or interiors",
        "world_ground_registered":False, "independent_reality_error_m":None,
        "model_sha256":street["model_sha256"],
        "processor_sha256":sha(Path(__file__)),
    }
    atomic_json(folder/"quality.json", quality)
    atomic_json(ROOT/"assets/facades/quality.json", quality)
    print("FACADE_QUALITY",json.dumps(quality,ensure_ascii=False),flush=True)


if __name__ == "__main__":
    main()
