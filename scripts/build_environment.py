"""Real source overlays, conflict candidates and conservative DEM inspection collision."""
import json
import math
import sqlite3
import subprocess
import argparse
from pathlib import Path
from collections import Counter
import numpy as np
from shapely import make_valid, force_2d, transform
from shapely.geometry import shape, mapping, box, Polygon, Point
from shapely.strtree import STRtree
from pyproj import Transformer
from nyc.download import ROOT, atomic_json, now, sha
from nyc.environment_mesh import glb
from nyc.coordinates import geographic_to_metric, metric_to_geographic

TO_METRIC=Transformer.from_crs(4326,32118,always_xy=True)
TO_GEO=Transformer.from_crs(32118,4326,always_xy=True)
TRANSPORT={2300:"bridge",2310:"tunnel_portal",2320:"rail_bridge",2330:"pedestrian_bridge",2340:"rail_viaduct",2350:"overpass"}
RAIL={2400:"rail_level_unknown_may_be_hidden",2410:"elevated_rail",2420:"embankment_rail",2430:"rail_viaduct",2440:"open_cut",2450:"rail_fence",2465:"abandoned"}
OUT=ROOT/"assets/environment"
REPAIRS=[]


def compact(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix(path.suffix+".tmp")
    temp.write_text(json.dumps(value,ensure_ascii=False,separators=(",",":")));temp.replace(path)


def catalog_sources():
    result={}
    for manifest in json.loads((ROOT/"data/manifests/stage7/vector-sources.json").read_text()):
        rows={}
        for page in manifest["pages"]:
            if sha(ROOT/page["path"])!=page["sha256"]:raise ValueError("raw source checksum changed")
            for r in json.loads((ROOT/page["path"]).read_text()):
                key=r["socrata_row_id"]
                if key in rows and rows[key]!=r:raise ValueError("source changed across overlapping query windows")
                rows[key]=r
        if len(rows)!=manifest["unique_rows"]:raise ValueError("row count mismatch")
        features=[]
        for key,r in rows.items():
            if manifest["name"]=="trees":
                x,y=float(r["longitude"]),float(r["latitude"]);g=Point(x,y)
            else:g=force_2d(shape(r[manifest["geometry_field"]]))
            if not g.is_valid:
                before=transform(g,TO_METRIC.transform,interleaved=False)
                fixed=make_valid(g);after=transform(fixed,TO_METRIC.transform,interleaved=False)
                REPAIRS.append({"source_dataset":manifest["dataset_id"],"row_id":key,"area_before_m2":before.area,"area_after_m2":after.area,"area_change_m2":after.area-before.area,"raw_manifest":manifest["metadata"],"stage":"before clipping"})
            g=make_valid(g)
            if g.is_empty:continue
            x,y,xx,yy=g.bounds
            if not(-74.35<x<=xx<-73.65 and 40.45<y<=yy<40.95):raise ValueError("unexpected source coordinate units/range")
            m=transform(g,TO_METRIC.transform,interleaved=False)
            code=int(float(r.get("feat_code")or 0));name=manifest["name"]
            kind=TRANSPORT.get(code,name)if name=="transport"else RAIL.get(code,name)if name=="rail"else name
            id=(f"nyc:trees2015:{r['tree_id']}"if name=="trees"else f"nyc:{name}:row:{key}")
            f={"id":id,"kind":kind,"code":code,"name":r.get("name")or r.get("signname")or r.get("spc_common"),
              "geometry_metric":mapping(m),"geometry":mapping(g),"properties":r,
              "source_period":"2015–2016 census"if name=="trees"else"source planimetric/parks, individual observation unknown",
              "source_dataset":manifest["dataset_id"],"vertical_state":"unknown; projection reference only",
              "canonical_height_m":None,"source_z_not_interpreted":True}
            if name=="rail":f["render_as_ground_track"]=False;f["possible_hidden_underground"]=code==2400
            features.append(f)
        result[manifest["name"]]=features
    return result


def local_context(region,layer,bounds):
    path=ROOT/f"data/intermediate/stage7/{region}-{layer}.json"
    if not path.exists():
        path.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run(["ogr2ogr","-f","GeoJSON",str(path),str(ROOT/"data/processed/context/context.gpkg"),
                        layer,"-spat",*map(str,bounds)],check=True,capture_output=True)
    data=json.loads(path.read_text());result=[];clip=box(*bounds)
    for f in data["features"]:
        original=shape(f["geometry"]);valid=make_valid(original)
        if not original.is_valid:REPAIRS.append({"source_layer":layer,"source_row_id":f["properties"]["socrata_row_id"],"area_before_m2":original.area,"area_after_m2":valid.area,"area_change_m2":valid.area-original.area,"raw_cache":str(path.relative_to(ROOT)),"stage":"before clipping"})
        g=valid.intersection(clip)
        if g.is_empty or g.area<1e-8:continue
        r=f["properties"];code=int(float(r.get("feat_code")or 0))
        result.append({"id":f"nyc:{layer}:row:{r['socrata_row_id']}","kind":layer,"name":r.get("name"),"code":code,
            "geometry_metric":mapping(g),"geometry":mapping(transform(g,TO_GEO.transform,interleaved=False)),
            "properties":r,"source_period":"retained official planimetric capture; individual date unknown",
            "canonical_height_m":None,"vertical_state":"unknown; reference only",
            "fill_allowed":code in [2620,2660]if layer=="water"else True})
    return result


def source_buildings(db,bounds):
    x,y,xx,yy=bounds;result=[]
    rows=db.execute("""SELECT b.payload FROM spatial r JOIN buildings b ON b.rowid=r.row_id
        WHERE r.minx<=? AND r.maxx>=? AND r.miny<=? AND r.maxy>=?
        AND b.capture LIKE '2026-10-27-city:%' ORDER BY b.id""",[xx,x,yy,y])
    clip=box(*bounds)
    for (text,)in rows:
        r=json.loads(text)
        if not r["placeholder"] and shape(r["geometry"]).intersects(clip):result.append(r)
    return result


def publish_layer(path,features,origin,colour,lift,fill=False):
    if not features:return {"state":"no-data","features":0}
    value=glb(features,origin,lift,colour,fill)
    if value is None:return {"state":"no-data","features":0}
    payload,frame,bounds=value;path.parent.mkdir(parents=True,exist_ok=True);path.with_suffix(".glb").write_bytes(payload)
    compact(path,{"asset":{"version":"1.1"},"geometricError":100,
        "root":{"transform":frame["enu_to_ecef_column_major"],"boundingVolume":{"box":bounds},"geometricError":100,
        "children":[{"boundingVolume":{"box":bounds},"geometricError":0,"content":{"uri":path.with_suffix(".glb").name}}]}})
    return {"state":"available","features":len(features),"tileset":str(path.relative_to(OUT)),
            "scope":"projection reference; no physical height"}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vectors-only',action='store_true',help='Publish vectors and park boundary input before acquiring park terrain')
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);sources=catalog_sources()
    spatial={k:STRtree([shape(f["geometry_metric"])for f in v])for k,v in sources.items()}
    def within(name,region):
        result=[]
        for index in spatial[name].query(region,predicate="intersects"):
            f=dict(sources[name][int(index)]);g=shape(f["geometry_metric"]).intersection(region)
            if g.is_empty:continue
            f["geometry_metric"]=mapping(g);f["geometry"]=mapping(transform(g,TO_GEO.transform,interleaved=False));result.append(f)
        return sorted(result,key=lambda f:f["id"])
    db=sqlite3.connect(f"file:{ROOT}/data/processed/city/buildings.sqlite?mode=ro",uri=True)
    points=json.loads((ROOT/"config/observation-points.json").read_text())["points"];summaries=[];conflicts=[];tree_conflicts=[];repairs=[]
    styles={"roads":([.48,.51,.53,1],.08,True),"sidewalk":([.66,.66,.60,1],.12,True),
       "median":([.50,.59,.46,1],.16,True),"water":([.27,.55,.65,1],0,True),
       "transport":([.65,.36,.20,1],.3,False),"piers":([.48,.36,.27,1],.2,False),
       "rail":([.69,.42,.25,1],.35,False),"rail-structure":([.57,.40,.65,1],.25,False),
       "parks":([.27,.47,.28,1],.2,False),"trees":([.18,.43,.29,1],.4,False),
       "outlines":([.68,.55,.27,1],.25,False)}
    for p in points:
        cx,cy=geographic_to_metric(p["lon"],p["lat"]);r=p["radius_m"];bounds=[cx-r,cy-r,cx+r,cy+r];region=box(*bounds)
        buildings=source_buildings(db,bounds)
        all_layers={name:within(name,region)for name in sources}
        all_layers["roads"]=local_context(p["id"],"roadbed",bounds)
        all_layers["water"]=local_context(p["id"],"water",bounds)
        all_layers["outlines"]=[{"id":b["id"],"kind":"source_outline","name":b["name"],
            "geometry_metric":b["geometry"],"geometry":b["geometry_wgs84"],"source_period":"observation unknown",
            "vertical_state":"base and relative height unresolved"}for b in buildings]
        # Hidden2400 includes tunnel copies without Z: retained in JSON, never drawn as ground rails.
        rendered={**all_layers,"rail":[f for f in all_layers["rail"]if not f["possible_hidden_underground"]]}
        layers={}
        for name,(colour,lift,fill)in styles.items():
            layers[name]=publish_layer(OUT/p["id"]/(name+".json"),rendered.get(name,[]),[cx,cy],colour,lift,fill)
        content={"preset":p,"bounds_metric_m":bounds,"layer_states":layers,
          "features":{k:[{kk:vv for kk,vv in f.items()if kk!="geometry_metric"}for f in fs]for k,fs in all_layers.items()},
          "global_terrain_registered":False,"reference_plane":"WGS84 ellipsoid0, small draw-order offsets NOT actual heights",
          "physical_road_bridge_surfaces":0,"lanes_or_random_furniture_generated":0}
        compact(OUT/p["id"]/"context.json",content);summaries.append({**p,"layers":layers,"context":p["id"]+"/context.json"})
        # Horizontal overlaps are candidates only: overhead roofs/overpasses and dates can differ.
        road_shapes=[shape(f["geometry_metric"])for f in all_layers["roads"]];road_tree=STRtree(road_shapes)
        water_shapes=[shape(f["geometry_metric"])for f in all_layers["water"]];water_tree=STRtree(water_shapes)
        building_shapes=[shape(b["geometry"])for b in buildings];building_tree=STRtree(building_shapes)
        for i,b in enumerate(buildings):
            for j in road_tree.query(building_shapes[i],predicate="intersects"):
                a=building_shapes[i].intersection(road_shapes[j]).area
                if a>.5:conflicts.append({"preset":p["id"],"building_id":b["id"],"road_id":all_layers["roads"][int(j)]["id"],"area_m2":a,"building_raw":b["raw_record"],"reason":"overhead outline vs2D road, dates/level need review; NOT proven physical collision","geometry_modified":False})
        for tree in all_layers["trees"]:
            q=shape(tree["geometry_metric"]);hits=[]
            if len(building_tree.query(q,predicate="intersects")):hits.append("building_overhead_projection")
            if len(road_tree.query(q,predicate="intersects")):hits.append("roadbed_projection")
            if len(water_tree.query(q,predicate="intersects")):hits.append("water_projection")
            if hits:tree_conflicts.append({"preset":p["id"],"tree_id":tree["id"],"hits":hits,"source_period":"2015–2016 vs newer layers","action":"retain dated point; no current3Dtree generated"})
        print("ENV",p["id"],len(buildings),"trees",len(all_layers["trees"]),flush=True)
    # Whole real park boundaries, not green boxes or assumed grass.
    parks=sources["parks"]
    centre=geographic_to_metric(-73.97,40.74)
    park_layer=publish_layer(OUT/"parks.json",parks,centre,[.25,.45,.26,1],.2,False)
    compact(OUT/"parks-source.json",{"features":[{k:v for k,v in f.items()if k!="geometry_metric"}for f in parks]})
    if args.vectors_only:return
    # Exact rendered DEM triangles + conservative exclusion columns, never highest-surface snapping.
    walks=[]
    for spec in json.loads((ROOT/"assets/environment/terrain-manifest.json").read_text())["datasets"]:
        scene=json.loads((ROOT/"assets/foundation"/spec["terrain"]).read_text());t=scene["terrain"]
        bounds=spec["bounds_metric_m"];origin=t["local_origin_projected_m"];region=box(*bounds)
        buildings=source_buildings(db,bounds);water=local_context("walk-"+spec["id"],"water",bounds);roads=local_context("walk-"+spec["id"],"roadbed",bounds)
        extra=within("transport",region)+within("rail-structure",region)
        obstacles=[shape(b["geometry"]).buffer(1)for b in buildings]
        obstacles.extend(shape(f["geometry_metric"]).buffer(1)for f in water+roads+extra)
        obstacle_tree=STRtree(obstacles);vertices=np.array(t["vertices"]).reshape((-1,3));allowed=[];best=None;distance=math.inf
        for offset in range(0,len(t["indices"]),3):
            indices=t["indices"][offset:offset+3];v=vertices[indices];normal=np.cross(v[1]-v[0],v[2]-v[0])
            slope=math.degrees(math.atan2(np.linalg.norm(normal[:2]),abs(normal[2])))
            if slope>25:continue
            tri=Polygon(v[:,:2]+np.array(origin))
            if not len(obstacle_tree.query(tri,predicate="intersects")):
                allowed.append(offset);mean=v.mean(axis=0)
                if float(mean[0]**2+mean[1]**2)<distance:distance=float(mean[0]**2+mean[1]**2);best=mean.tolist()
        collision={"schema_version":7,"id":spec["id"],"frame":"local EPSG32118, NAVD88 metre; NOT ECEF",
          "terrain":spec["terrain"],"terrain_source_sha256":sha(ROOT/"assets/foundation"/spec["terrain"]),
          "allowed_triangle_offsets":allowed,"spawn":best,"layer_id":"ground","eye_height_m":1.7,
          "speed_m_per_s":1.4,"step_safety_m":.2,"slope_limit_degrees":25,
          "max_world_step_m":.5,"safety_buffer_m":1,"buffer_is_not_measured_wall":True,
          "blocked_classes":["source building projection","all water","all roadbeds","transport incl portals/bridge under-space","rail structures"],
          "bridge_decks":[],"tunnel_interiors":[],"building_interiors":False,
          "collision_not_render_mesh":"same DEM triangles forground; conservative 2D exclusion columns around unknown structures",
          "current_real_world_walkability_verified":False}
        compact(OUT/"collision"/(spec["id"]+".json"),collision);walks.append({"id":spec["id"],"allowed_triangles":len(allowed),"available":best is not None,"collision":"collision/"+spec["id"]+".json"})
        print("WALK",spec["id"],len(allowed),flush=True)
    db.close()
    compact(OUT/"manifest.json",{"schema_version":7,"created_at_utc":now(),"observations":summaries,"parks":park_layer,
      "walks":walks,"global_vertical_registered":False,"physical_bridge_surfaces":0,
      "source_scope":"25 observed windows+6 retained DEM crops+2 full park bounding crops, not whole-city environment",
      "rail_2400_hidden_ambiguous_not_drawn":True,"trees":"dated2015–2016 point references, no invented canopies",
      "street_furniture":"only source transit entrance footprints; lamps/hydrants/benches not acquired",
      "dossiers":"bridges.json"})
    atomic_json(ROOT/"reports/stage7/road-building-conflicts.json",conflicts)
    atomic_json(ROOT/"reports/stage7/tree-conflicts.json",tree_conflicts)
    atomic_json(ROOT/"reports/stage7/geometry-repairs.json",REPAIRS)
    atomic_json(ROOT/"reports/stage7/coverage.json",{"observations":len(points),"park_records":len(parks),
      "source_unique_features":{k:len(v)for k,v in sources.items()},"road_building_overlap_candidates":len(conflicts),
      "tree_overlap_candidates":len(tree_conflicts),"walks":walks,
      "physical_road_surfaces_verified":0,"physical_bridge_decks_verified":0,"global_z_alignment_verified":False,
      "geometry_repairs":"make_valid derived; original raw retained; no building geometry modified",
      "cross_border_structures":"no NJ approach acquired as NYC coverage; selected five main bridges are NYC bridges, maritime jurisdiction not inferred from shore-clipped polygons"})


if __name__=="__main__":
    main()
