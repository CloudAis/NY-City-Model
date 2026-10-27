"""Fetch one reference tile using the URL discovered from an official imagery item.

No imagery is copied into published assets. Re-fetches preserve original raw bytes.
"""
import argparse,json,math
from pathlib import Path
from nyc.download import Downloader,ROOT,sha,atomic_json,now

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--item',default='423f15185bd04f8dad8d99fba736772f')
p.add_argument('--version',default='2024')
p.add_argument('--level',type=int,default=18)
p.add_argument('--row',type=int,default=98565)
p.add_argument('--column',type=int,default=77178)
p.add_argument('--output',default='data/raw/imagery')
p.add_argument('--refetch',action='store_true')
a=p.parse_args()
if len(a.item)!=32 or any(c not in '0123456789abcdef'for c in a.item):p.error('invalid official ArcGIS item ID')
if not a.version or any(c not in '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_'for c in a.version):p.error('version must be a safe capture label')
if min(a.level,a.row,a.column)<0:p.error('negative tile index')
d=Downloader(max_bytes=8*1024**2)
item_path=d.get(f'https://nyc.maps.arcgis.com/sharing/rest/content/items/{a.item}?f=pjson',f'data/raw/supporting/imagery-item-{a.item}.json')
item=json.loads(item_path.read_text());service=item.get('url','').rstrip('/')
if not service.startswith('https://')or not service.endswith('/MapServer'):raise ValueError('official item does not point to a tiled MapServer')
mp=d.get(service+'?f=pjson',f'data/raw/supporting/ortho-{a.item}-service.json');meta=json.loads(mp.read_text());info=meta['tileInfo']
lod=next((x for x in info['lods']if x['level']==a.level),None)
if lod is None:raise ValueError('level not published by service')
resolution=lod['resolution'];width=info['cols']*resolution;height=info['rows']*resolution
w=info['origin']['x']+a.column*width;n=info['origin']['y']-a.row*height
root=Path(a.output)/a.version;root.mkdir(parents=True,exist_ok=True)
path=d.get(f'{service}/tile/{a.level}/{a.row}/{a.column}',root/f'{a.level}-{a.row}-{a.column}.image','image',refresh=a.refetch)
receipt=json.loads(path.with_name(path.name+'.receipt.json').read_text())
report={'at':now(),'official_item':a.item,'service':service,'path':str(path.resolve().relative_to(ROOT))if path.resolve().is_relative_to(ROOT)else str(path.resolve()),'sha256':sha(path),'bytes':path.stat().st_size,'tile':{'level':a.level,'row':a.row,'column':a.column},'bounds':[w,n-height,w+width,n],'crs':info['spatialReference'],'pixel_dimensions':[info['cols'],info['rows']],'map_units_per_pixel':resolution,'downloaded_at':receipt['download_completed_at'],'item_modified_milliseconds':item.get('modified'),'observation_date':None,'observation_note':'Read acquisition year/period from official metadata; item modification and version label are not observation dates','license':item.get('licenseInfo'),'reuse_class':'reference-only pending licence reconciliation; never copied to assets','refetch_requested':a.refetch}
atomic_json(ROOT/'reports/ortho-tile-latest.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
