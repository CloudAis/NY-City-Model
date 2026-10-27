"""Discover supporting resources from captured official pages, retain exact provenance."""
import json,re,html,urllib.parse,urllib.request,sys,zipfile
from pathlib import Path
from nyc.download import Downloader,ROOT,atomic_json,now,sha
D=Downloader();records=[]
def links(text,base):return sorted(set(urllib.parse.urljoin(base,html.unescape(x))for x in re.findall(r'(?:href|src)=[\"\']([^\"\']+)',text)))
def capture(name,url,kind='json',limit=256*1024*1024):
 try:
  p=Downloader(max_bytes=limit).get(url,'data/raw/supporting/'+name,kind);r={'id':name,'url':url,'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size,'status':'downloaded'}
  if kind=='zip':
   with zipfile.ZipFile(p)as z:
    r['archive_entries']=[{'path':i.filename,'compressed_bytes':i.compress_size,'bytes':i.file_size}for i in z.infolist()];r['uncompressed_bytes']=sum(i.file_size for i in z.infolist())
  records.append(r);print(name,r['status'],r['bytes'],flush=True);return p
 except Exception as e:records.append({'id':name,'url':url,'status':'failed_or_budget_blocked','error':str(e)});print('FAILED',name,str(e),flush=True)
for name in ['model3d','pluto']:
 data=json.loads((ROOT/f'data/raw/catalog/{name}-content.response').read_text());ll=links(data['description'],'https://www.nyc.gov');records.append({'id':name+'-resources','entry':f'https://www.nyc.gov/content/planning/pages/resources/datasets/{"nyc-3d-model"if name=="model3d"else"mappluto-pluto-change"}','content_api_source':str(ROOT/f'data/raw/catalog/{name}-content.response'),'links':ll,'status':'catalogued'})
 if name=='model3d':
  url=next(u for u in ll if u.endswith('nyc_3dmodel_mn01.zip'));capture('nyc_3dmodel_mn01.zip',url,'zip')
 else:
  for ending in ['nyc_pluto_26v2_csv.zip','pluto_datadictionary.pdf','pluto_readme.pdf']:
   url=next(u for u in ll if u.endswith(ending));capture(ending,url,'zip'if ending.endswith('zip')else'binary')
  fs=next(u for u in ll if '/FeatureServer/0'in u);capture('mappluto-layer.json',fs+'?f=pjson')
# Socrata catalogue discovery returns official dataset identities; asset URLs are read from resulting metadata.
for name,q in [('borough','Borough Boundaries'),('roadbed','Roadbed'),('water','Hydrography'),('lidar','LiDAR')]:
 url='https://api.us.socrata.com/api/catalog/v1?'+urllib.parse.urlencode({'search_context':'data.cityofnewyork.us','q':q,'limit':8});capture('catalog-'+name+'.json',url)
for id in ['7sc8-jtbz','tnru-abg2']:capture('socrata-'+id+'.json',f'https://data.cityofnewyork.us/api/views/{id}.json')
# Official planimetric publication supplies actual NYC feature service URLs through its ArcGIS catalogue.
url='https://nyc.maps.arcgis.com/sharing/rest/search?'+urllib.parse.urlencode({'q':'owner:NYC_GIS Planimetric','f':'json','num':100});capture('arcgis-planimetrics-search.json',url)
# The 2024 imagery item is linked directly in captured official metadata; inspect metadata/data rather than assume tile URLs.
p=ROOT/'data/raw/catalog/Metadata_AerialImagery.md';text=p.read_text();ids=sorted(set(re.findall(r'item.html\?id=([a-f0-9]{32})',text)))
for id in ids:
 r=capture('imagery-item-'+id+'.json',f'https://nyc.maps.arcgis.com/sharing/rest/content/items/{id}?f=pjson')
 if r:
  obj=json.loads(r.read_text());print('IMAGERY_ITEM',obj.get('title'),obj.get('url'),flush=True)
atomic_json(ROOT/'data/manifests/supporting-discovery.json',{'at':now(),'items':records})
