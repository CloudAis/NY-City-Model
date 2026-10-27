"""Ground, relative heights and absolute tops stay distinct; unresolved inputs cannot be added."""
from dataclasses import dataclass,asdict
from .coordinates import metres,UnresolvedReference

@dataclass(frozen=True)
class Elevation:
 value:float|None
 unit:str
 quantity:str
 datum:str|None
 horizontal_frame:str|None
 ground_reference_id:str|None=None
 source:str|None=None

 def metric(self):
  if self.value is None:raise UnresolvedReference('measurement is unknown')
  if self.quantity=='building_relative'and self.value<0:raise ValueError('negative relative building height is not valid ground data')
  return metres(self.value,self.unit)

 def record(self):
  r=asdict(self)
  try:r['value_m']=self.metric();r['unit_status']='resolved'
  except UnresolvedReference:r['value_m']=None;r['unit_status']='unresolved'
  return r

def absolute_roof(ground:Elevation,relative:Elevation):
 if ground.quantity!='ground_orthometric' or relative.quantity!='building_relative':raise ValueError('only relative building height may be added to ground; never add an absolute roof twice')
 if not ground.datum or not ground.horizontal_frame:raise UnresolvedReference('ground datum/reference frame unresolved')
 if not ground.ground_reference_id or relative.ground_reference_id!=ground.ground_reference_id:raise UnresolvedReference('relative height and ground do not share the same base reference')
 return Elevation(ground.metric()+relative.metric(),'metre','roof_absolute',ground.datum,ground.horizontal_frame,ground.ground_reference_id,'derived: same-reference ground + relative building height')

class GeoidConversion:
 """GEOID12B has a NAD83(2011) frame contract, not a citywide constant offset."""
 def __init__(self,grid_path):
  from pathlib import Path
  from pyproj import Transformer
  self.grid=Path(grid_path).resolve()
  if not self.grid.exists():raise UnresolvedReference('GEOID12B grid is unavailable')
  # GEOID12B stores N=h-H. PROJ inverse of ellipsoid->orthometric vgridshift returns h.
  self.operation=Transformer.from_pipeline(f'+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad +step +proj=vgridshift +grids={self.grid} +multiplier=1 +step +proj=unitconvert +xy_in=rad +xy_out=deg')

 def orthometric_to_ellipsoid(self,lon_deg,lat_deg,elevation:Elevation):
  if elevation.datum!='NAVD88' or elevation.horizontal_frame!='NAD83(2011)':raise UnresolvedReference('GEOID12B requires explicit NAVD88 and NAD83(2011); do not substitute generic NAD83 or WGS84')
  if elevation.quantity not in ['ground_orthometric','roof_absolute','water_orthometric']:raise ValueError('absolute orthometric elevation required')
  height=self.operation.transform(lon_deg,lat_deg,elevation.metric(),errcheck=True)[2]
  return Elevation(height,'metre','ellipsoid_height','GRS80 ellipsoid / NAD83(2011)','NAD83(2011)',elevation.ground_reference_id,'GEOID12B registered grid; still requires an explicit horizontal/frame operation before WGS84 ECEF')

def building_register(record,raw_attributes):
 id=record['id'];source='nyc-building-footprints';common=dict(unit='foot_unspecified',datum=None,horizontal_frame=None,ground_reference_id=id,source=source)
 ground=Elevation(raw_attributes.get('GROUND_ELEVATION'),quantity='ground_orthometric',**common)
 height=Elevation(raw_attributes.get('HEIGHT_ROOF')if record['height_m']is not None else None,quantity='building_relative',**common)
 unknown=lambda kind:Elevation(None,'unknown',kind,None,None,None,None).record()
 return {'building_id':id,'schema_version':1,'raw_values':{'GROUND_ELEVATION':raw_attributes.get('GROUND_ELEVATION'),'HEIGHT_ROOF':raw_attributes.get('HEIGHT_ROOF')},'ground':ground.record(),'building_relative':height.record(),'roof_absolute':unknown('roof_absolute'),'spire_height':unknown('spire_height'),'antenna_height':unknown('antenna_height'),'legacy_stage2_height_m':record['height_m'],'legacy_stage2_ground_m':record['ground_elevation_m'],'legacy_note':'Stage2 assumed international feet for attributes labelled only feet. Preserved for audit; not canonical measurements and never applied to buildings.','ground_datum_evidence':'source says modern measurements generally NAVD88, not a per-feature datum guarantee','raw_record':record['raw_record'],'world_placement_allowed':False,'block_reason':'foot subtype and per-feature vertical reference unresolved'}
