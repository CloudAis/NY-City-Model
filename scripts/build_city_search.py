"""Static full-source search shards; no browser API/DB or invented names required."""
import json
import math
import sqlite3
from collections import defaultdict
from nyc.download import ROOT, atomic_json, now
from nyc.coordinates import metric_to_geographic


def compact(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    temp=p.with_suffix(p.suffix+".tmp")
    temp.write_text(json.dumps(value,ensure_ascii=False,separators=(",",":")))
    temp.replace(p)


def main():
    root=ROOT/"assets/inspection/search"
    ids=defaultdict(list);bins=defaultdict(list);names=defaultdict(list)
    known={}
    for folder in ["one-world-trade-center","432-park-avenue","empire-state-building","111-west-57th-street"]:
        p=ROOT/"landmarks"/folder/"dossier.json"
        if p.exists():
            d=json.loads(p.read_text());id=d.get("stable_building_id")
            if id:known[id]={"address":d.get("address"),"aliases":[d["name"]]}
    if "nyc:footprints:doitt:1114961"in known:
        known["nyc:footprints:doitt:1114961"]["aliases"].extend(["One WTC","1WTC"])
    for d in json.loads((ROOT/"config/grove-facade-controls.json").read_text())["fronts"]:
        known[d["building_id"]]={"address":d["address"],"aliases":[]}
    db=sqlite3.connect(f"file:{ROOT}/data/processed/building-stage4/city/associations.sqlite?mode=ro",uri=True)
    count=0
    for id,borough,state,meta in db.execute("SELECT id,borough,state,metadata FROM objects ORDER BY id"):
        m=json.loads(meta);x,y,xx,yy=m["bounds_metric_m"]
        a=metric_to_geographic(x,y);b=metric_to_geographic(xx,yy)
        extra=known.get(id,{})
        r={"id":id,"bin":m.get("bin"),"bbl":m.get("base_bbl"),"borough":borough,"name":m.get("name"),
           "address":extra.get("address"),"aliases":extra.get("aliases",[]),
           "bbox":[a[0],a[1],b[0],b[1]],"source_version":m["source_version"],
           "raw_record":m["raw_record"],"relative_height_raw_ft":m.get("relative_height_raw_ft"),
           "canonical_height_m":None,"ground_ellipsoid_m":None,"roof_status":m["roof_status"],
           "facade_status":m["facade_status"],"observation_date":m.get("observation_date"),
           "last_edited_at":m.get("last_edited_at"),"state":state,"feature_code":m.get("feature_code")}
        number=id.rsplit(":",1)[-1];bucket=number[-3:].zfill(3)
        ids[bucket].append(r);count+=1
        if r["bin"]and len(r["bin"])>=4:bins[r["bin"][:4]].append([r["bin"],id,borough])
        if r["name"]or r["address"]or r["aliases"]:names[borough].append(r)
        if count%100000==0:print("INDEXED",count,flush=True)
    db.close()
    for bucket,rows in ids.items():compact(root/"ids"/(bucket+".json"),rows)
    for bucket,rows in bins.items():compact(root/"bins"/(bucket+".json"),rows)
    for borough,rows in names.items():compact(root/"names"/(borough+".json"),rows)
    compact(root/"manifest.json",{"schema_version":8,"created_at_utc":now(),"source_records":count,
        "boroughs":["manhattan","brooklyn","queens","bronx","staten-island"],
        "id_bucket":"last3 decimal source-ID digits,zero padded","bin_bucket":"first4 BIN digits",
        "named_records":sum(map(len,names.values())),"names_are_current_verified":False,
        "bin_buckets":sorted(bins),"id_buckets":sorted(ids),
        "address_scope":"Only retained identified landmark/4Grove address evidence; no parcel address spread",
        "common_source":"NYC official footprints,capture2026-10-27-city; individual observation dates may be unknown",
        "height_rule":"raw feet only; canonical heights/ground still unresolved",
        "spatial_bounds":"actual source projected bbox formally converted to geographic, not building body or roof evidence"})
    print("SEARCH_READY",count,"NAMED",sum(map(len,names.values())),flush=True)


if __name__=="__main__":
    main()
