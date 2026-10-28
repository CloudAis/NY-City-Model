"""Audit real PLUTO parcel context for representative AOIs; do NOT assign building appearance."""
import csv
import json
from nyc.download import ROOT, atomic_json, sha


def main():
    manifest=json.loads((ROOT/"assets/facades/manifest.json").read_text())
    parcel_areas={}
    for a in manifest["areas"]:
        area=json.loads((ROOT/"assets/facades"/a["details"]).read_text())
        for b in area["buildings"]:
            if b["base_bbl"]:parcel_areas.setdefault(b["base_bbl"],set()).add(a["id"])
    counts={a["id"]:{}for a in manifest["areas"]}
    matches=[]
    source=ROOT/"data/intermediate/extracted/nyc_pluto_26v2_csv/pluto_26v2.csv"
    with source.open()as f:
        for row in csv.DictReader(f):
            key=row.get("bbl","").split(".")[0]
            if key not in parcel_areas:continue
            record={k:row.get(k)for k in ["bbl","address","landuse","bldgclass","numbldgs","numfloors","yearbuilt"]}
            record["area_memberships"]=sorted(parcel_areas[key])
            matches.append(record)
            for aid in parcel_areas[key]:
                value=row.get("landuse","")
                counts[aid][value]=counts[aid].get(value,0)+1
    # These are parcel-level checks for variety, not per-building classifications.
    if counts["bronx-hunts-point"].get("06",0)<1 or counts["queens-forest-hills"].get("01",0)<1:
        raise ValueError("Configured representative themes lack expected parcel context")
    atomic_json(ROOT/"reports/stage6/parcel-context.json",{
        "source":str(source.relative_to(ROOT)),"sha256":sha(source),"version":"PLUTO26v2",
        "dictionary":"data/raw/supporting/pluto_datadictionary.pdf",
        "dictionary_sha256":sha(ROOT/"data/raw/supporting/pluto_datadictionary.pdf"),
        "scope":"parcel context, NOT individual building use/floor/material/age assignment",
        "area_parcel_landuse_counts":counts,"matched_parcels":matches,
        "examples":"LandUse01 one/two family;03 multifamily elevator;05 commercial/office;06 industrial/manufacturing; definitions from retained official dictionary",
        "appearance_fields_overwritten":0})
    print("MATCHED_CONTEXT_PARCELS",len(matches),"BUILDING_APPEARANCE_WRITES",0,flush=True)


if __name__=="__main__":
    main()
