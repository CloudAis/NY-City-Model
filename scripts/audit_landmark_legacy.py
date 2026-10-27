"""Native source candidates only. No crosswalk or unit/datum resolution is implied.
The broad search box uses official CRS2263 solely for candidate discovery.
"""
import rhino3dm,json,sys,time
sys.path.insert(0,'scripts')
from nyc.coordinates import US_SURVEY_FOOT
from pathlib import Path
p=Path('data/intermediate/extracted/nyc_3dmodel_mn01/NYC_3DModel_MN01.3dm');start=time.monotonic();m=rhino3dm.File3dm.Read(str(p));print('MODEL_READ',len(m.Objects),flush=True);rows=[];cx,cy=298886.84/US_SURVEY_FOOT,60669.09/US_SURVEY_FOOT
for obj in m.Objects:
 g=obj.Geometry
 try:b=g.GetBoundingBox()
 except:continue
 if b.Min.X<cx+200 and b.Max.X>cx-200 and b.Min.Y<cy+200 and b.Max.Y>cy-200 and b.Max.Z>1200:
  rows.append({'guid':str(obj.Attributes.Id),'layer':m.Layers[obj.Attributes.LayerIndex].Name,'type':g.ObjectType.name,'bbox':[[b.Min.X,b.Min.Y,b.Min.Z],[b.Max.X,b.Max.Y,b.Max.Z]],'user_strings':list(obj.Attributes.GetUserStrings()),'vertices':len(g.Vertices)if hasattr(g,'Vertices')else None})
Path('reports/stage5/native-wtc-candidates.json').write_text(json.dumps({'count':len(rows),'objects':rows,'elapsed_seconds':time.monotonic()-start,'status':'native local audit only, NO coordinate/unit conflict silently resolved'},indent=2));print('CANDIDATES',rows[:25],flush=True)
