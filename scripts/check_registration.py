"""Real source-correspondence points, numerical errors, geodesic distance and tangent-plane limits.

These are NOT field-survey control points. Reality errors are explicitly unmeasured.
"""
import json,sqlite3,math,struct,hashlib,csv
from pathlib import Path
from functools import lru_cache
from pyproj import Transformer
from shapely.geometry import shape,Point,LineString
from nyc.download import ROOT,atomic_json,sha,now
from nyc.coordinates import LocalFrame,metric_to_geographic,geographic_to_ecef,geodesic_distance,enu_to_gltf,gltf_to_enu,GEODESIC

@lru_cache(maxsize=36)
def raw_page(path):return json.loads((ROOT/path).read_text())

def source_feature(record):
 page=raw_page(record['raw_record']['path'])
 f=next(f for f in page['features']if f['attributes']['OBJECTID']==record['source_object_id'])
 if str(f['attributes']['DOITT_ID'])!=record['source_id']:raise ValueError('source identity mismatch')
 return page,f

def main():
 db=sqlite3.connect(f'file:{ROOT}/data/processed/city/buildings.sqlite?mode=ro',uri=True)
 bounds=json.loads((ROOT/'reports/city-dimensions.json').read_text())['boroughs'];points=[];chosen=set()
 for row in bounds:
  borough=row['borough'];w,s,e,n=row['bounds_32118_index']
  for fx,fy in [(.2,.2),(.5,.2),(.8,.5),(.8,.8),(.5,.8),(.2,.5)]:
   tx,ty=w+(e-w)*fx,s+(n-s)*fy;best=None
   for radius in [1000,2500,5000,15000]:
    candidates=db.execute('SELECT b.payload FROM spatial r JOIN buildings b ON b.rowid=r.row_id WHERE b.borough=? AND b.capture=? AND r.minx<=? AND r.maxx>=? AND r.miny<=? AND r.maxy>=? ORDER BY ((r.minx+r.maxx)/2-?)*((r.minx+r.maxx)/2-?)+((r.miny+r.maxy)/2-?)*((r.miny+r.maxy)/2-?) LIMIT 80',(borough,'2026-10-27-city:'+borough,tx+radius,tx-radius,ty+radius,ty-radius,tx,tx,ty,ty))
    for (text,)in candidates:
     r=json.loads(text)
     if r['id']in chosen or r['placeholder']or r['repair']:continue
     p=shape(r['geometry']).representative_point();distance=(p.x-tx)**2+(p.y-ty)**2
     if best is None or distance<best[0]:best=(distance,r)
    if best:break
   if best is None:continue
   r=best[1];page,f=source_feature(r);wkid=page['spatialReference'].get('latestWkid',page['spatialReference']['wkid']);wkid={102100:3857,102718:2263}.get(wkid,wkid)
   source_xy=f['geometry']['rings'][0][0];to_metric=Transformer.from_crs(wkid,32118,always_xy=True);back=Transformer.from_crs(32118,wkid,always_xy=True)
   x,y=to_metric.transform(*source_xy,errcheck=True);restored=back.transform(x,y,errcheck=True);lon,lat=metric_to_geographic(x,y)
   frame=LocalFrame.at(*metric_to_geographic((math.floor(x/500)+.5)*500,(math.floor(y/500)+.5)*500),0)
   world=geographic_to_ecef(lon,lat,0);enu=frame.to_local(world);gpu=struct.unpack('<3f',struct.pack('<3f',*enu_to_gltf(*enu)));world_back=frame.to_ecef(gltf_to_enu(*gpu))
   source_deviation=shape(r['geometry']).boundary.distance(Point(x,y));id=f'NYC-SOURCE-{len(points)+1:02d}';chosen.add(r['id'])
   points.append({'id':id,'role':'source-correspondence; NOT an independent surveyed control point','borough':borough,'building_id':r['id'],'bin':r['bin'],'source_object_id':r['source_object_id'],'source_record':r['raw_record'],'source_coordinate_reference':{'crs':f'EPSG:{wkid}','axis_order':'easting,northing','units':'metre'},'source_xy':source_xy,'vertex_locator':{'ring':0,'vertex':0},'normalized_projected_m':[x,y],'longitude_latitude_deg':[lon,lat],'source_to_metric_operation':{'description':to_metric.description,'definition':to_metric.definition,'nominal_accuracy_m':to_metric.accuracy},'coordinate_roundtrip_m':math.dist(source_xy,restored),'pipeline_gpu_reconstruction_error_m':math.dist(world,world_back),'relative_source_geometry_deviation_m':source_deviation,'relative_reality_measurement_error_m':None,'reality_measurement_note':'No independent ground survey or dated independent matching image/control observation available','frame':frame.manifest()})
 if len(points)<30:print('ACTUAL_CORRESPONDENCE_POINTS',len(points),'target 30; not fabricated',flush=True)
 target=.10
 if any(max(p['coordinate_roundtrip_m'],p['pipeline_gpu_reconstruction_error_m'],p['relative_source_geometry_deviation_m'])>target for p in points):raise ValueError('numerical pipeline target exceeded')
 # Use real source endpoints. Distances are geodesic; projected, Mercator and one-plane results are comparisons only.
 def pair(label,a,b):
  lonlat1=a['longitude_latitude_deg'];lonlat2=b['longitude_latitude_deg'];geodesic=geodesic_distance(lonlat1,lonlat2)
  wm=Transformer.from_crs(4326,3857,always_xy=True);mercator=math.dist(wm.transform(*lonlat1),wm.transform(*lonlat2))
  projected=math.dist(a['normalized_projected_m'],b['normalized_projected_m']);frame=LocalFrame.at(*lonlat1,0);local=frame.to_local(geographic_to_ecef(*lonlat2,0))
  return {'name':label,'from':a['id'],'to':b['id'],'from_building':a['building_id'],'to_building':b['building_id'],'from_longitude_latitude_deg':lonlat1,'to_longitude_latitude_deg':lonlat2,'geodesic_m':geodesic,'projected_32118_m':projected,'projected_minus_geodesic_m':projected-geodesic,'mercator_m':mercator,'mercator_relative_error':mercator/geodesic-1,'one_origin_tangent_horizontal_m':math.hypot(*local[:2]),'curvature_below_tangent_plane_m':local[2],'observed_real_distance_m':None}
 by_boro={b:[p for p in points if p['borough']==b]for b in ['manhattan','bronx','brooklyn','queens','staten-island']}
 distances=[pair('跨河量级：曼哈顿—布鲁克林实际来源角点',by_boro['manhattan'][0],by_boro['brooklyn'][0]),pair('跨区：布朗克斯—史泰登岛实际来源角点',by_boro['bronx'][-1],by_boro['staten-island'][0])]
 # Find a real street-block-scale pair among lower-Manhattan source corners, not invented intersections.
 pilot=[json.loads(s)for s in(ROOT/'data/processed/lower-manhattan/buildings.jsonl').read_text().splitlines()]
 a=pilot[0];pa,fa=source_feature(a);tx=Transformer.from_crs(3857,4326,always_xy=True);ll=tx.transform(*fa['geometry']['rings'][0][0]);near=[]
 for r in pilot[1:]:
  xy=shape(r['geometry']).exterior.coords[0]if shape(r['geometry']).geom_type=='Polygon'else list(shape(r['geometry']).geoms)[0].exterior.coords[0];geo=metric_to_geographic(*xy);d=geodesic_distance(ll,geo)
  if 80<d<250:near.append((abs(d-150),r,geo,xy))
 if near:
  _,r,geo,xy=min(near,key=lambda x:x[0]);aa={'id':'BLOCK-A','building_id':a['id'],'longitude_latitude_deg':ll,'normalized_projected_m':shape(a['geometry']).exterior.coords[0]};bb={'id':'BLOCK-B','building_id':r['id'],'longitude_latitude_deg':geo,'normalized_projected_m':xy};distances.insert(0,pair('街区量级：下城两真实建筑角点；非测量街道中心线',aa,bb))
 dumbo=json.loads((ROOT/'data/processed/brooklyn-dumbo/buildings.jsonl').read_text().splitlines()[0]);xy=list(shape(dumbo['geometry']).exterior.coords[0]);geo=metric_to_geographic(*xy);river_a={'id':'RIVER-A','building_id':a['id'],'longitude_latitude_deg':ll,'normalized_projected_m':shape(a['geometry']).exterior.coords[0]};river_b={'id':'RIVER-B','building_id':dumbo['id'],'longitude_latitude_deg':geo,'normalized_projected_m':xy};river=pair('跨东河：下城—DUMBO真实建筑角点',river_a,river_b)
 context=ROOT/'data/intermediate/stage3/context/lower-manhattan-water.geojson'
 if context.exists():
  line=LineString([river_a['normalized_projected_m'],river_b['normalized_projected_m']]);crossed=[f['properties']for f in json.loads(context.read_text())['features']if str(f['properties']['feat_code'])in ['2620','2660']and line.intersects(shape(f['geometry']))];river['intersected_real_water_sources']=crossed
  if not crossed:raise ValueError('cross-river distance example does not intersect retained source water')
 distances[1]=river
 # Exact geodesic ruler construction verifies unit conversions, not NYC survey accuracy.
 ruler=[]
 for metres in [1,10,100,1000,10000,50000]:
  end=GEODESIC.fwd(-74,40.75,90,metres)[:2];ruler.append({'requested_m':metres,'calculated_m':geodesic_distance([-74,40.75],end)})
 origin=LocalFrame.at(-74,40.75,0);local=[origin.to_local(geographic_to_ecef(*p['longitude_latitude_deg'],0))for p in points]
 report={'schema_version':1,'at':now(),'checkpoints':points,'source_correspondence_points':len(points),'borough_counts':{k:len(v)for k,v in by_boro.items()},'independently_surveyed_control_points':0,'reality_accuracy_status':'unmeasured; no 0.10m real-world claim','numeric_target_m':target,'maximum_roundtrip_m':max(p['coordinate_roundtrip_m']for p in points),'maximum_gpu_pipeline_m':max(p['pipeline_gpu_reconstruction_error_m']for p in points),'maximum_relative_source_geometry_m':max(p['relative_source_geometry_deviation_m']for p in points),'numeric_target_passed':True,'datum_transformation_uncertainty':'NAD83 to WGS84 operation accuracy is separately declared, not included in numerical residuals','distances':distances,'metric_rulers':ruler,'single_city_tangent_plane_assessment':{'origin':origin.manifest(),'min_up_m':min(v[2]for v in local),'max_up_m':max(v[2]for v in local),'decision':'No common flat city plane; ECEF world and individual local tiles retain curvature','extent_note':'Evaluated at these 30 real source positions; not an exhaustive surface accuracy proof'}}
 atomic_json(ROOT/'reports/stage3/registration.json',report);atomic_json(ROOT/'data/processed/foundation/checkpoints.json',points)
 with(ROOT/'data/processed/foundation/checkpoints.csv').open('w',newline='')as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(['id','borough','building_id','source_path','source_object_id','ring','vertex','source_x','source_y','easting_m','northing_m','longitude_deg','latitude_deg','roundtrip_m','gpu_pipeline_m','relative_source_m','reality_error_m','role'])
  for p in points:w.writerow([p['id'],p['borough'],p['building_id'],p['source_record']['path'],p['source_object_id'],0,0,*p['source_xy'],*p['normalized_projected_m'],*p['longitude_latitude_deg'],p['coordinate_roundtrip_m'],p['pipeline_gpu_reconstruction_error_m'],p['relative_source_geometry_deviation_m'],'','source-correspondence, not surveyed control'])
 print('SOURCE_POINTS',len(points),'INDEPENDENT_SURVEYS',0,'MAX_GPU_M',report['maximum_gpu_pipeline_m'],flush=True)

if __name__=='__main__':main()
