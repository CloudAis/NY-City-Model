"""Reproduce a real retained-water polygon hole test; never fabricate an island polygon."""
import json,subprocess
from nyc.download import ROOT,atomic_json
from shapely.geometry import shape,box,mapping
from shapely import constrained_delaunay_triangles

subprocess.run(['/usr/bin/python3',str(ROOT/'scripts/gdal_water_hole.py')],check=True)
s=json.loads((ROOT/'data/intermediate/stage3/coastline-proof-source.json').read_text());g=shape(s['source_feature']['geometry']);hole=shape(s['hole_geometry']);clipped=g.intersection(box(*hole.buffer(100).bounds));tris=constrained_delaunay_triangles(clipped);area=sum(t.area for t in tris.geoms);overlap=sum(t.intersection(hole).area for t in tris.geoms)
if overlap>1e-6 or abs(area-clipped.area)>max(1e-5,clipped.area*1e-9):raise ValueError('water triangulation fills source land holes or loses source coverage')
atomic_json(ROOT/'data/processed/foundation/shoreline-hole-proof.json',{'source':{k:v for k,v in s.items()if k not in ['source_feature','hole_geometry']},'source_properties':s['source_feature']['properties'],'clipped_water_geometry_metric':mapping(clipped),'real_source_hole_geometry_metric':mapping(hole),'water_triangles':len(tris.geoms),'water_area_m2':clipped.area,'triangle_area_m2':area,'water_over_source_hole_m2':overlap,'physical_landmark_name':'not independently identified; source waterbody name is retained'})
print('REAL_SOURCE_HOLE_AREA',hole.area,'TRIANGLES',len(tris.geoms),'WATER_OVER_HOLE',overlap)
