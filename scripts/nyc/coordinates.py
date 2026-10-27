"""Shared, explicit metric/geodetic/ECEF/ENU contracts. No implicit height datums."""
from dataclasses import dataclass
import math
from typing import Sequence
from pyproj import CRS,Transformer,Geod

US_SURVEY_FOOT=1200/3937
INTERNATIONAL_FOOT=0.3048
UNIT_FACTORS={'metre':1.0,'us_survey_foot':US_SURVEY_FOOT,'international_foot':INTERNATIONAL_FOOT}
METRIC_CRS=CRS.from_epsg(32118)
WGS84=CRS.from_epsg(4326)
GEODESIC=Geod(ellps='WGS84')
_TO_GEO=Transformer.from_crs(METRIC_CRS,WGS84,always_xy=True)
_TO_METRIC=Transformer.from_crs(WGS84,METRIC_CRS,always_xy=True)
_TO_ECEF=Transformer.from_crs(4979,4978,always_xy=True)
_FROM_ECEF=Transformer.from_crs(4978,4979,always_xy=True)

class UnresolvedReference(ValueError):pass

def metres(value:float,unit:str)->float:
 if unit not in UNIT_FACTORS:raise UnresolvedReference('unit not resolved: '+str(unit))
 if isinstance(value,bool)or not math.isfinite(value):raise ValueError('finite numeric measurement required')
 return value*UNIT_FACTORS[unit]

def lon_lat(lon_deg:float,lat_deg:float):
 if not all(math.isfinite(v)for v in [lon_deg,lat_deg])or not(-180<=lon_deg<=180 and -90<=lat_deg<=90):raise ValueError('longitude/latitude in degrees required, always longitude first')
 return lon_deg,lat_deg

def geographic_to_metric(lon_deg,lat_deg):return _TO_METRIC.transform(*lon_lat(lon_deg,lat_deg),errcheck=True)
def metric_to_geographic(easting_m,northing_m):return _TO_GEO.transform(easting_m,northing_m,errcheck=True)
def geographic_to_ecef(lon_deg,lat_deg,ellipsoid_height_m):
 lon_lat(lon_deg,lat_deg)
 if not math.isfinite(ellipsoid_height_m):raise ValueError('explicit ellipsoid height required')
 return _TO_ECEF.transform(lon_deg,lat_deg,ellipsoid_height_m,errcheck=True)
def ecef_to_geographic(x_m,y_m,z_m):return _FROM_ECEF.transform(x_m,y_m,z_m,errcheck=True)

def geodesic_distance(a:Sequence[float],b:Sequence[float]):
 lon_lat(*a[:2]);lon_lat(*b[:2]);return GEODESIC.inv(*a[:2],*b[:2])[2]

@dataclass(frozen=True)
class LocalFrame:
 longitude_deg:float
 latitude_deg:float
 ellipsoid_height_m:float
 origin_ecef_m:tuple
 basis_enu:tuple
 matrix_enu_to_ecef:tuple

 @classmethod
 def at(cls,lon_deg,lat_deg,ellipsoid_height_m):
  lon_lat(lon_deg,lat_deg);a,b=math.radians(lon_deg),math.radians(lat_deg)
  east=(-math.sin(a),math.cos(a),0.0)
  north=(-math.sin(b)*math.cos(a),-math.sin(b)*math.sin(a),math.cos(b))
  up=(math.cos(b)*math.cos(a),math.cos(b)*math.sin(a),math.sin(b))
  origin=geographic_to_ecef(lon_deg,lat_deg,ellipsoid_height_m)
  return cls(lon_deg,lat_deg,ellipsoid_height_m,origin,(east,north,up),(*east,0.,*north,0.,*up,0.,*origin,1.))

 def to_local(self,ecef):
  delta=[ecef[i]-self.origin_ecef_m[i]for i in range(3)]
  return tuple(sum(delta[i]*axis[i]for i in range(3))for axis in self.basis_enu)

 def to_ecef(self,enu):return tuple(self.origin_ecef_m[i]+sum(enu[j]*self.basis_enu[j][i]for j in range(3))for i in range(3))

 def manifest(self):return {'world_crs':'EPSG:4978','geographic_crs':'EPSG:4979','origin_longitude_latitude_degrees':[self.longitude_deg,self.latitude_deg],'origin_ellipsoid_height_m':self.ellipsoid_height_m,'origin_ecef_m':self.origin_ecef_m,'enu_to_ecef_column_major':self.matrix_enu_to_ecef,'gltf_coordinates':'East,Up,-North','engine_conversion':'glTF Y-up -> tiles Z-up: (x,y,z)->(x,-z,y), applied exactly once','units':'metre','height_reference':'WGS84 ellipsoid; source orthometric heights need a separate approved operation'}

def enu_to_gltf(e,n,u):return(e,u,-n)
def gltf_to_enu(x,y,z):return(x,-z,y)

def projected_crs_audit(crs_input):
 c=CRS.from_user_input(crs_input)
 return {'identifier':c.to_string(),'wkt':c.to_wkt(),'datum':c.datum.name if c.datum else None,'axes':[{'name':a.name,'abbreviation':a.abbrev,'direction':a.direction,'unit':a.unit_name,'unit_to_si':a.unit_conversion_factor}for a in c.axis_info],'always_xy_in_pipeline':True,'native_axis_order_must_not_be_confused_with_payload_order':True}

def projected_vertices_to_local(xy,ellipsoid_height_m,local_frame):
 """Batched version of the same formal transformations; never orthometric input.

 Height is an explicitly declared display ellipsoid height, or an independently
 approved WGS84 ellipsoid height. This function does not resolve source datums.
 """
 import numpy as np
 points=np.asarray(xy,dtype=np.float64)
 if points.ndim!=2 or points.shape[1]!=2 or not np.isfinite(points).all():raise ValueError('finite projected metre XY pairs required')
 h=np.broadcast_to(np.asarray(ellipsoid_height_m,dtype=np.float64),(len(points),))
 if not np.isfinite(h).all():raise ValueError('explicit finite ellipsoid heights required')
 lon,lat=_TO_GEO.transform(points[:,0],points[:,1],errcheck=True)
 xyz=np.array(_TO_ECEF.transform(lon,lat,h,errcheck=True)).T
 return (xyz-np.asarray(local_frame.origin_ecef_m))@np.asarray(local_frame.basis_enu).T
