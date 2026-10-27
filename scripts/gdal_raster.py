"""Run with /usr/bin/python3: inspect actual GDAL raster metadata and retain missing cells."""
import argparse,json
from pathlib import Path
import numpy as np
from osgeo import gdal
gdal.UseExceptions()
p=argparse.ArgumentParser();p.add_argument('--file',required=True);p.add_argument('--output',required=True);a=p.parse_args()
ds=gdal.Open(a.file);band=ds.GetRasterBand(1);sr=ds.GetSpatialRef()
if ds.RasterCount!=1:raise ValueError('a single-band bare-earth DEM is required')
arr=band.ReadAsArray().astype(np.float32);tiff_values=arr.copy();tiff_zero_count=int((arr==0).sum());mask=band.GetMaskBand().ReadAsArray()!=0;valid=mask&np.isfinite(arr)
nodata=band.GetNoDataValue()
if nodata is not None and np.isfinite(nodata):valid&=arr!=nodata
lerc_path=Path(a.output).with_name(Path(a.output).name+'-lerc.json')
if not lerc_path.exists():raise ValueError('LERC validity mask required; untagged TIFF zeros may be NoData')
lerc=json.loads(lerc_path.read_text());export=json.loads(Path(lerc['exportMetadata']).read_text());gt=ds.GetGeoTransform();extent=export['extent']
expected=[extent['xmin'],extent['ymax'],extent['xmax'],extent['ymin']];actual=[gt[0],gt[3],gt[0]+ds.RasterXSize*gt[1],gt[3]+ds.RasterYSize*gt[5]]
if any(abs(x-y)>1e-5 for x,y in zip(expected,actual)):raise ValueError('LERC and TIFF grids do not share a georeference')
arr=np.fromfile(lerc['valuesFile'],dtype='<f4').reshape(ds.RasterYSize,ds.RasterXSize);valid=np.fromfile(lerc['maskFile'],dtype=np.uint8).reshape(arr.shape)!=0;valid&=np.isfinite(arr)
max_difference=float(np.max(np.abs(tiff_values[valid]-arr[valid])))if valid.any()else None
if max_difference is not None and max_difference>.1:raise ValueError('same-request TIFF/LERC valid samples differ beyond 0.10m; do not mix captures')
arr[~valid]=np.nan
out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);np.save(out.with_suffix('.npy'),arr)
metadata={'raster':a.file,'height_and_mask_source':lerc['source'],'lerc_mask_applied':True,'lerc_info':lerc,'tiff_zero_count':tiff_zero_count,'tiff_zero_but_lerc_missing':int(((tiff_values==0)&(~valid)).sum()),'real_zero_valid_cells':int(((arr==0)&valid).sum()),'maximum_valid_tiff_lerc_difference_m':max_difference,'tiff_mask_problem':'Absent TIFF mask makes some NoData appear as zero; corrected using actual LERC mask','driver':ds.GetDriver().ShortName,'size':[ds.RasterXSize,ds.RasterYSize],'geotransform':ds.GetGeoTransform(),'crs_wkt':sr.ExportToWkt()if sr else None,'authority':[sr.GetAuthorityName(None),sr.GetAuthorityCode(None)]if sr else None,'data_axis_to_srs_axis_mapping':sr.GetDataAxisToSRSAxisMapping()if sr else None,'band_unit_actual':band.GetUnitType()or None,'band_metadata':band.GetMetadata(),'nodata':None if nodata is None else float(nodata)if np.isfinite(nodata)else str(nodata),'valid_cells':int(valid.sum()),'missing_cells':int((~valid).sum()),'minimum_valid':float(arr[valid].min())if valid.any()else None,'maximum_valid':float(arr[valid].max())if valid.any()else None,'numpy_file':str(out.with_suffix('.npy')),'gdal_version':gdal.VersionInfo(),'numpy_version':np.__version__,'vertical_datum_from_file':None,'note':'Actual TIFF georeference plus actual LERC heights/mask; unit and datum established only by explicit source evidence.'}
out.with_suffix('.json').write_text(json.dumps(metadata,indent=2));print(json.dumps({k:metadata[k]for k in ['driver','size','authority','band_unit_actual','nodata','valid_cells','missing_cells','minimum_valid','maximum_valid']}))
