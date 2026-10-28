"""CRC/SHA-verified local study package, with actual tested JS and public-domain originals."""
import hashlib
import json
import re
import zipfile
from urllib.parse import urlparse
from nyc.download import ROOT, atomic_json, now, sha


def main():
    browser = json.loads((ROOT/"reports/stage6/browser.json").read_text())
    landmarks = json.loads((ROOT/"reports/stage6/landmarks/browser.json").read_text())
    quality = json.loads((ROOT/"reports/stage6/quality.json").read_text())
    integrity = json.loads((ROOT/"reports/stage6/input-integrity.json").read_text())
    if browser["errors"] or len(browser["checks"])!=8 or landmarks["errors"] or not integrity["prior_raw_unchanged"]:
        raise ValueError("Candidate runtime/input checks incomplete")
    app = ROOT/"dist"
    requested = {urlparse(u).path for u in browser["requests"]+landmarks["requests"]}
    entries = set()
    paths = {}
    for page in ["facades.html","landmarks.html"]:
        html=(app/page).read_text()
        current=set(re.findall(r'["\']\./(assets/[^"\']+)["\']',html))
        if not current or any("/"+p not in requested for p in current):
            raise ValueError("Entry JS differs from actual tested candidate: "+page)
        entries.update(current)
        paths["app/"+page]=app/page
    paths["app/index.html"]=app/"facades.html"
    for name in sorted(requested):
        if name.startswith("/assets/"):
            p=app/name.lstrip("/")
            if not p.exists():
                raise ValueError("Actual tested JS no longer current: "+name)
            paths["app"+name]=p
    for directory in ["cesium","licenses","datasets/facades","datasets/landmarks"]:
        for p in sorted((app/directory).rglob("*")):
            if p.is_file(): paths["app/"+str(p.relative_to(app))]=p
    mappings=json.loads((ROOT/"data/manifests/stage5/replacement-map.json").read_text())
    for mapping in mappings:
        if mapping.get("context_source"):
            c=mapping["context_source"]
            assert sha(ROOT/"assets"/c["content"])==c["source_sha256"]
            for name in [c["content"],c["metadata"]]:
                paths["app/datasets/"+name]=ROOT/"assets"/name
                paths["source/assets/"+name]=ROOT/"assets"/name
    assert sha(ROOT/"assets/facades/grove-1936/model.glb")==quality["model_sha256"]
    for directory in ["src","scripts","tests","config","docs","assets/facades","assets/landmarks",
                      "landmarks","data/manifests/stage6","data/manifests/stage5"]:
        for p in sorted((ROOT/directory).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts:
                paths["source/"+str(p.relative_to(ROOT))]=p
    # Stage6 originals are identified LOC government/Highsmith public-domain material.
    # No stage5 research photo, commercial imagery or full-city original DB is copied.
    for p in sorted((ROOT/"data/raw/stage6").rglob("*")):
        if p.is_file(): paths["source/"+str(p.relative_to(ROOT))]=p
    for name in ["README.md","AGENTS.md","package.json","package-lock.json","requirements-lock.txt",
                 "tsconfig.json","vite.config.ts","index.html","terrain.html","buildings.html",
                 "landmarks.html","facades.html","THIRD_PARTY_NOTICES.md"]:
        paths["source/"+name]=ROOT/name
    for p in sorted((ROOT/"reports/stage6").rglob("*")):
        if p.is_file() and p.name not in ["release.json","package.log","standalone-browser.json",
                                        "standalone.log","standalone.png"]:
            paths[str(p.relative_to(ROOT))]=p
    paths["reports/FACADE_REVIEW.md"]=ROOT/"reports/FACADE_REVIEW.md"
    start="""NYC stage6 / source AOIs and dated facade studies

12 AOIs,918 retained source objects,10667 facade candidate edges.
4 separate1936 photograph wall fragments. Current verified facades0.
Complete current streets0. Roofs/stoops/railings/back facades and registration remain incomplete.
This is NOT complete ordinary-building reconstruction or a full-city exterior delivery.

Run from this directory:
  python3 -m http.server 8000 --bind127.0.0.1 --directory app
(Use a space: --bind 127.0.0.1)
Open http://localhost:8000/facades.html. index.html is an alias.
Default evidence mode shows source outlines. Explicitly enable1936 historical fragments.
The landmark inspector is retained, with its previous two partial representations.
External source links need Internet if clicked; core runtime is local.
file:// was not validated in the managed browser.

source/ contains modular source, configuration, per-face inventories, provenance and
identified LOC public-domain originals. Preserve raw bytes and read rights/source dates.
Full-city source DB/earlier datasets and private stage5 originals are NOT included.
Processing the full project requires those retained workspace inputs.
Read reports/FACADE_REVIEW.md and source/docs/NEXT_STEPS.md before continuing.
"""
    start=start.replace("--bind127.0.0.1","--bind 127.0.0.1").replace("(Use a space: --bind 127.0.0.1)\n","")
    target=ROOT/"reports/nyc-stage6-facade-studies.zip"
    temp=target.with_suffix(".zip.tmp")
    digests={}
    with zipfile.ZipFile(temp,"w",zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        z.writestr("START.txt",start)
        for name,p in sorted(paths.items()):
            digests[name]=sha(p);z.write(p,name)
        z.writestr("CHECKSUMS.json",json.dumps(digests,indent=2)+"\n")
    with zipfile.ZipFile(temp) as z:
        if z.testzip():raise ValueError("ZIP CRC failure")
        for name,expected in digests.items():
            h=hashlib.sha256()
            with z.open(name) as f:
                for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
            if h.hexdigest()!=expected:raise ValueError("ZIP SHA failure: "+name)
    temp.replace(target)
    atomic_json(ROOT/"reports/stage6/release.json",{
        "at_utc":now(),"path":str(target.relative_to(ROOT)),"bytes":target.stat().st_size,"sha256":sha(target),
        "checked_files":len(digests),"crc_and_every_payload_sha_checked":True,
        "tested_entry_assets":sorted(entries),"facade_browser_at":browser["at_utc"],
        "landmark_browser_at":landmarks["at"],"areas":12,"source_objects":918,"historical_fragments":4,
        "complete_current_streets":0,"current_verified_facades":0,
        "stage6_originals_included":True,"stage5_private_originals_included":False,
        "standalone_result":"reports/stage6/standalone-browser.json; separate actual execution",
        "scope":"local evidence inventories +4 historical fragments; not full city",
    })
    print("PACKAGE_VERIFIED",target.stat().st_size,"bytes",len(digests),"files",flush=True)


if __name__=="__main__":
    main()
