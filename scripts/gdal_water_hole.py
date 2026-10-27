"""System GDAL helper: select an actual source hole with deterministic area criteria."""
import json
from pathlib import Path
from osgeo import ogr
ogr.UseExceptions();root=Path(__file__).resolve().parents[1];ds=ogr.Open(str(root/'data/processed/context/context.gpkg'));layer=ds.GetLayerByName('water');best=None
for feature in layer:
 if feature.GetField('feat_code')not in ['2620','2660']:continue
 g=feature.GetGeometryRef()
 for j in range(g.GetGeometryCount()):
  polygon=g.GetGeometryRef(j)
  for k in range(1,polygon.GetGeometryCount()):
   hole=ogr.Geometry(ogr.wkbPolygon);hole.AddGeometry(polygon.GetGeometryRef(k));area=hole.GetArea()
   if 10000<area<1000000 and(best is None or area>best[0]):best=(area,feature.ExportToJson(),hole.ExportToJson(),feature.GetFID())
if best is None:raise ValueError('no matching actual source hole; do not substitute a synthetic case')
out=root/'data/intermediate/stage3/coastline-proof-source.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'source_gpkg':'data/processed/context/context.gpkg','source_layer':'water','source_fid':best[3],'source_feature':json.loads(best[1]),'hole_geometry':json.loads(best[2]),'hole_area_m2':best[0],'crs':'EPSG:32118'}))
