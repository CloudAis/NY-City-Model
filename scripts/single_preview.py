from pathlib import Path
import argparse,json
from nyc.tiles import frame,local_point,rings
from nyc.download import ROOT
p=argparse.ArgumentParser();p.add_argument('datasets',nargs='*',default=['data/processed/lower-manhattan']);p.add_argument('--output',default='reports/nyc-real-sample-preview.html');a=p.parse_args();areas=[]
for path in a.datasets:
 rows=[json.loads(x)for x in(Path(path)/'buildings.jsonl').read_text().splitlines()if x];rows=[r for r in rows if not r['placeholder']];allp=[p for r in rows for ring in rings(r['geometry'])for p in ring];x=sum(p[0]for p in allp)/len(allp);y=sum(p[1]for p in allp)/len(allp);origin,basis,matrix,ll=frame(x,y);features=[]
 for r in rows:
  lines=[]
  for ring in rings(r['geometry']):
   for q1,q2 in zip(ring,ring[1:]):
    for q in [q1,q2]:e,n,u=local_point(*q[:2],origin,basis);lines.extend([round(e,4),round(n,4),round(u+.25,4)])
  features.append({'id':r['id'],'bin':r['bin'],'name':r['name'],'height_raw_ft':r['height_raw_ft'],'legacy_stage2_height_m':r['height_m'],'height_status':r['evidence']['height']['status'],'edited_at':r['last_edited_at'],'observation_date':None,'lines':lines})
 areas.append({'id':Path(path).name,'origin_wgs84':ll,'origin_ecef_m':origin,'enu_to_ecef_column_major':matrix,'height_reference':'declared WGS84 ellipsoid reference only, not ground','features':features})
raw=json.dumps({'representation':'genuine official footprint linework only','height_applied':False,'source':'https://github.com/CityOfNewYork/nyc-geo-metadata/blob/main/Metadata/Metadata_BuildingFootprints.md','areas':areas},ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
text=(ROOT/'scripts/templates/preview.html').read_text().replace('__REAL_DATA_JSON__',raw);out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text);print(out,len(text.encode()),'bytes; real features',sum(len(x['features'])for x in areas))
