"""Repeatable stage-3 acquisition, following links retained from the official NYS DEM page.

Only real 257-square bare-earth crops and one registered geoid grid; no cloud dependency at runtime.
"""
import argparse,json,urllib.parse,warnings
from nyc.download import Downloader,atomic_json,ROOT,sha
from pyproj.transformer import TransformerGroup

AREAS={'lower-manhattan':[-74.021,40.700,-74.002,40.716],'midtown':[-73.996,40.743,-73.970,40.761],'brooklyn-dumbo':[-74.000,40.692,-73.980,40.710],'queens-lic':[-73.958,40.736,-73.932,40.756],'bronx-mott-haven':[-73.936,40.800,-73.912,40.822],'staten-st-george':[-74.090,40.633,-74.065,40.654]}

def main():
 p=argparse.ArgumentParser();p.add_argument('--area',choices=list(AREAS));a=p.parse_args();d=Downloader(timeout=35,retries=2,max_bytes=64*1024**2)
 catalog=json.loads((ROOT/'data/raw/stage3/catalog/nys-elevation-services.json').read_text())
 service=next(s for s in catalog['services']if s['name']=='NYC_TopoBathymetric_2017_1_meter'and s['type']=='ImageServer')
 base='https://elevation.its.ny.gov/arcgis/rest/services/'+service['name']+'/'+service['type']
 metadata=json.loads((ROOT/'data/raw/stage3/catalog/NYC_TopoBathymetric_2017_1_meter.json').read_text())
 if 'Units converted to meters by NYS'not in metadata['description']or'bare earth digital elevation model'not in metadata['description']:raise ValueError('bare-earth / vertical unit evidence changed; do not assume a metre DTM')
 out=[]
 for name,bbox in AREAS.items():
  if a.area and name!=a.area:continue
  params={'f':'json','bbox':','.join(map(str,bbox)),'bboxSR':4326,'imageSR':32118,'size':'257,257','format':'tiff','pixelType':'F32','interpolation':'RSP_BilinearInterpolation','noDataInterpretation':'esriNoDataMatchAny'}
  receipt=d.get(base+'/exportImage?'+urllib.parse.urlencode(params),f'data/raw/stage3/dem/{name}-export.json');x=json.loads(receipt.read_text());image=d.get(x['href'],f'data/raw/stage3/dem/{name}.tif','binary')
  masked_params={**params,'format':'lerc'};masked_meta=d.get(base+'/exportImage?'+urllib.parse.urlencode(masked_params),f'data/raw/stage3/dem/{name}-lerc-export.json');mx=json.loads(masked_meta.read_text());masked=d.get(mx['href'],f'data/raw/stage3/dem/{name}.lerc','binary')
  if mx['extent']!=x['extent']:raise ValueError('LERC mask and TIFF georeference extents differ')
  out.append({'id':name,'surface_kind':'bare_earth_dem','request_bbox_wgs84':bbox,'export_metadata':str(receipt.relative_to(ROOT)),'raster':str(image.relative_to(ROOT)),'sha256':sha(image),'extent':x['extent'],'source_service':base,'vertical_units':'metre','vertical_datum':'NAVD88','geoid_model':'GEOID12B','source_horizontal_frame':'NAD83 realization unresolved; service 2263 vs index 6539','source_description_evidence':'data/raw/stage3/catalog/NYC_TopoBathymetric_2017_1_meter.json','source_capture_period':['2017-05-03','2017-07-26'],'processing':'server bilinear resampling to 257x257; native service XY resolution is 1 US survey foot despite its name; output is not native-resolution terrain'})
  print('DEM',name,image.stat().st_size,flush=True)
  out[-1].update({'masked_raster':str(masked.relative_to(ROOT)),'masked_sha256':sha(masked),'lerc_export_metadata':str(masked_meta.relative_to(ROOT)),'primary_height_values_source':'LERC decoded pixels and validity mask; TIFF is retained for actual GDAL georeferencing only','tiff_mask_warning':'NYS TIFF export has no NoData tag and turns absent samples into zero; never use unmasked TIFF heights'})
 target=ROOT/'data/manifests/stage3/dem-samples.json'
 if a.area and target.exists():out=[r for r in json.loads(target.read_text())if r['id']!=a.area]+out
 atomic_json(target,out)
 warnings.filterwarnings('ignore',category=UserWarning)
 group=TransformerGroup('EPSG:6349','EPSG:6319',always_xy=True,allow_ballpark=False,allow_superseded=True)
 # The operation is superseded by GEOID18 but matches the captured source's GEOID12B definition.
 candidates=[(op,g)for op in group.unavailable_operations for g in op.grids if g.short_name=='us_noaa_g2012bu0.tif']
 if candidates:
  op,g=candidates[0];path=d.get(g.url,'data/raw/stage3/geoid/'+g.short_name,'binary')
  atomic_json(ROOT/'data/manifests/stage3/geoid.json',{'path':str(path.relative_to(ROOT)),'source_url':g.url,'sha256':sha(path),'model':'GEOID12B','source_crs':'EPSG:6349','target_crs':'EPSG:6319','nominal_operation_accuracy_m':op.accuracy,'operation':op.name,'open_license_from_proj_database':g.open_license,'applied_to_dem':False,'reason':'source horizontal realization differs between service and index; no implicit reinterpretation as NAD83(2011)'})

if __name__=='__main__':main()
