"""Package the actual tested partial landmark inspector, never a full-city claim."""
import hashlib
import json
import re
import zipfile
from urllib.parse import urlparse
from nyc.download import ROOT, sha, atomic_json, now


def main():
    evidence = json.loads((ROOT / "reports/stage5/browser.json").read_text())
    foundation = json.loads((ROOT / "reports/stage5/foundation/browser.json").read_text())
    quality = json.loads((ROOT / "reports/stage5/quality.json").read_text())
    integrity = json.loads((ROOT / "reports/stage5/input-integrity.json").read_text())
    if evidence["errors"] or len(evidence["checks"]) != 6 or foundation["errors"]:
        raise ValueError("Actual browser checks are incomplete")
    if quality["fine_model_complete"] != 0 or not integrity["tinnis_untouched"]:
        raise ValueError("Scope or original-input integrity changed")
    manifest = json.loads((ROOT / "assets/landmarks/manifest.json").read_text())
    paths = {}
    app = ROOT / "dist"
    html = (app / "landmarks.html").read_text()
    requested = {urlparse(u).path for u in evidence["requests"]}
    entry_assets = set(re.findall(r'["\']\./(assets/[^"\']+)["\']', html))
    if not entry_assets or any("/" + p not in requested for p in entry_assets):
        raise ValueError("Current entry build differs from actual tested candidate")
    runtime_assets = sorted(p for p in requested if p.startswith("/assets/"))
    for name in runtime_assets:
        p = app / name.lstrip("/")
        if not p.is_file():
            raise ValueError("Tested JavaScript is no longer the current build: " + name)
        paths["app" + name] = p
    paths["app/landmarks.html"] = app / "landmarks.html"
    paths["app/index.html"] = app / "landmarks.html"
    for directory in ["cesium", "licenses", "datasets/landmarks"]:
        for p in sorted((app / directory).rglob("*")):
            if p.is_file():
                paths["app/" + str(p.relative_to(app))] = p
    for item in manifest["landmarks"]:
        model = ROOT / "assets/landmarks" / item["slug"] / "model.glb"
        dossier = json.loads((model.parent / "dossier.json").read_text())
        if sha(model) != dossier["model_sha256"]:
            raise ValueError("Model changed since dossier checks")
        mapping = item["replacement"]
        if mapping.get("context_source"):
            context = mapping["context_source"]
            if sha(ROOT / "assets" / context["content"]) != context["source_sha256"]:
                raise ValueError("Original context changed")
            for key in ["content", "metadata"]:
                name = context[key]
                paths["app/datasets/" + name] = ROOT / "assets" / name
                paths["source/assets/" + name] = ROOT / "assets" / name
    for directory in ["src", "scripts", "tests", "docs", "landmarks",
                      "assets/landmarks", "data/manifests/stage5"]:
        for p in sorted((ROOT / directory).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts:
                paths["source/" + str(p.relative_to(ROOT))] = p
    for name in ["README.md", "AGENTS.md", "package.json", "package-lock.json",
                 "requirements-lock.txt", "tsconfig.json", "vite.config.ts",
                 "index.html", "terrain.html", "buildings.html", "landmarks.html",
                 "THIRD_PARTY_NOTICES.md"]:
        paths["source/" + name] = ROOT / name
    for p in sorted((ROOT / "data/raw/stage5/research").glob("*.receipt.json")):
        paths["source/" + str(p.relative_to(ROOT))] = p
    for p in sorted((ROOT / "reports/stage5").rglob("*")):
        if p.is_file() and p.suffix in [".json", ".csv", ".log", ".png"] and p.name not in [
            "release.json", "standalone-browser.json", "standalone.png"
        ]:
            paths[str(p.relative_to(ROOT))] = p
    paths["reports/LANDMARK_REVIEW.md"] = ROOT / "reports/LANDMARK_REVIEW.md"
    start = """NYC stage 5 / partial landmark inspection checkpoint

29 dossiers; 4 partly researched; 2 partial representations; 0 completed fine landmarks.
One WTC: partial faceted main volume and spire axis. 432 Park: structural grid lines only.
World ground datum, full facades/crowns and dated four-side verification remain unresolved.
This archive is NOT a full New York city model.

From this directory, run:
  python3 -m http.server 8000 --bind 127.0.0.1 --directory app
Open http://localhost:8000/landmarks.html (or /index.html).
Runtime assets are local. Source-reference links require Internet only if clicked.
Do not rely on file://; the managed browser blocks it and it was not validated.

source/ contains modular project source, dossiers and provenance.
The original full-city GIS database, raw photos/PDF/HTML, historic 3dm, and historical
entry-page datasets are NOT included. Restore them from the existing workspace or
recorded source URLs before a full processing rebuild. Unknown media licences are
reference-only; no downloaded research photo/PDF is redistributed here.
Read reports/LANDMARK_REVIEW.md and source/docs/NEXT_STEPS.md before continuing.
"""
    target = ROOT / "reports/nyc-stage5-landmark-studies.zip"
    tmp = target.with_suffix(".zip.tmp")
    hashes = {}
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6,
                         allowZip64=True) as archive:
        archive.writestr("START.txt", start)
        for name, path in sorted(paths.items()):
            if "data/raw/stage5/research/" in name and not name.endswith(".receipt.json"):
                raise ValueError("Private research original must not be redistributed")
            hashes[name] = sha(path)
            archive.write(path, name)
        archive.writestr("CHECKSUMS.json", json.dumps(hashes, indent=2) + "\n")
    with zipfile.ZipFile(tmp) as archive:
        if archive.testzip():
            raise ValueError("ZIP CRC failed")
        for name, expected in hashes.items():
            digest = hashlib.sha256()
            with archive.open(name) as f:
                for block in iter(lambda: f.read(1024 * 1024), b""):
                    digest.update(block)
            if digest.hexdigest() != expected:
                raise ValueError("ZIP read-back SHA mismatch: " + name)
    tmp.replace(target)
    atomic_json(ROOT / "reports/stage5/release.json", {
        "at_utc": now(), "path": str(target.relative_to(ROOT)), "bytes": target.stat().st_size,
        "sha256": sha(target), "checked_payload_files": len(hashes),
        "zip_crc_and_every_payload_sha_checked": True,
        "runtime_entry_assets_match_actual_browser": sorted(entry_assets),
        "actual_browser_at": evidence["at"], "foundation_browser_at": foundation["at"],
        "requested_dossiers": 29, "published_partial_representations": 2,
        "fine_models_complete": 0, "world_ground_registered": False,
        "research_originals_distributed": False,
        "standalone_browser_result": "reports/stage5/standalone-browser.json (separate actual execution)",
        "scope": "two local-reference studies and one exact-ID source neighbourhood; not full city",
    })
    print("PACKAGED", target, target.stat().st_size, flush=True)


if __name__ == "__main__":
    main()
