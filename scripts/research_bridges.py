"""Primary-source bridge dimensions, quantity scopes and explicit unresolved deck datum."""
import json
import re
from html import unescape
from nyc.download import ROOT, atomic_json, sha, now

FACTS={
 "brooklyn":{"name":"Brooklyn Bridge","values":[("length_with_approaches",6016,"Total length of bridge and approaches: 6,016 feet"),("main_span",1595.5,"Main span: 1,595.5 feet"),("clearance_at_centre",135,"Clearance at center: 135 feet")]},
 "manhattan":{"name":"Manhattan Bridge","values":[("lower_abutment_length",5790,"5,790 feet"),("upper_portal_length",6090,"6,090 feet"),("main_span",1470,"Main span: 1,470 feet")]},
 "williamsburg":{"name":"Williamsburg Bridge","values":[("total_length",7308,"Total length: 7,308 feet"),("main_span",1600,"Main span: 1,600 feet"),("clearance_at_centre",135,"Clearance at center: 135 feet"),("tower_height",310,"Height of towers: 310 feet")]},
 "queensboro":{"name":"Ed Koch Queensboro Bridge","values":[("length_without_approaches",3725,"Total length: 3,725 feet"),("length_with_approaches",7449,"Total length including the approaches: 7,449 feet")]},
 "verrazzano":{"name":"Verrazzano-Narrows Bridge","values":[("tower_height",693,"693 foot high towers"),("tower_distance_main_span",4260,"4,260 foot distance between them"),("reported_seasonal_deck_difference",12,"12 feet lower in the summer")]},
}


def main():
    items=[]
    for id,spec in FACTS.items():
        path=ROOT/f"data/raw/stage7/bridges/{id}.html"
        receipt=json.loads(path.with_name(path.name+".receipt.json").read_text())
        text=re.sub(r"\s+"," ",unescape(re.sub("<[^>]*>"," ",path.read_text())))
        values=[]
        for quantity,feet,quote in spec["values"]:
            if quote not in text:raise ValueError("Source quote absent: "+quote)
            values.append({"quantity":quantity,"source_value":feet,"source_unit":"international_foot",
                "value_m":feet*.3048,"status":"source_explicit","independently_verified":False,
                "source_quote":quote,"url":receipt["final_url"],"path":str(path.relative_to(ROOT)),
                "sha256":sha(path),"accuracy_m":None,"observation_date":None,
                "scope_note":"clearance/tower extent is NOT absolute deck elevation; reference water/tide datum not established"})
        dossier={"id":id,"name":spec["name"],"source_values":values,
            "width_m":None,"deck_absolute_elevation_m":None,"deck_vertical_datum":None,
            "tower_absolute_top_m":None,"approach_grade_profile":None,
            "bridgehead_survey_control":None,"physical_world_placement_allowed":False,
            "rendering":"official transport outline only; no unverified deck/tower/cable mesh",
            "same_city_scope":"selected main spans connect NYC boroughs; no NJ approach included as NYC coverage",
            "publication_date":None,"downloaded_at":receipt["download_completed_at"],
            "research_status":"partial_primary_facts","model_complete":False,
            "validation":{"horizontal_reference":"source transport outlines at observation windows",
                "vertical_continuity":False,"under_bridge_clearance":False,"width_verified":False},
            "missing":["dated deck survey and vertical datum","width","tower/base elevations","approach geometry and continuity","structural component dimensions"]}
        atomic_json(ROOT/f"bridges/{id}/dossier.json",dossier);items.append(dossier)
    atomic_json(ROOT/"assets/environment/bridges.json",{"at_utc":now(),"bridges":items,"count":5,
        "complete_bridge_models":0,"source_unit_basis":"ordinary engineering dimensions per retained NIST international-foot definition; GIS feet remain unresolved"})


if __name__=="__main__":
    main()
