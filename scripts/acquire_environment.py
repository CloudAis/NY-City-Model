"""Official, bounded and restartable acquisition for static environment samples."""
import json
import math
from pathlib import Path
from urllib.parse import urlencode
from nyc.download import ROOT, Downloader, atomic_json, now, sha

SOURCES = {"transport":"r9cu-9r7b", "rail":"anc7-97cy", "rail-structure":"dwer-xbgx",
           "sidewalk":"52n9-sdep", "median":"ees7-4ufv", "piers":"6hbv-tek4",
           "parks":"enfh-gkve", "trees":"uvpi-gqnh"}


def windows():
    points=json.loads((ROOT/"config/observation-points.json").read_text())["points"]
    boxes=[]
    for p in points:
        dy=p["radius_m"]/111000;dx=dy/math.cos(math.radians(p["lat"]))
        boxes.append([p["lon"]-dx,p["lat"]-dy,p["lon"]+dx,p["lat"]+dy])
    from nyc.coordinates import metric_to_geographic
    for d in json.loads((ROOT/"assets/foundation/manifest.json").read_text())["datasets"]:
        x,y,xx,yy=d["bounds_metric_m"]
        a=metric_to_geographic(x,y);b=metric_to_geographic(xx,yy)
        boxes.append([a[0],a[1],b[0],b[1]])
    return boxes


def main():
    downloader=Downloader(timeout=45,retries=2,interval=.4,max_bytes=32*1024*1024)
    root=ROOT/"data/raw/stage7/vectors"
    batches=[windows()[i:i+4]for i in range(0,len(windows()),4)]
    report=[]
    for name,dataset in SOURCES.items():
        meta_path=downloader.get(f"https://data.cityofnewyork.us/api/views/{dataset}.json",
                                f"data/raw/stage7/catalog/{name}-dataset.json")
        meta=json.loads(meta_path.read_text())
        fields={c["fieldName"]:c.get("dataTypeName")for c in meta["columns"]if not c["fieldName"].startswith(":")}
        geometry=next((k for k,v in fields.items()if v in ["multipolygon","polygon","line","multiline","point"]),"")
        if not geometry and name!="trees":raise ValueError("Actual geometry column absent: "+name)
        region_batches=[None]if name=="parks"else batches
        ids=set();pages=[];start=now();counts=[]
        for batch,boxes in enumerate(region_batches):
            if name=="parks":
                where="upper(signname) in ('CENTRAL PARK','PROSPECT PARK')"
            elif name=="trees":
                where=" OR ".join(f"(longitude between {w:.7f} and {e:.7f} AND latitude between {s:.7f} and {n:.7f})"for w,s,e,n in boxes)
            else:
                where=" OR ".join(f"intersects({geometry}, 'POLYGON (({w:.7f} {s:.7f},{e:.7f} {s:.7f},{e:.7f} {n:.7f},{w:.7f} {n:.7f},{w:.7f} {s:.7f}))')"for w,s,e,n in boxes)
            base=f"https://data.cityofnewyork.us/resource/{dataset}.json?"
            count_url=base+urlencode({"$select":"count(*)","$where":where})
            count_path=downloader.get(count_url,root/name/f"count-{batch:02}.json")
            count=int(json.loads(count_path.read_text())[0]["count"])
            if count>40000:raise ValueError("Subset budget exceeded: "+name)
            counts.append(count);keys=[];got=0
            for offset in range(0,count,500):
                params={"$where":where,"$select":":id as socrata_row_id,"+",".join(fields),
                        "$order":":id ASC","$limit":500,"$offset":offset}
                path=downloader.get(base+urlencode(params),root/name/f"batch-{batch:02}-{offset:06}.json")
                rows=json.loads(path.read_text())
                if not isinstance(rows,list):raise ValueError("Not a Socrata row array")
                page_ids=[r["socrata_row_id"]for r in rows]
                keys.extend(page_ids);ids.update(page_ids);got+=len(rows)
                pages.append({"path":str(path.relative_to(ROOT)),"sha256":sha(path),
                              "batch":batch,"records":len(rows)})
            if got!=count or len(set(keys))!=count:raise ValueError("Incomplete stable row-ID pagination: "+name)
            print("SOURCE_BATCH",name,batch,count,flush=True)
        end_path=downloader.get(f"https://data.cityofnewyork.us/api/views/{dataset}.json",
                               root/name/"metadata-end.json",refresh=True)
        end=json.loads(end_path.read_text())
        if end.get("rowsUpdatedAt")!=meta.get("rowsUpdatedAt"):
            raise ValueError("Dynamic dataset changed: retain raw, acquire a new snapshot instead")
        manifest={"name":name,"dataset_id":dataset,"metadata":str(meta_path.relative_to(ROOT)),
            "geometry_field":geometry or None,"fields":fields,"pages":pages,"unique_rows":len(ids),
            "batch_counts":counts,"capture_started_at":start,"capture_finished_at":now(),
            "rows_updated_at":meta.get("rowsUpdatedAt"),"page_updated_at":meta.get("viewLastModified"),
            "observation_period":"2015–2016 census"if name=="trees"else None,
            "source_dates":"planimetric feature acquisition dates in captured rules; not inferred from download",
            "coordinate_contract":"Socrata geometry longitude,latitude degrees; ignore any unverified Z",
            "consistency":"stable row-ID pages, counts per overlapping batch and end metadata; not a transactional snapshot",
            "scope":"25 observation windows plus6 existing DEM extents; parks selected by actual signname",
            "licence":"NYC Open Data Terms; source metadata retained","citywide_complete":False}
        atomic_json(root/name/"manifest.json",manifest);report.append(manifest)
        print("SOURCE_DONE",name,len(ids),flush=True)
    atomic_json(ROOT/"data/manifests/stage7/vector-sources.json",report)


if __name__=="__main__":
    main()
