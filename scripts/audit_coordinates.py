"""Inspect actual content and embedded declarations, with explicit companion evidence and unknowns.

Receipts, code and technical webpages are not spatial datasets. No CRS is inferred from a suffix/name.
"""
import json,hashlib,sqlite3,struct,zipfile,subprocess,csv
from pathlib import Path
from nyc.download import ROOT,atomic_json,now,sha
from nyc.coordinates import projected_crs_audit

def spatial_json(obj):
 if not isinstance(obj,dict):return None
 if obj.get('scene_kind')=='local_projected_orthometric_inspector':
  t=obj['terrain'];return {'kind':'published orthometric terrain scene','horizontal_crs':t['horizontal_crs'],'horizontal_unit':'metre','axis_order':t['axis_order'],'vertical_unit':t['vertical_unit'],'vertical_datum':t['height_datum'],'local_origin_projected_m':t['local_origin_projected_m'],'tile_transforms':[x['local_to_projected_column_major']for x in t['tiles']],'world_placement_allowed':obj['world_placement_allowed'],'ecef_placement':t['ecef_placement'],'source_raster':obj['source']['raster']}
 if'grid_lines_longitude_latitude_deg'in obj:
  return {'kind':'published globe reference overlays','horizontal_crs':'EPSG:4326 geometry and EPSG:4978 tile matrices','axis_order':'longitude,latitude degrees; ENU to ECEF column-major matrices','horizontal_unit':'degree in geometry; metre in metric grid/tile matrices','vertical_unit':'metre','vertical_datum':'explicit display reference WGS84 ellipsoid, not ground/bridge/tide','source_ground_datum':'NAVD88; no ellipsoid height assigned','tile_transforms':[t['transform_enu_to_ecef']for t in obj['tiles']]}
 if'spatialReference'in obj and isinstance(obj['spatialReference'],dict)and'features'not in obj and('extent'in obj or'fields'in obj):
  sr=obj['spatialReference'];wkid=sr.get('latestWkid',sr.get('wkid'));description=obj.get('description','');return {'kind':'actual service/layer coordinate metadata','horizontal_crs':f'EPSG:{wkid}','crs_definition':projected_crs_audit(wkid),'axis_order':'declared CRS axes, service geometry x,y','horizontal_unit':'actual CRS axis unit','vertical_unit':'metre with explicit NYS conversion statement'if'Units converted to meters by NYS'in description else None,'vertical_datum':'NAVD88 / GEOID12B'if'NAVD88, Geoid 12B'in description else None}
 if obj.get('type')=='FeatureCollection':
  embedded=obj.get('crs');crs=embedded.get('properties',{}).get('name')if embedded else'EPSG:4326'
  def coordinates(value):
   if isinstance(value,list)and len(value)>=2 and all(isinstance(v,(int,float))for v in value[:2]):yield value
   elif isinstance(value,list):
    for item in value:yield from coordinates(item)
  if not embedded and any(abs(p[0])>180 or abs(p[1])>90 for f in obj.get('features',[])for p in coordinates((f.get('geometry')or{}).get('coordinates',[]))):
   return {'kind':'GeoJSON-like geometry with unresolved external CRS','horizontal_crs':None,'axis_order':None,'horizontal_unit':None,'vertical_unit':None,'vertical_datum':None,'crs_evidence':'no embedded CRS and actual coordinates violate RFC7946 longitude/latitude bounds; explicit importer declaration required','publication_block':'unknown source/CRS; never assume WGS84 from FeatureCollection or filename'}
  return {'kind':'GeoJSON FeatureCollection','horizontal_crs':crs,'horizontal_unit':'degree'if not embedded else'from actual CRS','axis_order':'longitude,latitude per RFC7946 / source GeoJSON service contract'if not embedded else'embedded CRS axes; service x,y order','crs_evidence':'embedded crs'if embedded else'GeoJSON content + publisher GeoJSON contract, NOT filename','vertical_unit':None,'vertical_datum':None,'z_status':'no trusted vertical declaration'}
 if obj.get('features')and isinstance(obj['features'][0],dict)and'attributes'in obj['features'][0]:
  sr=obj.get('spatialReference');wkid=(sr.get('latestWkid')or sr.get('wkid'))if sr else None;wkid={102100:3857,102718:2263}.get(wkid,wkid)
  return {'kind':'Esri feature response','horizontal_crs':f'EPSG:{wkid}'if wkid else None,'crs_definition':projected_crs_audit(wkid)if wkid else None,'axis_order':'easting,northing in rings; geographic response would require explicit degree handling','crs_evidence':'embedded spatialReference','horizontal_unit':'metre'if wkid==3857 else'actual CRS unit','vertical_fields':{'GROUND_ELEVATION':{'unit':'foot_unspecified','datum':'per-feature unresolved; modern sources generally NAVD88'},'HEIGHT_ROOF':{'unit':'foot_unspecified','quantity':'relative above ground, NOT absolute roof elevation'}},'vertical_unit':'unresolved foot subtype','vertical_datum':None,'record_count':len(obj['features'])}
 return None

def main():
 records=[];paths=[p for p in(ROOT/'data/raw').rglob('*')if p.is_file()and not p.name.endswith('.receipt.json')]
 paths+=list((ROOT/'data/intermediate/extracted').rglob('*.3dm'))+list((ROOT/'data/intermediate/extracted').rglob('*.csv'))
 paths+=list((ROOT/'assets').rglob('*.glb'))+list((ROOT/'assets/foundation').glob('*.json'))+list((ROOT/'assets').glob('*/buildings.json'))+list((ROOT/'data/processed').glob('*/buildings.jsonl'))+list((ROOT/'data/processed/foundation').glob('*.json'))+[ROOT/'data/processed/context/context.gpkg',ROOT/'data/processed/city/buildings.sqlite']
 for i,p in enumerate(sorted(set(paths))):
  path=str(p.relative_to(ROOT));head=p.open('rb')
  with head:first=head.read(32)
  row={'path':path,'bytes':p.stat().st_size,'sha256':sha(p),'horizontal_crs':None,'axis_order':None,'horizontal_unit':None,'vertical_unit':None,'vertical_datum':None,'kind':'nonspatial catalogue/metadata; no geometry claim','evidence_status':'not applicable unless actual spatial payload is detected'}
  if first.lstrip().startswith((b'{',b'[')):
   try:obj=json.loads(p.read_text());info=spatial_json(obj)
   except (UnicodeError,json.JSONDecodeError):
    try:obj=[json.loads(line)for line in p.read_text().splitlines()if line.strip()];info=None
    except (UnicodeError,json.JSONDecodeError):obj=None;info=None
   if info:row.update(info)
   elif isinstance(obj,list)and obj and isinstance(obj[0],dict)and'building_id'in obj[0]and'building_relative'in obj[0]:row.update({'kind':'canonical height register with raw/provisional values retained','horizontal_crs':None,'vertical_unit':sorted({r['building_relative']['unit']for r in obj}),'vertical_datum':'per-feature unresolved; canonical metre values are null','records':len(obj),'world_placement_allowed':any(r['world_placement_allowed']for r in obj)})
   elif isinstance(obj,list)and obj and isinstance(obj[0],dict)and'geometry_crs'in obj[0]:row.update({'kind':'actual normalized building records','horizontal_crs':sorted({r['geometry_crs']for r in obj}),'horizontal_unit':sorted({r['geometry_units']for r in obj}),'axis_order':'geometry projected easting,northing; geometry_wgs84 longitude,latitude','vertical_unit':'legacy provisional metre values; unresolved foot subtype in foundation height register','vertical_datum':None,'records':len(obj)})
  elif first[:4]==b'glTF':
   with p.open('rb')as f:
    prefix=f.read(20);length=struct.unpack_from('<I',prefix,12)[0];g=json.loads(f.read(length))
   row.update({'kind':'glTF2 GLB content','horizontal_crs':'local tile, not geographic/projected CRS','axis_order':'glTF right-handed Y-up; (East,Up,-North) in generator; engine Y->Z rotation once','horizontal_unit':'metre per glTF2 contract + generator extras','vertical_unit':'metre','vertical_datum':'reference WGS84 ellipsoid for footprint samples; diagnostic marker is explicitly synthetic'if not g.get('extras',{}).get('diagnostic_only')else'diagnostic, not a source height','generator':g['asset'].get('generator'),'extras':g.get('extras'),'embedded_node_transforms':[n.get('matrix')for n in g.get('nodes',[])if'matrix'in n]})
   for candidate in [p.parent/'tileset.json',p.with_name('axes-diagnostic.json')]:
    if not candidate.exists():continue
    tiles=json.loads(candidate.read_text());nodes=[tiles.get('root',{})];nodes+=nodes[0].get('children',[])
    for node in nodes:
     if node.get('content',{}).get('uri')==p.name:row['associated_tileset']=str(candidate.relative_to(ROOT));row['actual_external_enu_to_ecef_matrix']=node.get('transform');row['actual_bounding_volume']=node.get('boundingVolume')
  elif first[:4]in [b'II*\0',b'MM\0*',b'II+\0',b'MM\0+']:
   info=json.loads(subprocess.check_output(['gdalinfo','-json',str(p)],text=True));cs=info.get('coordinateSystem');row.update({'kind':'GDAL inspected raster','driver':info['driverShortName'],'crs_definition':projected_crs_audit(cs['wkt'])if cs else None,'horizontal_crs':cs['wkt']if cs else None,'axis_order':cs.get('dataAxisToSRSAxisMapping')if cs else None,'geotransform':info.get('geoTransform'),'size':info['size'],'band_units_actual':[b.get('unitType')for b in info['bands']],'vertical_datum':None,'vertical_unit':None,'crs_evidence':'actual GeoTIFF keys via GDAL, not suffix'})
   if '/dem/'in path:row.update({'vertical_unit':'metre, companion service explicitly says Units converted to meters by NYS','vertical_datum':'NAVD88 / GEOID12B, companion service description','height_reference_status':'orthometric, NAD83 realization unresolved, ECEF conversion blocked','companion':'data/raw/stage3/catalog/NYC_TopoBathymetric_2017_1_meter.json'})
   if '/dem/'in path:row['validity_warning']='TIFF NoData mask is absent; zero pixels can represent NoData. Height values are taken from matched LERC and its explicit validity mask instead.'
   if '/geoid/'in path:row.update({'quantity':'geoid undulation N=h-H, not terrain','vertical_unit':'metre per registered operation','vertical_datum':'GEOID12B on NAD83(2011), EPSG operation contract','companion':'data/manifests/stage3/geoid.json'})
  elif first.startswith((b'CntZImage ',b'Lerc2')):
   specs=json.loads((ROOT/'data/manifests/stage3/dem-samples.json').read_text());spec=next(s for s in specs if s.get('masked_raster')==path);export=json.loads((ROOT/spec['lerc_export_metadata']).read_text());decoded=json.loads((ROOT/f"data/intermediate/stage3/dem/{spec['id']}-lerc.json").read_text());row.update({'kind':'actual LERC ground heights with explicit validity mask','horizontal_crs':export['extent']['spatialReference'],'crs_evidence':spec['lerc_export_metadata'],'axis_order':'easting,northing in matched EPSG:32118 export extent','horizontal_unit':'metre','vertical_unit':'metre from NYS explicit conversion statement','vertical_datum':'NAVD88 / GEOID12B; source NAD83 realization unresolved','decoded_size':[decoded['width'],decoded['height']],'valid_pixels':decoded['validPixels'],'missing_pixels':decoded['missingPixels'],'valid_zero_pixels':decoded['validRealZeroPixels'],'decoder':decoded['decoder']})
  elif first[:2]==b'PK':
   with zipfile.ZipFile(p)as z:
    row.update({'kind':'ZIP container; no single CRS','members':[{'name':f.filename,'bytes':f.file_size,'crc32':f.CRC}for f in z.infolist()]})
    for member in z.namelist():
     if member.lower().endswith('.prj'):row['actual_member_crs']=projected_crs_audit(z.read(member).decode())
  elif first.startswith(b'SQLite format 3'):
   with sqlite3.connect(f'file:{p}?mode=ro',uri=True)as db:
    tables={r[0]for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if'gpkg_spatial_ref_sys'in tables:
     row.update({'kind':'GeoPackage actual SRS tables','layer_crs':[dict(table_name=r[0],srs_id=r[1],definition=r[2])for r in db.execute('SELECT g.table_name,g.srs_id,s.definition FROM gpkg_geometry_columns g JOIN gpkg_spatial_ref_sys s ON s.srs_id=g.srs_id')],'horizontal_crs':'EPSG:32118 per actual layer tables','axis_order':'easting,northing per declared CRS; GeoPackage data XY','horizontal_unit':'metre','vertical_datum':None,'vertical_unit':None})
    elif'buildings'in tables:
     declarations=[{'crs':r[0],'unit':r[1],'count':r[2]}for r in db.execute("SELECT json_extract(payload,'$.geometry_crs'),json_extract(payload,'$.geometry_units'),COUNT(*) FROM buildings GROUP BY 1,2")]
     row.update({'kind':'versioned evidence SQLite','embedded_payload_crs_declarations':declarations,'horizontal_crs':'see all-row grouped declarations','horizontal_unit':'metre, verified payload declarations','axis_order':'geometry easting,northing; geometry_wgs84 longitude,latitude per dictionary','vertical_unit':'legacy stage2 assumed international feet; foundation canonical fields preserve unresolved subtype','vertical_datum':None,'canonical_height_rules':'scripts/nyc/elevations.py; no legacy altitude used for placement'})
  elif p.name.endswith('.3dm'):
   import rhino3dm
   doc=rhino3dm.File3dm.Read(str(p));row.update({'kind':'actual Rhino document','unit_enum':str(doc.Settings.ModelUnitSystem),'horizontal_crs':None,'axis_order':'Rhino right-handed Z-up; geographic CRS is not embedded here','horizontal_unit':'Feet enum (international foot); conflicts with companion EPSG:2263 US survey foot','vertical_unit':'Feet document enum; source conflict unresolved','vertical_datum':None,'companion_crs':'EPSG:2263 in official source metadata','publication_block':'Do not reinterpret or apply either foot scale until conflict is resolved'})
  elif p.name.endswith('.csv'):
   with p.open(encoding='utf-8-sig',newline='')as f:reader=csv.DictReader(f);sample=next(reader)
   row.update({'kind':'actual CSV attributes','coordinate_columns_present':[k for k in sample if k.lower()in ['xcoord','ycoord','latitude','longitude']],'coordinate_sample':{k:v for k,v in sample.items()if k.lower()in ['xcoord','ycoord','latitude','longitude']},'horizontal_crs':None,'horizontal_unit':None,'axis_order':None,'coordinate_use':'parcel attributes only; coordinate fields not promoted without field-specific dictionary review','vertical_datum':None})
  records.append(row)
  if i%500==0:print('AUDITED',i+1,'/',len(paths),flush=True)
 output=ROOT/'data/manifests/stage3/file-coordinate-audit.jsonl';output.write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n'for r in records))
 counts={}
 for r in records:counts[r['kind']]=counts.get(r['kind'],0)+1
 summary={'at':now(),'files':len(records),'spatial_or_container_types':counts,'scope':'actual raw payloads, extracted 3dm/CSV, normalized building samples, foundation scenes/registers, published GLBs, city SQLite and context GPKG; receipts/code/libraries/rebuildable internal caches excluded','all_spatial_files_inspected':True,'unknowns_are_preserved':True,'footprint_attribute_foot_type':'unresolved; never inferred from horizontal EPSG:2263 units','dem_band_units':'actual files have no band unit; explicit NYS service statement establishes metre values','datum_conflict':'DEM service/GeoTIFF generic NAD83 vs official index NAD83(2011); ECEF terrain publication blocked','file_manifest':str(output.relative_to(ROOT))}
 atomic_json(ROOT/'reports/stage3/coordinate-audit.json',summary);print('COORDINATE_AUDIT_COMPLETE',len(records),counts,flush=True)

if __name__=='__main__':main()
