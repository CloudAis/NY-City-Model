"""Facade evidence inventory. Source outline edges are candidates, not verified walls."""
import hashlib
import json
import math
from shapely.geometry import shape
from shapely.geometry.polygon import orient
from .coordinates import metric_to_geographic, LocalFrame, projected_vertices_to_local
from .facade_math import homography

ELEMENTS = ["wall_material", "window_grid", "floor_divisions", "cornice", "entrance",
            "porch", "balcony", "fire_escape", "roof_equipment"]


def facade_candidates(record):
    geometry = shape(record["geometry"])
    polygons = [geometry] if geometry.geom_type == "Polygon" else list(geometry.geoms)
    faces = []
    for part, polygon in enumerate(polygons):
        polygon = orient(polygon, sign=1)
        for ring_index, ring in enumerate([polygon.exterior, *polygon.interiors]):
            for a, b in zip(ring.coords, list(ring.coords)[1:]):
                a, b = list(a[:2]), list(b[:2])
                width = math.dist(a, b)
                if width < .01:
                    continue
                middle = [(a[i] + b[i]) / 2 for i in range(2)]
                frame = LocalFrame.at(*metric_to_geographic(*middle), 0)
                enu = projected_vertices_to_local([a, b], 0, frame)
                edge = enu[1] - enu[0]
                outward = [edge[1], -edge[0]]  # solid is on the left, including holes
                azimuth = math.degrees(math.atan2(outward[0], outward[1])) % 360
                key = hashlib.sha256(json.dumps([a, b], separators=(",", ":")).encode()).hexdigest()[:16]
                faces.append({
                    "id": f"{record['id']}:facade-candidate:{part}:{ring_index}:{key}",
                    "building_id": record["id"], "part_id": record["parts"][part]["part_id"],
                    "ring_index": ring_index, "endpoints_metric_m": [a, b],
                    "endpoints_lon_lat": [metric_to_geographic(*a), metric_to_geographic(*b)],
                    "width_projected_m": width, "outward_azimuth_degrees": azimuth,
                    "shape_status": "derived_from_overhead_outline_NOT_verified_wall",
                    "vertical_shape": None, "height_m": None, "exposure": "unknown_may_be_party_wall",
                    "observation_date": None, "occlusion": "not_surveyed",
                    "evidence_status": "unknown", "reference_ids": [],
                    "components": {name: {"status": "unknown", "value": None, "source": None}
                                   for name in ELEMENTS},
                    "generalized_material": None, "procedural": False, "current_complete": False,
                })
    return faces


def coverage(buildings):
    faces = [f for b in buildings for f in b["facades"]]
    return {"building_denominator": len(buildings), "facade_candidate_denominator": len(faces),
            "buildings_with_any_current_verified_facade": sum(any(f["current_complete"] for f in b["facades"]) for b in buildings),
            "current_verified_facades": sum(f["current_complete"] for f in faces),
            "unknown_facade_candidates": sum(f["evidence_status"] == "unknown" for f in faces),
            "denominator_note": "source overhead edges, including possible shared walls; NOT independently surveyed facade count",
            "procedural_facades": 0}
