"""Build local orthometric terrain and source-clipped context without unresolved ECEF heights."""
import json,math,subprocess,os
from pathlib import Path
from collections import defaultdict
import numpy as np
from shapely.geometry import shape,mapping,box,Polygon,MultiPolygon
from shapely import make_valid,constrained_delaunay_triangles,transform
from pyproj import Transformer
from nyc.download import ROOT,atomic_json,sha,now
from nyc.coordinates import LocalFrame,metric_to_geographic
from nyc.terrain import BareEarthRaster
from nyc.elevations import building_register
from nyc.diagnostic_gltf import axes_glb,DIRECTIONS
from check_registration import source_feature

TO_GEO=Transformer.from_crs(32118,4326,always_xy=True)
WATER_TYPES={2600:'lake/reservoir',2610:'pond',2620:'river',2630:'stream',2640:'wetland/marsh',2650:'beach/shoreline',2660:'bay/ocean'}
def compact(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')));os.replace(temp,path)

def clip_context(id,layer,bounds):
 path=ROOT/f'data/intermediate/stage3/context/{id}-{layer}.geojson';path.parent.mkdir(parents=True,exist_ok=True)
 if not path.exists():subprocess.run(['ogr2ogr','-f','GeoJSON',str(path),str(ROOT/'data/processed/context/context.gpkg'),layer,'-spat',*map(str,bounds),'-t_srs','EPSG:32118'],check=True,capture_output=True)
 data=json.loads(path.read_text());features=[];repair_log=[];clip=box(*bounds)
 for f in data['features']:
  original=shape(f['geometry']);valid=make_valid(original);g=valid.intersection(clip)
  if g.is_empty:continue
  polys=list(g.geoms)if g.geom_type in ['MultiPolygon','GeometryCollection']else[g];polys=[p for p in polys if isinstance(p,Polygon)and p.area>1e-8]
  if not polys:continue
  g=MultiPolygon(polys)if len(polys)>1 else polys[0];props=f['properties'];sid=str(props.get('socrata_row_id')or f['id']);code=int(props['feat_code'])
  record={'id':f'nyc:{layer}:row:{sid}','source_row_id':sid,'properties':props,'geometry_metric':mapping(g),'geometry':mapping(transform(g,TO_GEO.transform,interleaved=False)),'crs':'EPSG:4326','source_crs':'EPSG:32118','scope':'source-clipped sample only','world_height':'reference ellipsoid h=0, not terrain/bridge/water observation'}
  if layer=='water':record.update({'surface_type':WATER_TYPES.get(code,'unknown'),'fill_allowed':code in [2620,2660],'display_water_level_m':0 if code in [2620,2660]else None,'display_water_datum':'NAVD88 in orthometric inspector; WGS84 ellipsoid reference in globe; separate scenes, no vertical conversion implied','water_level_status':'chosen display level, NOT measured tide'if code in [2620,2660]else'unknown; boundary only','not_water_surface':code in [2640,2650]})
  else:record.update({'elevation':None,'deck_height':None,'z_status':'unknown; reference linework only; never draped to DEM','bridge_clearance_preserved_by':'No transport surface/body is generated without bridge-deck evidence.'})
  if not original.is_valid:repair_log.append({'id':record['id'],'source_valid':False,'source_area_m2':original.area,'repaired_area_m2':valid.area,'source_cache':str(path.relative_to(ROOT))})
  features.append(record)
 return features,repair_log

def main():
 manifest=json.loads((ROOT/'data/manifests/stage3/dem-samples.json').read_text());out=ROOT/'data/processed/foundation';assets=ROOT/'assets/foundation';out.mkdir(parents=True,exist_ok=True);assets.mkdir(parents=True,exist_ok=True);datasets=[];register=[];reports=[]
 policy=json.loads((ROOT/'data/manifests/stage3/height-policy.json').read_text());compact(out/'height-policy.json',policy);compact(assets/'height-policy.json',policy)
 for spec in manifest:
  id=spec['id'];meta=ROOT/f'data/intermediate/stage3/dem/{id}.json';raster=BareEarthRaster(meta,spec);lod=raster.lod(4);cx,cy=lod['local_origin_projected_m'];h,w=raster.values.shape
  x1,y1=raster.coordinate(0,0);x2,y2=raster.coordinate(h-1,w-1);bounds=[min(x1,x2),min(y1,y2),max(x1,x2),max(y1,y2)];water,wrep=clip_context(id,'water',bounds);roads,rrep=clip_context(id,'roadbed',bounds)
  scene_water=[];water_quality=[]
  for f in water:
   if not f['fill_allowed']:continue
   g=shape(f['geometry_metric']);tris=constrained_delaunay_triangles(g);area=0;vertices=[]
   for tri in tris.geoms:
    area+=tri.area
    for x,y in list(tri.exterior.coords)[:3]:vertices.extend([x-cx,y-cy,0])
   delta=abs(area-g.area)
   if delta>max(1e-5,g.area*1e-9):raise ValueError('water triangulation crosses holes or loses coverage')
   scene_water.append({'source_id':f['id'],'vertices':vertices,'level_m':0,'datum':'NAVD88','level_is_display_only':True});water_quality.append({'source_id':f['id'],'source_clipped_area_m2':g.area,'triangle_area_m2':area,'area_difference_m2':delta,'interior_rings_preserved':sum(len(p.interiors)for p in(g.geoms if isinstance(g,MultiPolygon)else[g]))})
  records=[json.loads(s)for s in(ROOT/f'data/processed/{id}/buildings.jsonl').read_text().splitlines()];footprints=[]
  for r in records:
   _,f=source_feature(r);entry=building_register(r,f['attributes']);register.append(entry)
   if r['placeholder']:continue
   lines=[];samples=[]
   polygons=[shape(r['geometry'])]if r['geometry']['type']=='Polygon'else list(shape(r['geometry']).geoms)
   for p in polygons:
    for ring in [p.exterior,*p.interiors]:
     pts=list(ring.coords)
     for a,b in zip(pts,pts[1:]):
      count=max(1,math.ceil(math.dist(a,b)/15))
      for i in range(count):
       start=[a[k]+(b[k]-a[k])*i/count for k in range(2)];end=[a[k]+(b[k]-a[k])*(i+1)/count for k in range(2)];za=raster.sample(*start);zb=raster.sample(*end)
       if za is None or zb is None:continue
       lines.extend([start[0]-cx,start[1]-cy,za+.08,end[0]-cx,end[1]-cy,zb+.08]);samples.extend([za,zb])
   if samples:
    entry['dem_ground_reference']={'quantity':'derived_ground_samples','unit':'metre','datum':'NAVD88','source_capture_period':['2017-05-03','2017-07-26'],'source_raster':spec.get('masked_raster',spec['raster']),'minimum_m':min(samples),'maximum_m':max(samples),'span_m':max(samples)-min(samples),'not_measured_building_base':True,'body_deformation_applied':False,'scope':'DEM sampled along projected roof outline; not evidence of actual foundation contact'}
   footprints.append({'id':r['id'],'lines':lines})
  ground=[]
  for row in range(0,h,32):
   for col in range(0,w,32):
    z=float(raster.values[row,col])
    if not math.isfinite(z):continue
    x,y=raster.coordinate(row,col);lon,lat=metric_to_geographic(x,y);ground.append({'id':f'{id}:dem:{row}:{col}','source_row':row,'source_column':col,'projected_m':[x,y],'local_m':[x-cx,y-cy,z],'longitude_latitude_deg':[lon,lat],'height_m':z,'datum':'NAVD88','source_raster':spec.get('masked_raster',spec['raster']),'ecef_height_m':None})
  # Four tiles share one exact source grid, including common boundaries. No skirts or zero-filled seams.
  shared=lod['tile_seam_max_m']
  payload={'schema_version':1,'id':id,'scene_kind':'local_projected_orthometric_inspector','world_placement_allowed':False,'datum_issue':'generic NAD83 service vs NAD83(2011) index; no silent frame assignment','terrain':lod,'water':scene_water,'water_source_features':water,'roads':roads,'footprints':footprints,'ground_samples':ground,'source':spec,'full_city_coverage':False,'vertical_exaggeration':1}
  compact(out/f'{id}.json',payload)
  published={k:v for k,v in payload.items()if k not in ['roads','water_source_features']};published['context_reference']=f'{id}-overlays.json';published['road_height_status']='No deck elevation; no road surfaces generated'
  compact(assets/f'{id}.json',published)
  # Globe overlays use declared reference heights only, never the unconverted NAVD88 heights.
  ref=LocalFrame.at(*metric_to_geographic(cx,cy),0);tiledata=json.loads((ROOT/f'assets/{id}/tileset.json').read_text());grids=[]
  for x in range(math.ceil(bounds[0]/100)*100,math.floor(bounds[2]/100)*100+1,100):grids.append([[*metric_to_geographic(x,bounds[1])],[*metric_to_geographic(x,bounds[3])]])
  for y in range(math.ceil(bounds[1]/100)*100,math.floor(bounds[3]/100)*100+1,100):grids.append([[*metric_to_geographic(bounds[0],y)],[*metric_to_geographic(bounds[2],y)]])
  overlay={'id':id,'water':water,'roads':roads,'ground_samples':ground,'grid_lines_longitude_latitude_deg':grids,'grid_spacing_projected_m':100,'local_reference_frame':ref.manifest(),'tiles':[{'transform_enu_to_ecef':c['transform'],'box_local_enu_m':c['boundingVolume']['box'],'content':c['content']['uri']}for c in tiledata['root']['children']],'tile_axis_contract':'one glTF Y-up to Z-up engine rotation, then ENU -> ECEF'}
  overlay['roads']=[{k:v for k,v in f.items()if k!='geometry_metric'}for f in roads];overlay['water']=[{k:v for k,v in f.items()if k!='geometry_metric'}for f in water]
  compact(assets/f'{id}-overlays.json',overlay)
  reports.append({'id':id,'dem':raster.metadata,'source_capture':'2017; not download date','lod_triangles':len(lod['indices'])//3,'lod_missing_vertices':sum(v is None for v in lod['heights']),'valid_cells':raster.metadata['valid_cells'],'resolution_output_m':lod['source_resolution_m'],'water_triangulation':water_quality,'geometry_repairs':wrep+rrep,'water_filled_features':len(scene_water),'wetland_and_beach_never_filled_as_water':True,'road_z_unresolved':len(roads),'published_tile_seam_max_m':shared,'shared_boundary_comparisons':lod['tile_shared_boundary_comparisons'],'source_overlapping_crops_not_stitched':True,'ecef_terrain_publication':'blocked by unresolved source realization; local NAVD88 preview is available'})
  datasets.append({'id':id,'terrain':f'{id}.json','overlays':f'{id}-overlays.json','bounds_metric_m':bounds,'valid_dem_samples':raster.metadata['valid_cells'],'height_range_navd88_m':[raster.metadata['minimum_valid'],raster.metadata['maximum_valid']]});print('FOUNDATION',id,'roads',len(roads),'water',len(water),'triangles',len(lod['indices'])//3,flush=True)
 compact(out/'building-elevations.json',register);compact(assets/'building-elevations.json',register)
 axes=axes_glb();(assets/'axes-diagnostic.glb').write_bytes(axes);f=LocalFrame.at(-74.011,40.708,200)
 atomic_json(assets/'axes-diagnostic.json',{'asset':{'version':'1.1'},'geometricError':100,'root':{'boundingVolume':{'box':[0,0,0,110,0,0,0,110,0,0,0,110]},'geometricError':100,'transform':f.matrix_enu_to_ecef,'content':{'uri':'axes-diagnostic.glb'}}})
 atomic_json(assets/'manifest.json',{'schema_version':1,'generated_at':now(),'datasets':datasets,'height_contract':'NAVD88 metre terrain is separate from WGS84 ellipsoid world. No fixed city offset.','dem_source':'NYC 2017 / NYS public ImageServer; cached offline crops','global_terrain_registered':False,'global_terrain_block':'source horizontal realization conflict','ground_source_not_dsm':True,'geoid_grid_local':'data/raw/stage3/geoid/us_noaa_g2012bu0.tif','geoid_applied_to_dem':False,'axes':{'tileset':'axes-diagnostic.json','frame':f.manifest(),'endpoints_enu_m':DIRECTIONS,'diagnostic_only':True,'default_visible':False}})
 atomic_json(ROOT/'reports/stage3/terrain-quality.json',{'at':now(),'datasets':reports,'building_height_register_count':len(register),'canonical_unknown_foot_heights':sum(r['building_relative']['unit_status']=='unresolved'for r in register),'no_zero_filled_exterior':True,'geoid_grid_available':(ROOT/'data/raw/stage3/geoid/us_noaa_g2012bu0.tif').is_file(),'vertical_registration_unresolved':True})

if __name__=='__main__':main()
