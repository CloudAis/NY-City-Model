"""Publish four distinct dated wall fragments; never replace current source geometry."""
import json
import struct
import math
from pathlib import Path
import numpy as np
from nyc.download import ROOT, atomic_json, sha
from nyc.coordinates import LocalFrame, metric_to_geographic, projected_vertices_to_local


def main():
    folder = ROOT / "assets/facades/grove-1936"
    source = json.loads((folder / "texture-processing.json").read_text())
    controls = json.loads((ROOT / "config/grove-facade-controls.json").read_text())
    first = controls["fronts"][0]
    anchor = np.array(first["front_metric"][0])
    direction = np.array(first["front_metric"][1]) - anchor
    direction /= np.linalg.norm(direction)
    frame = LocalFrame.at(*metric_to_geographic(*anchor), 0)
    blob = bytearray()
    views, accessors, primitives, clouds = [], [], [], []

    def buffer(data, target=None):
        blob.extend(b"\0" * (-len(blob) % 4))
        offset = len(blob)
        blob.extend(data)
        views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(data),
                      **({"target": target} if target else {})})
        return len(views)-1

    def attribute(data, kind, dtype, component):
        array = np.asarray(data, dtype=dtype)
        entry = {"bufferView": buffer(array.tobytes(), 34962), "componentType": component,
                 "type": kind, "count": len(array)}
        if kind == "VEC3":
            entry.update(min=array.min(axis=0).tolist(), max=array.max(axis=0).tolist())
        accessors.append(entry)
        return len(accessors)-1

    for i, front in enumerate(source["fronts"]):
        start = anchor + direction * front["historical_plane_left_m"]
        end = start + direction * front["historical_plane_width_m"]
        h = front["historical_plane_height_m"]
        # Archive planes preserve derived photo proportions, not forced into newer outlines.
        xy = [start, end, end, start]
        enu = projected_vertices_to_local(xy, [0, 0, h, h], frame)
        front["pick_point_local_enu_m"] = enu.mean(axis=0).tolist()
        pos = (enu[:, [0, 2, 1]] * [1, 1, -1]).astype("<f4")
        clouds.append(pos)
        # Front faces north: reverse winding because East x Up points south.
        indices = np.array([0, 2, 1, 0, 3, 2], dtype="<u4")
        face = np.cross(pos[indices[1]]-pos[indices[0]], pos[indices[2]]-pos[indices[0]])
        face /= np.linalg.norm(face)
        attrs = {
            "POSITION": attribute(pos, "VEC3", "<f4", 5126),
            "NORMAL": attribute([face]*4, "VEC3", "<f4", 5126),
            "TEXCOORD_0": attribute([[1, 1], [0, 1], [0, 0], [1, 0]], "VEC2", "<f4", 5126),
            "_FEATURE_ID_0": attribute([i]*4, "SCALAR", "<u4", 5125),
        }
        accessors.append({"bufferView": buffer(indices.tobytes(), 34963), "componentType": 5125,
                          "count": 6, "type": "SCALAR"})
        primitives.append({"attributes": attrs, "indices": len(accessors)-1, "mode": 4, "material": i,
            "extensions": {"EXT_mesh_features": {"featureIds": [{"attribute": 0, "featureCount": 4,
                "propertyTable": 0, "label": "facade"}]}}})
    properties, schema = {}, {}
    for key, values in {
        "id": [f["building_id"] for f in source["fronts"]],
        "facade_id": [f["building_id"]+":facade:historical-front:1936" for f in source["fronts"]],
        "address": [f["address"] for f in source["fronts"]],
        "date": ["1936-08-25"]*4,
        "status": ["partial_historical_photo_NOT_current_verified"]*4,
    }.items():
        text, offsets = bytearray(), [0]
        for value in values:
            text.extend(value.encode())
            offsets.append(len(text))
        properties[key] = {"values": buffer(text), "stringOffsets": buffer(np.array(offsets, dtype="<u4").tobytes()),
                           "stringOffsetType": "UINT32"}
        schema[key] = {"type": "STRING"}
    points = np.vstack(clouds)
    lower, upper = points.min(axis=0), points.max(axis=0)
    lo, hi = [lower[0], -upper[2], lower[1]], [upper[0], -lower[2], upper[1]]
    centre = [(float(a)+float(b))/2 for a, b in zip(lo, hi)]
    half = [max(.02, (float(b)-float(a))/2) for a, b in zip(lo, hi)]
    bounds = centre+[half[0], 0, 0, 0, half[1], 0, 0, 0, half[2]]
    gltf = {
        "asset": {"version": "2.0", "generator": "NYC dated facade-fragment pipeline6"},
        "extensionsUsed": ["EXT_mesh_features", "EXT_structural_metadata", "KHR_materials_unlit"],
        "extensions": {"EXT_structural_metadata": {"schema": {"id": "facade-evidence",
            "classes": {"facade": {"properties": schema}}}, "propertyTables": [{"class": "facade", "count": 4,
                "properties": properties}]}},
        "buffers": [{"byteLength": len(blob)}], "bufferViews": views, "accessors": accessors,
        "images": [{"uri": f["texture"]} for f in source["fronts"]],
        "samplers": [{"wrapS": 33071, "wrapT": 33071, "magFilter": 9729, "minFilter": 9987}],
        "textures": [{"sampler": 0, "source": i} for i in range(4)],
        "materials": [{"name": f["address"]+"-1936-distinct-fragment",
            "alphaMode": "OPAQUE", "doubleSided": False,
            "pbrMetallicRoughness": {"baseColorTexture": {"index": i},
                "metallicFactor": 0, "roughnessFactor": 1},
            "extensions": {"KHR_materials_unlit": {}}} for i, f in enumerate(source["fronts"])],
        "meshes": [{"primitives": primitives}], "nodes": [{"mesh": 0}],
        "scenes": [{"nodes": [0]}], "scene": 0,
        "extras": {"units": "metre", "axes": "East,Up,-North", "frame": frame.manifest(),
            "current_verified_facades": 0, "complete_buildings": 0, "current_replacement_allowed": False,
            "historical_reference_only": True, "has_invented_rear": False,
            "roof_stoops_railings": "not modelled; occluded photograph areas masked neutral",
            "ground": "explicit local display zero, NOT registered real ground",
            "texture_role": source["note"], "source_manifest_sha256": sha(folder / "texture-processing.json")}
    }
    encoded = json.dumps(gltf, separators=(",", ":")).encode()
    encoded += b" " * (-len(encoded) % 4)
    blob.extend(b"\0" * (-len(blob) % 4))
    payload = struct.pack("<4sII", b"glTF", 2, 28+len(encoded)+len(blob))
    payload += struct.pack("<II", len(encoded), 0x4e4f534a)+encoded
    payload += struct.pack("<II", len(blob), 0x004e4942)+blob
    (folder / "model.glb").write_bytes(payload)
    atomic_json(folder / "tileset.json", {"asset": {"version": "1.1"}, "geometricError": 100,
        "root": {"transform": list(frame.matrix_enu_to_ecef), "boundingVolume": {"box": bounds},
            "geometricError": 100, "children": [{"boundingVolume": {"box": bounds}, "geometricError": 0,
                "content": {"uri": "model.glb"}}]}})
    street = {**source, "frame": frame.manifest(), "model_sha256": sha(folder / "model.glb"),
        "fixed_path": [
            {"id": "front", "label": "街墙正面", "enu_camera": [12, 43, 7], "enu_target": [12, 0, 4]},
            {"id": "left", "label": "左侧接缝", "enu_camera": [-12, 28, 8], "enu_target": [10, 0, 4]},
            {"id": "right", "label": "右侧接缝", "enu_camera": [38, 25, 8], "enu_target": [14, 0, 4]},
            {"id": "close", "label": "窗格近看", "enu_camera": [10, 14, 5], "enu_target": [10, 0, 4]},
            {"id": "rear", "label": "背面缺口", "enu_camera": [12, -28, 9], "enu_target": [12, 0, 4]}
        ],
        "geometry_count": {"facade_fragments": 4, "triangles": 8, "complete_buildings": 0},
        "replacement_policy": "Never hide current footprints or substitute these1936 fragments for2026 buildings",
        "remaining": controls["missing_geometry"]}
    atomic_json(folder / "street.json", street)
    area_file = ROOT / "assets/facades/manhattan-grove/area.json"
    area = json.loads(area_file.read_text())
    for building in area["buildings"]:
        front = next((f for f in source["fronts"] if f["building_id"] == building["id"]), None)
        if not front:
            continue
        building["archival_front"] = {
            "date": "1936-08-25", "source": "https://www.loc.gov/item/ny0381/",
            "association": "retained current source BBL/one source entity + PLUTO address + street sequence; historical wall match not independently verified",
            "texture": "../grove-1936/"+front["texture"], "scope": "partial historical front only",
            "width_conflict_m": front["width_conflict_m"], "current_complete": False,
        }
        for facade in building["facades"]:
            angle = facade["outward_azimuth_degrees"]
            if angle < 25 or angle > 345:
                facade["historical_evidence"] = {"date": "1936-08-25", "status": "partial_historical",
                    "material": front["wall_material"], "source": "HABS NY-449 photo119530p",
                    "occlusion": "foreground and uncertain edge pixels neutral-masked",
                    "components": {
                        "wall_material": front["wall_material"],
                        "window_grid": {"status": "derived_historical_photo", "value": "3 upper main-storey openings,2 lower main-storey windows plus separate doorway; cropped basement/attic not counted", "source": "individual photo119530p region"},
                        "floor_divisions": {"status": "derived_historical_photo", "value": "two main street-facing storeys visible; current floor count not inferred"},
                        "cornice": {"status": "partial_historical_photo", "value": "individual roofline visible in original; projection depth not measured, shadow mask excluded"},
                        "entrance": {"status": "partial_occluded", "value": "each doorway retained separately; lower steps/fence masked"},
                        "porch": {"status": "unknown_metric_geometry", "value": None},
                        "balcony": {"status": "unknown", "value": None},
                        "fire_escape": {"status": "unknown", "value": None},
                        "roof_equipment": {"status": "unknown_metric_geometry", "value": None}
                    },
                    "current_verified": False}
    atomic_json(area_file, area)
    atomic_json(ROOT / "data/manifests/stage6/street.json", street)
    print("ARCHIVAL_FRAGMENTS", 4, "COMPLETE_CURRENT_STREETS", 0, flush=True)


if __name__ == "__main__":
    main()
