"""Actual perspective correction, neutral occlusion masks and per-building UV assets.

Run with /usr/bin/python3 (installed Pillow/numpy); no generated image completion.
"""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from PIL import Image, ImageOps, __version__ as PILLOW_VERSION
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from nyc.facade_math import homography


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    controls = json.loads((ROOT / "config/grove-facade-controls.json").read_text())
    rows = list(csv.DictReader((ROOT / "data/raw/stage6/catalog/loc-rights-table.csv")
                              .read_text(encoding="cp1252", errors="replace").splitlines()))
    rights = {r["id"]: r for r in rows if r["id"] in ["482_high.html", "114_habs.html"]}
    if "public domain" not in rights["114_habs.html"]["publication"].lower():
        raise ValueError("Government drawing/photo permission not found")
    catalog = json.loads((ROOT / controls["source_catalog"]).read_text())
    photo_caption = next(f["title"] for f in catalog["resources"][0]["files"][0] if f.get("use") == "caption")
    if "Arnold Moses" not in photo_caption or "August 25, 1936" not in photo_caption:
        raise ValueError("Individual original government photograph not identified")
    raw = ROOT / controls["source_image"]
    image = Image.open(raw).convert("RGB")
    if list(image.size) != controls["native_size"]:
        raise ValueError("Source dimensions changed")
    folder = ROOT / "assets/facades/grove-1936"
    folder.mkdir(parents=True, exist_ok=True)
    preview = image.copy()
    preview.thumbnail((1800, 1400))
    preview.save(folder / "source-photo.jpg", quality=92)
    drawing = Image.open(ROOT / controls["source_drawing"]).convert("RGB")
    drawing.thumbnail((1800, 1500))
    drawing.save(folder / "source-drawing.jpg", quality=92)
    scale = controls["drawing_scale"]
    ppm = np.linalg.norm(np.array(scale["twenty_five_feet_pixel"]) - scale["zero_pixel"]) / (25 * .3048)
    wall_h = (scale["front_grade_y"] - scale["front_cornice_top_y"]) / ppm
    first = controls["fronts"][0]
    width = np.linalg.norm(np.array(first["front_metric"][1]) - first["front_metric"][0])
    preview_ratio = image.width / controls["source_preview_size"][0]
    first_quad = np.array(first["quad_preview"], dtype=float) * preview_ratio
    # One planar reference from4's drawing-derived wall height and retained source
    # width. It cannot prove that the1936 plane matches the current overhead outline.
    # The north-facing street is viewed from the north. Photograph left is east:
    # address order in the photo is10,8,6,4, not4,6,8,10.
    street_H = homography(first_quad, [[width, wall_h], [0, wall_h], [0, 0], [width, 0]])
    reports = []
    for front in controls["fronts"]:
        quad = np.array(front["quad_preview"], dtype=float) * preview_ratio
        projected = np.column_stack([quad, np.ones(4)]) @ street_H.T
        projected = projected[:, :2] / projected[:, 2:]
        derived_height = float(np.mean(projected[:2, 1]) - np.mean(projected[2:, 1]))
        edge_x = [float(np.mean(projected[[0, 3], 0])), float(np.mean(projected[[1, 2], 0]))]
        derived_width = abs(edge_x[1]-edge_x[0])
        current_width = float(np.linalg.norm(np.array(front["front_metric"][1]) - front["front_metric"][0]))
        if not (1 < derived_height < 20 and derived_width > 0):
            raise ValueError("Unusable archival plane fit")
        # Preserve derived image aspect, never silently stretch to a source footprint.
        out_w = min(1024, max(256, round(derived_width * 100)))
        out_h = min(1536, max(256, round(out_w * derived_height / derived_width)))
        destination = [[0, 0], [out_w-1, 0], [out_w-1, out_h-1], [0, out_h-1]]
        forward = homography(quad, destination)
        inverse = np.linalg.inv(forward)
        inverse /= inverse[2, 2]
        result = image.transform((out_w, out_h), Image.Transform.PERSPECTIVE,
            tuple(inverse.flatten()[:8]), Image.Resampling.BICUBIC)
        data = np.array(result)
        y, x = np.indices((out_h, out_w))
        policy = controls["mask_policy"]
        known = ((y >= out_h * policy["upper_v_fraction"]) &
                 (y < out_h * policy["lower_v_fraction"]) &
                 (x >= out_w * policy["edge_fraction"]) &
                 (x < out_w * (1-policy["edge_fraction"])))
        if front["address"].startswith("10 "):
            known &= x < out_w * .93
        data[~known] = policy["neutral_rgb"]
        # Grayscale source: no fabricated brick colour or cross-building colour transfer.
        name = front["address"].split()[0]
        texture = folder / f"front-{name}.png"
        Image.fromarray(data).save(texture)
        Image.fromarray((known * 255).astype("uint8")).save(folder / f"mask-{name}.png")
        reprojection = np.column_stack([quad, np.ones(4)]) @ forward.T
        reprojection = reprojection[:, :2] / reprojection[:, 2:]
        reports.append({**front, "texture": texture.name, "texture_sha256": digest(texture),
            "mask": f"mask-{name}.png", "size_px": [out_w, out_h],
            "source_quad_native_px": quad.tolist(), "image_to_texture_homography": forward.tolist(),
            "metric_derivation": "4Grove drawing graphic scale + retained source-width reference + common-photo-plane projection; NOT independently calibrated",
            "historical_plane_width_m": derived_width, "historical_plane_height_m": derived_height,
            "historical_plane_left_m": min(edge_x),
            "photo_u_increases_world_west": True,
            "current_source_front_width_m": current_width,
            "width_conflict_m": derived_width-current_width,
            "source_metric_accuracy_m": None, "current_wall_match_verified": False,
            "known_pixel_fraction": float(known.mean()),
            "unknown_pixel_fraction": float(1-known.mean()),
            "control_reprojection_error_pixels": float(np.max(np.linalg.norm(reprojection-destination, axis=1))),
            "colour_operation": "none; grayscale source retained, no simulated albedo recovery",
            "inpainting": False, "generated_completion": False,
            "uv_policy": "separate0..1 per facade; no repeat wrapping; photo aspect preserved on historical reference plane",
            "observation_date": "1936-08-25", "current_complete": False})
    manifest = {"schema_version": 6, "fronts": reports, "photo_source": controls["source_image"],
        "photo_sha256": digest(raw), "drawing_sha256": digest(ROOT / controls["source_drawing"]),
        "controls_sha256": digest(ROOT / "config/grove-facade-controls.json"),
        "processor_sha256": digest(Path(__file__)), "pillow_version": PILLOW_VERSION,
        "numpy_version": np.__version__, "rights_table_sha256": digest(ROOT / "data/raw/stage6/catalog/loc-rights-table.csv"),
        "rights": {k: re.sub("<[^>]*>", " ", v["publication"]) for k, v in rights.items()},
        "credit": "Library of Congress, Prints & Photographs Division, HABS NY-449; photograph Arnold Moses,1936-08-25; drawings Harry Davis Riley",
        "licence_scope": "Only identified original HABS government photo119530p and measured sheet1; no third-party copied image used",
        "rights_table_decode": "cp1252; invalid legacy bytes replaced only during text parsing; raw preserved",
        "drawing_scale_px_per_m": float(ppm), "drawing_front_wall_height_m": float(wall_h),
        "physical_world_replacement_allowed": False,
        "current_verified_facades": 0, "complete_historical_facades": 0,
        "photo_direction_evidence": controls["photo_direction_evidence"],
        "note": "Four distinct partial historical wall fragments, not four complete buildings or a completed current street"}
    (folder / "texture-processing.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n")
    target = ROOT / "data/manifests/stage6/texture-sources.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n")
    print("RECTIFIED_ACTUAL_FACADES", len(reports), "CURRENT_COMPLETE", 0, flush=True)


if __name__ == "__main__":
    main()
