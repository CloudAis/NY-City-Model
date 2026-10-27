import argparse,sqlite3,json,math,hashlib,os
from pathlib import Path
from pyproj import Transformer
from shapely.geometry import shape,box
from nyc.download import ROOT,atomic_json,sha
p=argparse.ArgumentParser();p.add_argument('--bbox',nargs=4,type=float,required=True);p.add_argument('--borough',choices=['manhattan','bronx','brooklyn','queens','staten-island']);p.add_argument('--version',required=True);p.add_argument('--output',required=True);p.add_argument('--max-records',type=int,default=10000);a=p.parse_args();w,s,e,n=a.bbox
if not all(math.isfinite(x)for x in a.bbox)or not(-180<=w<e<=180 and -90<=s<n<=90):raise ValueError('invalid WGS84 bbox')
if any(x not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-'for x in a.version):raise ValueError('invalid capture version')
t=Transformer.from_crs(4326,32118,always_xy=True);pts=[t.transform(x,y)for x,y in [(w,s),(w,n),(e,s),(e,n)]];minx=min(p[0]for p in pts)-1;maxx=max(p[0]for p in pts)+1;miny=min(p[1]for p in pts)-1;maxy=max(p[1]for p in pts)+1;db=sqlite3.connect(f'file:{ROOT}/data/processed/city/buildings.sqlite?mode=ro',uri=True);sql='SELECT b.payload FROM spatial r JOIN buildings b ON b.rowid=r.row_id WHERE r.minx<=? AND r.maxx>=? AND r.miny<=? AND r.maxy>=? AND b.capture LIKE ?';args=[maxx,minx,maxy,miny,a.version+':%']
if a.borough:sql+=' AND b.borough=?';args.append(a.borough)
sql+=' ORDER BY b.id';out=Path(a.output);out.mkdir(parents=True,exist_ok=True);tmp=out/'buildings-partial.jsonl';count=0;ids=set();region=box(w,s,e,n);heights=0;parts=0
try:
 with tmp.open('w')as f:
  for (text,)in db.execute(sql,args):
   r=json.loads(text)
   if not shape(r['geometry_wgs84']).intersects(region):continue
   if r['id']in ids:raise ValueError('duplicate entity versions in export')
   ids.add(r['id']);count+=1
   if count>a.max_records:raise ValueError('query budget exceeded; narrow bbox or explicitly increase max-records')
   heights+=r['height_m']is not None;parts+=len(r['parts']);f.write(text+'\n')
 os.replace(tmp,out/'buildings.jsonl')
finally:tmp.unlink(missing_ok=True);db.close()
atomic_json(out/'quality.json',{'query_bbox_wgs84':a.bbox,'borough':a.borough,'capture_version':a.version,'raw_records':count,'normalized_records':count,'polygon_parts':parts,'valid_height_records':heights,'independently_verified_heights':0,'failed':0,'citywide_complete':False,'publication_allowed':True,'license':'NYC Open Data Terms','output_sha256':sha(out/'buildings.jsonl'),'identity_sha256':hashlib.sha256('\n'.join(sorted(ids)).encode()).hexdigest()});print('CITY_QUERY',count,flush=True)
