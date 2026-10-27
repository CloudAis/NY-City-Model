"""Bare-earth sampling. NoData and exterior cells remain unknown; DSM is rejected."""
import json,math
from pathlib import Path
import numpy as np
from .coordinates import UnresolvedReference

class BareEarthRaster:
 def __init__(self,metadata_path,source):
  self.metadata=json.loads(Path(metadata_path).read_text());self.source=source
  if source.get('masked_raster')and(not self.metadata.get('lerc_mask_applied')or self.metadata.get('height_and_mask_source')!=source['masked_raster']):raise ValueError('required source validity mask was not applied; unmasked TIFF heights cannot be published')
  if source.get('surface_kind')!='bare_earth_dem':raise ValueError('explicit bare-earth evidence required; DSM/highest-hit is not a ground surface')
  if source.get('vertical_units')!='metre'or source.get('vertical_datum')!='NAVD88':raise UnresolvedReference('DEM units/datum must have explicit source evidence')
  if self.metadata['authority']!=['EPSG','32118']:raise ValueError('actual raster must be in EPSG:32118')
  self.values=np.load(self.metadata['numpy_file']);self.gt=self.metadata['geotransform'];self.height,self.width=self.values.shape
  if not np.isfinite(self.values).any():raise ValueError('no valid DEM cells; unknown terrain must not be published as zero')
  if self.gt[2]!=0 or self.gt[4]!=0:raise ValueError('rotated grid must be formally resampled before use')

 def coordinate(self,row,col):
  return(self.gt[0]+(col+.5)*self.gt[1],self.gt[3]+(row+.5)*self.gt[5])

 def sample(self,easting_m,northing_m):
  c=(easting_m-self.gt[0])/self.gt[1]-.5;r=(northing_m-self.gt[3])/self.gt[5]-.5
  if not(0<=c<=self.width-1 and 0<=r<=self.height-1):return None
  c0,r0=math.floor(c),math.floor(r);c1=min(c0+1,self.width-1);r1=min(r0+1,self.height-1)
  v=[self.values[r0,c0],self.values[r0,c1],self.values[r1,c0],self.values[r1,c1]]
  if not all(np.isfinite(x)for x in v):return None
  a,b=c-c0,r-r0
  return float(v[0]*(1-a)*(1-b)+v[1]*a*(1-b)+v[2]*(1-a)*b+v[3]*a*b)

 def lod(self,step=4):
  rows=list(range(0,self.height,step));cols=list(range(0,self.width,step))
  if rows[-1]!=self.height-1:rows.append(self.height-1)
  if cols[-1]!=self.width-1:cols.append(self.width-1)
  x0,y0=self.coordinate(rows[len(rows)//2],cols[len(cols)//2]);vertices=[];heights=[];indices=[]
  for row in rows:
   for col in cols:
    x,y=self.coordinate(row,col);z=float(self.values[row,col]);heights.append(z if math.isfinite(z)else None);vertices.extend([x-x0,y-y0,z if math.isfinite(z)else 0])
  width=len(cols)
  for r in range(len(rows)-1):
   for c in range(width-1):
    a=r*width+c;b=a+1;d=a+width;e=d+1
    # A missing source cell within the LOD cell also removes its surface. Never bridge a void.
    if not np.isfinite(self.values[rows[r]:rows[r+1]+1,cols[c]:cols[c+1]+1]).all():continue
    indices.extend([a,d,b,b,d,e])
  tiles=[];boundaries={};seams=[];cut_r=(len(rows)-1)//2;cut_c=(width-1)//2
  for ri,(r0,r1)in enumerate([(0,cut_r),(cut_r,len(rows)-1)]):
   for ci,(c0,c1)in enumerate([(0,cut_c),(cut_c,width-1)]):
    # Independent local origin and float32 vertex storage for every published tile.
    ox,oy=self.coordinate(rows[(r0+r1)//2],cols[(c0+c1)//2]);v=[];lookup={};tile_indices=[]
    for r in range(r0,r1+1):
     for c in range(c0,c1+1):
      old=r*width+c;lookup[old]=len(v)//3;x,y=self.coordinate(rows[r],cols[c]);z=heights[old]
      xyz=[float(np.float32(x-ox)),float(np.float32(y-oy)),float(np.float32(z if z is not None else 0))];v.extend(xyz)
      if z is not None and(r in [r0,r1]or c in [c0,c1]):
       key=(rows[r],cols[c]);restored=(xyz[0]+ox,xyz[1]+oy,xyz[2])
       if key in boundaries:seams.append(math.dist(restored,boundaries[key]))
       boundaries[key]=restored
    for i in range(0,len(indices),3):
     tri=indices[i:i+3]
     if all(k in lookup for k in tri):tile_indices.extend(lookup[k]for k in tri)
    tiles.append({'id':f'{ri}-{ci}','vertices':v,'indices':tile_indices,'origin_projected_m':[ox,oy],'source_lod_row_range':[r0,r1],'source_lod_column_range':[c0,c1],'local_to_projected_column_major':[1,0,0,0,0,1,0,0,0,0,1,0,ox,oy,0,1],'coordinate_kind':'projected x/y and NAVD88 z, NOT ECEF','ecef_transform':None})
  max_seam=max(seams,default=0)
  if max_seam>.10:raise ValueError('published float32 terrain tile seam exceeds 0.10m numerical target')
  return {'width':width,'height':len(rows),'vertices':vertices,'heights':heights,'indices':indices,'tiles':tiles,'tile_shared_boundary_comparisons':len(seams),'tile_seam_max_m':max_seam,'local_origin_projected_m':[x0,y0],'axis_order':'East,North,Up (Z-up), NOT a glTF or ECEF vertex buffer','horizontal_crs':'EPSG:32118','height_datum':'NAVD88','vertical_unit':'metre','vertical_exaggeration':1,'source_resolution_m':[abs(self.gt[1]),abs(self.gt[5])],'display_decimation':step,'unknown_not_filled_with_zero':True,'ecef_placement':None,'ecef_block_reason':'source NAD83 realization differs between service/index; geoid is not applied on an assumption'}
