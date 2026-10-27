from pathlib import Path
import json,math,datetime,hashlib
from collections import Counter
from shapely.geometry import Polygon,MultiPolygon,GeometryCollection,mapping
from shapely import make_valid,union_all
from shapely import transform as vector_transform
def transform(fn,g):return vector_transform(g,fn,interleaved=False)
from pyproj import Transformer,CRS
from .download import ROOT,atomic_json,sha
from . import PIPELINE_VERSION
FT=.3048
BOROUGHS={'1':'manhattan','2':'bronx','3':'brooklyn','4':'queens','5':'staten-island'}
def clean_ring(ring):
 out=[]
 for p in ring:
  q=(float(p[0]),float(p[1]))
  if not all(math.isfinite(n)for n in q):raise ValueError('non-finite coordinate')
  if not out or out[-1]!=q:out.append(q)
 if len(out)>1 and out[0]==out[-1]:out.pop()
 if len(set(out))<3:raise ValueError('ring has fewer than 3 distinct points')
 return out+[out[0]]
def polygonal(g):
 if isinstance(g,(Polygon,MultiPolygon)):return g
 p=[x for x in getattr(g,'geoms',[])if isinstance(x,(Polygon,MultiPolygon))]
 return union_all(p)if p else Polygon()
def esri_polygon(rings):
 clean=[clean_ring(r)for r in rings];polys=[Polygon(r)for r in clean]
 depths=[sum(1 for j,q in enumerate(polys)if j!=i and abs(q.area)>abs(p.area)and make_valid(q).covers(p.representative_point()))for i,p in enumerate(polys)]
 pieces=[]
 for i,p in enumerate(polys):
  if depths[i]%2:continue
  holes=[clean[j]for j,q in enumerate(polys)if depths[j]==depths[i]+1 and make_valid(p).covers(q.representative_point())]
  pieces.append(Polygon(clean[i],holes))
 original=MultiPolygon(pieces)if len(pieces)>1 else pieces[0]
 valid=polygonal(make_valid(original))
 if valid.is_empty:raise ValueError('repair produced no polygonal geometry')
 return original,valid,sum(len(r)for r in rings)-sum(len(r)for r in clean)
def numeric(value,kind):
 if value is None:return None,'null'
 if isinstance(value,bool):return None,'not_numeric'
 try:v=float(value)
 except (ValueError,TypeError):return None,'not_numeric'
 if not math.isfinite(v):return None,'non_finite'
 if kind=='height'and v==0:return None,'unknown_zero'
 if kind=='height'and(v<0 or v>4000):return None,'anomalous_range'
 if kind=='year'and(v==0 or not 1600<=v<=datetime.datetime.now().year+2):return None,'unknown_or_anomalous_year'
 return v,'valid'
def evidence(field,value,status='source_explicit',note=None):return {'source':'nyc-building-footprints','field':field,'value':value,'status':status if value is not None else'unknown','independently_verified':False,'observation_date':None,'note':note}
def normalize(manifest_path,output):
 manifest=json.loads(Path(manifest_path).read_text());records=[];failures=[];repairs=[];conflicts=[]
 for page in manifest['pages']:
  path=ROOT/page['path']
  if sha(path)!=page['sha256']:raise ValueError('raw page checksum mismatch')
  obj=json.loads(path.read_text());sr=obj.get('spatialReference',manifest['raw_spatial_reference']);wkid=sr.get('latestWkid',sr.get('wkid'));wkid={102100:3857,102718:2263}.get(wkid,wkid)
  tm=Transformer.from_crs(wkid,32118,always_xy=True);tw=Transformer.from_crs(32118,4326,always_xy=True)
  for f in obj['features']:
   a=f['attributes'];oid=a['OBJECTID'];sid=a.get('DOITT_ID');stable=sid is not None
   id=f'nyc:footprints:doitt:{sid}'if stable else f'nyc:footprints:{manifest["version"]}:object:{oid}'
   try:
    before,after,removed=esri_polygon(f['geometry']['rings']);bm=transform(tm.transform,before);gm=transform(tm.transform,after);gm=polygonal(make_valid(gm))
    if gm.is_empty or not gm.is_valid:raise ValueError('invalid standardized geometry')
    parts=list(gm.geoms)if isinstance(gm,MultiPolygon)else[gm];parts.sort(key=lambda p:(p.bounds,p.area))
    h,hs=numeric(a.get('HEIGHT_ROOF'),'height');ground,gs=numeric(a.get('GROUND_ELEVATION'),'ground');year,ys=numeric(a.get('CONSTRUCTION_YEAR'),'year');bbl=str(a['BASE_BBL'])if a.get('BASE_BBL')else None;bin=str(a['BIN'])if a.get('BIN')else None
    if bin and bin.endswith('000000'):bin_status='placeholder'
    else:bin_status='valid_format'if bin and len(bin)==7 and bin.isdigit()else'unknown_or_invalid'
    boro=BOROUGHS.get(bbl[0]if bbl else bin[0]if bin else'','unknown');placeholder=a.get('FEATURE_CODE')==1003
    changed=not before.is_valid or removed!=0 or abs(gm.area-bm.area)>1e-6
    repair={'id':id,'original_valid':before.is_valid,'area_before_m2':bm.area,'area_after_m2':gm.area,'area_change_m2':gm.area-bm.area,'area_change_fraction':(gm.area-bm.area)/bm.area if bm.area else None,'duplicate_points_removed':removed,'method':'Shapely make_valid; containment-depth holes; no simplification','raw_record':{'path':page['path'],'object_id':oid}}
    if changed:repairs.append(repair)
    hm=h*FT if h is not None else None;groundm=ground*FT if ground is not None else None;lonlat=transform(tw.transform,gm)
    rec={'id':id,'source_id':str(sid)if sid is not None else str(oid),'source_object_id':oid,'identity_stability':'source_DOITT_ID'if stable else'version_scoped_OBJECTID','bin':bin,'bin_status':bin_status,'base_bbl':bbl,'mappluto_bbl':a.get('MAPPLUTO_BBL'),'name':a.get('NAME')or None,'address':None,'borough':boro,'height_m':hm,'height_raw_ft':a.get('HEIGHT_ROOF'),'height_status':hs,'ground_elevation_m':groundm,'ground_status':gs,'ground_vertical_datum':'per-feature unknown; modern sources generally NAVD88','floors':None,'construction_year':int(year)if year is not None else None,'feature_code':a.get('FEATURE_CODE'),'placeholder':placeholder,'geometry_source':a.get('GEOM_SOURCE'),'last_edited_at':datetime.datetime.fromtimestamp(a['LAST_EDITED_DATE']/1000,datetime.timezone.utc).isoformat()if a.get('LAST_EDITED_DATE')else None,'observation_date':None,'source_version':manifest['version'],'raw_record':{'path':page['path'],'sha256':page['sha256'],'object_id':oid},'geometry_crs':'EPSG:32118','geometry_units':'metre','geometry':mapping(gm),'geometry_wgs84':mapping(lonlat),'parts':[{'part_id':f'{id}:part:{i:03d}','geometry':mapping(p)}for i,p in enumerate(parts)],'area_m2':gm.area,'repair':repair if changed else None,'evidence':{'position':evidence('SHAPE',None if placeholder else 'official footprint coordinates',note='NAD83/WGS84 transformation is not independent ground control'),'footprint':evidence('SHAPE',None if placeholder else 'official outline','derived'if changed else'source_explicit',note='placeholder excluded'if placeholder else'geometry repair logged'if changed else'no repair required'),'height':evidence('HEIGHT_ROOF',hm,'derived',note='Source relative roof height in feet; converted using 0.3048; not independently verified; no extrusion in stage1/2'),'roof':evidence(None,None,note='roof form not contained in footprint height'),'facade':evidence(None,None,note='no facade or interior evidence'),'age':evidence('CONSTRUCTION_YEAR',int(year)if year is not None else None,note='construction year is not survey date')}}
    records.append(rec)
   except Exception as e:failures.append({'id':id,'object_id':oid,'raw_path':page['path'],'error':str(e)})
 # Do not silently merge repeated source IDs or discard multiple building parts.
 counts=Counter(r['id']for r in records)
 for r in records:
  if counts[r['id']]>1:
   conflicts.append({'kind':'duplicate_source_id','entity_id':r['id'],'object_id':r['source_object_id']});r['entity_id']=r['id'];r['id']+=f':record:{r["source_object_id"]}'
 records.sort(key=lambda r:r['id']);out=Path(output);out.mkdir(parents=True,exist_ok=True)
 text=''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n'for r in records);(out/'buildings.jsonl').write_text(text)
 report={'pipeline_version':PIPELINE_VERSION,'processor_sha256':sha(__file__),'scope':manifest['scope'],'source_manifest':str(Path(manifest_path).resolve().relative_to(ROOT)),'raw_records':manifest['records_downloaded'],'normalized_records':len(records),'source_defined_entities':len(set(r.get('entity_id',r['id'])for r in records)),'physical_building_count':'not independently resolved; DOITT entities are not guaranteed physical one-to-one','polygon_parts':sum(len(r['parts'])for r in records),'valid_height_records':sum(r['height_m']is not None for r in records),'placeholder_records':sum(r['placeholder']for r in records),'independently_verified_heights':0,'downloaded_3d_building_models':0,'unknown_roof_form':len(records),'unknown_facade':len(records),'failed':len(failures),'repairs':len(repairs),'unique_bin_count':len(set(r['bin']for r in records if r['bin_status']=='valid_format')),'output_sha256':sha(out/'buildings.jsonl'),'projection':{'source_crs':str(wkid),'standard_crs':'EPSG:32118','to_wgs84_operation':tw.description,'nominal_transform_accuracy_m':tw.accuracy},'geometry_fully_downloaded':len(records)+len(failures)==manifest['records_downloaded'],'citywide_complete':manifest['scope']['bbox_wgs84']is None and not manifest.get('partition_only',False) and not failures and not manifest['consistency']['service_changed_during_window']}
 atomic_json(out/'quality.json',report);atomic_json(out/'repairs.json',repairs);atomic_json(out/'failures.json',failures);atomic_json(out/'conflicts.json',conflicts)
 return report
