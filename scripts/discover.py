"""Retain official entry pages and extract actual links; never guess asset downloads."""
from pathlib import Path
import json,re,html,urllib.parse
from nyc.download import Downloader,atomic_json,ROOT,now,sha
ENTRIES={
 'footprints-metadata':'https://raw.githubusercontent.com/CityOfNewYork/nyc-geo-metadata/main/Metadata/Metadata_BuildingFootprints.md',
 'footprints-service':'https://services6.arcgis.com/yG5s3afENB5iO9fj/arcgis/rest/services/BUILDING_view/FeatureServer?f=pjson',
 'model3d':'https://www.nyc.gov/content/planning/pages/resources/datasets/nyc-3d-model',
 'pluto':'https://www.nyc.gov/content/planning/pages/resources/datasets/mappluto-pluto-change',
 'metadata-directory':'https://api.github.com/repos/CityOfNewYork/nyc-geo-metadata/contents/Metadata',
 'nys-lidar':'https://gis.ny.gov/elevation',
 'nys-ortho':'https://gis.ny.gov/orthoimagery',
 'nyc-open-terms':'https://opendata.cityofnewyork.us/overview/#termsofuse',
 'gltf-spec':'https://raw.githubusercontent.com/KhronosGroup/glTF/main/extensions/2.0/Vendor/EXT_structural_metadata/README.md',
 '3d-tiles-spec':'https://raw.githubusercontent.com/CesiumGS/3d-tiles/main/specification/README.md'}
def main():
 d=Downloader();items=[]
 for name,url in ENTRIES.items():
  kind='json'if name in ['footprints-service','metadata-directory']else'text'
  try:
   p=d.get(url,f'data/raw/catalog/{name}.response',kind);text=p.read_text();links=set(re.findall(r'https?://[^\s<>"\)]+',text));links.update(urllib.parse.urljoin(url,html.unescape(x))for x in re.findall(r'(?:href|src)=[\"\']([^\"\']+)',text))
   items.append({'id':name,'entry':url,'raw_path':str(p.relative_to(ROOT)),'sha256':sha(p),'links':sorted(links),'status':'retrieved','captured_at':now()})
  except Exception as e:items.append({'id':name,'entry':url,'status':'failed','error':str(e)})
 atomic_json(ROOT/'data/manifests/discovery.json',{'pipeline_version':'0.1.0-stage2','items':items})
 for i in items:
  print(i['id'],i['status']);print('\n'.join(x for x in i.get('links',[])if any(k in x.lower()for k in ['zip','3d','pluto','download','lidar','ortho','bound','road','water','scene','arcgis','geojson'])))
if __name__=='__main__':main()
