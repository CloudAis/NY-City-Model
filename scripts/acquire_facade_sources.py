"""Reacquire only recorded, actually discovered source URLs; immutable raw cache."""
import argparse
import json
from pathlib import Path
from nyc.download import ROOT, Downloader, atomic_json, sha, now


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--refresh", action="store_true")
    a = p.parse_args()
    registry = json.loads((ROOT/"data/manifests/stage6/sources.json").read_text())
    downloader = Downloader(timeout=35, retries=2, interval=.5, max_bytes=32*1024*1024)
    events = []
    for source in registry["files"]:
        path = Path(source["path"])
        kind = "json" if path.suffix == ".json" else "html" if path.suffix == ".html" else (
            "image" if path.suffix in [".tif", ".jpg", ".png"] else "text" if path.suffix == ".csv" else "binary")
        try:
            result = downloader.get(source.get("request_url", source["url"]), path, kind, refresh=a.refresh)
            events.append({"source": str(path), "path": str(result.relative_to(ROOT)),
                           "sha256": sha(result), "matches_retained_version": sha(result)==source["sha256"]})
        except Exception as e:
            events.append({"source": str(path), "error": str(e)})
    atomic_json(ROOT/"reports/stage6/source-cache.json",
                {"at_utc": now(), "events": events, "refresh": a.refresh,
                 "raw_overwrite_allowed": False})
    if any("error" in e for e in events):
        raise ValueError("Some source retrievals failed; see source-cache.json")
    print("SOURCE_CACHE_VERIFIED", len(events), flush=True)


if __name__ == "__main__":
    main()
