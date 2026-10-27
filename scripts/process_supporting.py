"""Separate safe extraction, 3dm audit and parcel evidence; do not assign lot attributes as building truth."""
from pathlib import Path
import json,zipfile,csv,collections,sys
from nyc.download import ROOT,atomic_json,sha,now
MAX_UNPACKED=2*1024**3

def extract(archive):
 src=ROOT/'data/raw/supporting'/archive;dest=ROOT/'data/intermediate/extracted'/src.stem;receipt=dest/'extract-manifest.json'
 if receipt.exists():
  m=json.loads(receipt.read_text())
  if m['archive_sha256']!=sha(src):raise ValueError('archive changed under extraction cache')
  for f in m['files']:
   if sha(dest/f['name'])!=f['sha256']:raise ValueError('extraction checksum mismatch')
  return dest,m
 with zipfile.ZipFile(src)as z:
  info=z.infolist()
  if sum(i.file_size for i in info)>MAX_UNPACKED:raise ValueError('unpack disk budget exceeded')
  for i in info:
   target=(dest/i.filename).resolve()
   if not target.is_relative_to(dest.resolve())or i.flag_bits&1:raise ValueError('unsafe/encrypted zip member')
  dest.mkdir(parents=True,exist_ok=True);files=[]
  for i in info:
   if i.is_dir():continue
   target=dest/i.filename;target.parent.mkdir(parents=True,exist_ok=True)
   if target.exists():raise ValueError('unreceipted extraction exists; do not overwrite')
   with z.open(i)as inp,target.open('xb')as out:
    while chunk:=inp.read(1024*1024):out.write(chunk)
   files.append({'name':i.filename,'bytes':target.stat().st_size,'sha256':sha(target)})
 m={'archive':str(src.relative_to(ROOT)),'archive_sha256':sha(src),'at':now(),'files':files};atomic_json(receipt,m);return dest,m

def model():
 import rhino3dm
 dest,manifest=extract('nyc_3dmodel_mn01.zip');path=next(dest.rglob('*.3dm'));doc=rhino3dm.File3dm.Read(str(path))
 if doc is None:raise ValueError('3dm parser failed')
 layers=[{'index':l.Index,'name':l.Name,'parent_id':str(l.ParentLayerId)}for l in doc.Layers];types=collections.Counter();counts=collections.Counter();samples=[];mins=[float('inf')]*3;maxs=[float('-inf')]*3;ids=[];layerbboxes={};bbox_failures=[]
 for obj in doc.Objects:
  geom=obj.Geometry;name=type(geom).__name__;types[name]+=1;counts[obj.Attributes.LayerIndex]+=1;
  try:
   box=geom.GetBoundingBox();lo=[box.Min.X,box.Min.Y,box.Min.Z];hi=[box.Max.X,box.Max.Y,box.Max.Z]
  except TypeError as e:
   bbox_failures.append({'id':str(obj.Attributes.Id),'type':name,'reason':'annotation requires a dimension style; not treated as building geometry'});lo=[float('inf')]*3;hi=[float('-inf')]*3
  for i in range(3):mins[i]=min(mins[i],lo[i]);maxs[i]=max(maxs[i],hi[i])
  oid=str(obj.Attributes.Id);ids.append(oid)
  if len(samples)<25:samples.append({'object_id':oid,'name':obj.Attributes.Name,'geometry_type':name,'layer_index':obj.Attributes.LayerIndex,'bbox_source_units':[lo,hi]if all(__import__('math').isfinite(x)for x in lo+hi)else None,'user_strings':list(obj.Attributes.GetUserStrings())})
 report={'at':now(),'archive':manifest,'file':str(path.relative_to(ROOT)),'unit_system':str(doc.Settings.ModelUnitSystem),'absolute_tolerance_source_units':doc.Settings.ModelAbsoluteTolerance,'source_crs':'EPSG:2263 stated by OTI metadata; document units inspected separately','vertical_datum':'source 3D report must be reconciled; not directly applied as WGS84 ellipsoid height','bbox_source_units':[mins,maxs],'geometry_objects':len(ids),'unique_object_ids':len(set(ids)),'geometry_types':dict(types),'layers':[{**l,'objects':counts[l['index']]}for l in layers],'sample_objects':samples,'bbox_unavailable_annotation_objects':bbox_failures,'observation_year':2014,'dcp_data_date':'2018-08','dcp_release_date':'2018-10-19','publication_state':'downloaded and parsed; not yet spatially matched or converted to current buildings','matched_current_buildings':0,'independently_verified_models':0,'no_interiors_generated':True}
 report['unit_conflict']={'metadata_horizontal':'US survey foot, EPSG:2263','document_units':str(doc.Settings.ModelUnitSystem),'selection':None,'reason':'Reconcile control points and vendor documentation before model transformation; do not silently apply international-foot or survey-foot scaling.'}
 report['object_count_warning']='Layers include curves and Brep surfaces representing overlapping components; geometry object count is not a count of physical buildings.'
 report['overall_bbox_warning']='Includes broad context/contours; not an audited building-only MN01 coverage envelope.'
 atomic_json(ROOT/'reports/official-model-audit.json',report);print('MODEL',len(ids),str(doc.Settings.ModelUnitSystem),types,flush=True)

def parcels():
 dest,manifest=extract('nyc_pluto_26v2_csv.zip');path=next(dest.rglob('*.csv'));counts=collections.Counter();bblcounts=collections.Counter();target={}
 for p in(ROOT/'data/processed').glob('*/buildings.jsonl'):
  if p.parent.name=='city':continue
  for line in p.read_text().splitlines():
   r=json.loads(line)
   for bbl in [r.get('base_bbl'),r.get('mappluto_bbl')]:
    if bbl:target.setdefault(str(bbl),[]).append(r['id'])
 matches=[];total=0
 with path.open(newline='',encoding='utf-8-sig')as f:
  reader=csv.DictReader(f);fields=reader.fieldnames
  for row in reader:
   total+=1;boro=row.get('borough')or row.get('Borough');counts[boro]+=1;bbl=row.get('bbl')or row.get('BBL');bblcounts[bbl]+=1
   # CSV BBL may be serialized with a trailing .000; retain its original value as well.
   key=str(bbl).split('.')[0]if bbl else None
   if key in target:matches.append({'bbl':key,'raw_bbl':bbl,'building_ids':sorted(set(target[key])),'parcel_attributes':row,'source_file':str(path.relative_to(ROOT)),'source_version':'26v2','scope':'parcel only; not copied to building height/floors/age','evidence_status':'source_explicit','independently_verified':False})
 atomic_json(ROOT/'data/processed/pluto-pilot-links.json',matches)
 atomic_json(ROOT/'reports/pluto-audit.json',{'at':now(),'source_version':'26v2','data_date':'2026-08','release_date':None,'release_date_note':'page supplies version and data date; no exact release day assumed','archive':manifest,'rows':total,'borough_rows':dict(counts),'unique_bbl_values':len(bblcounts),'duplicate_bbl_values':sum(v>1 for v in bblcounts.values()),'fields':fields,'pilot_lot_matches':len(matches),'link_output':'data/processed/pluto-pilot-links.json','building_values_overwritten':0,'raw_path':str(path.relative_to(ROOT))})
 print('PLUTO',total,dict(counts),'matches',len(matches),flush=True)
if __name__=='__main__':
 which=sys.argv[1]if len(sys.argv)>1 else'all'
 if which in ['model','all']:model()
 if which in ['pluto','all']:parcels()
