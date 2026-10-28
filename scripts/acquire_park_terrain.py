"""Two real park DEM crops, separate NAVD88 inspection; never assign ellipsoid Z."""
import json, subprocess, urllib.parse
import numpy as np
from shapely.geometry import shape
from nyc.download import ROOT, Downloader, atomic_json, sha
from nyc.terrain import BareEarthRaster
from nyc.coordinates import metric_to_geographic


def main():
    catalog=json.loads((ROOT/'data/raw/stage3/catalog/nys-elevation-services.json').read_text())
    s=next(s for s in catalog['services'] if s['name']=='NYC_TopoBathymetric_2017_1_meter' and s['type']=='ImageServer')
    base='https://elevation.its.ny.gov/arcgis/rest/services/'+s['name']+'/'+s['type']
    evidence=json.loads((ROOT/'data/raw/stage3/catalog/NYC_TopoBathymetric_2017_1_meter.json').read_text())
    if 'Units converted to meters by NYS' not in evidence['description'] or 'bare earth digital elevation model' not in evidence['description']:raise ValueError('DEM unit/surface evidence changed')
    parks=json.loads((ROOT/'assets/environment/parks-source.json').read_text())['features']
    downloader=Downloader(timeout=40,retries=2,max_bytes=16*1024**2)
    specs=[];datasets=[]
    for f in parks:
        id={'Central Park':'central-park','Prospect Park':'prospect-park'}[f['name']]
        bounds=list(shape(f['geometry']).bounds)
        params={'f':'json','bbox':','.join(map(str,bounds)),'bboxSR':4326,'imageSR':32118,'size':'257,257','format':'tiff','pixelType':'F32','interpolation':'RSP_BilinearInterpolation','noDataInterpretation':'esriNoDataMatchAny'}
        meta=downloader.get(base+'/exportImage?'+urllib.parse.urlencode(params),f'data/raw/stage7/terrain/{id}-export.json')
        export=json.loads(meta.read_text());tif=downloader.get(export['href'],f'data/raw/stage7/terrain/{id}.tif','binary')
        lm=downloader.get(base+'/exportImage?'+urllib.parse.urlencode({**params,'format':'lerc'}),f'data/raw/stage7/terrain/{id}-lerc-export.json')
        lexport=json.loads(lm.read_text());lerc=downloader.get(lexport['href'],f'data/raw/stage7/terrain/{id}.lerc','binary')
        if lexport['extent']!=export['extent']:raise ValueError('height and mask extents differ')
        prefix=ROOT/f'data/intermediate/stage7/terrain/{id}';prefix.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run(['node','--input-type=module','-e',"import Lerc from 'lerc';import fs from 'node:fs';const b=fs.readFileSync(process.argv[1]);const d=Lerc.decode(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength));if(d.width!==257||d.height!==257||d.pixels.length!==1||d.dimCount!==1)throw Error('DEM shape');let v=Buffer.alloc(d.width*d.height*4);for(let i=0;i<d.pixels[0].length;i++)v.writeFloatLE(d.pixels[0][i],i*4);fs.writeFileSync(process.argv[2]+'.f32',v);fs.writeFileSync(process.argv[2]+'.mask',Buffer.from(d.mask??new Uint8Array(d.width*d.height).fill(1)));",str(lerc),str(prefix)],cwd=ROOT,check=True)
        info=json.loads(subprocess.check_output(['gdalinfo','-json',str(tif)],text=True))
        if info['coordinateSystem']['wkt'].find('ID["EPSG",32118]')<0:raise ValueError('actual exported CRS is not32118')
        values=np.fromfile(str(prefix)+'.f32',dtype='<f4').reshape(257,257)
        mask=np.fromfile(str(prefix)+'.mask',dtype='u1').reshape(257,257);values[mask==0]=np.nan
        np.save(str(prefix)+'.npy',values)
        spec={'id':id,'surface_kind':'bare_earth_dem','request_bbox_wgs84':bounds,'raster':str(tif.relative_to(ROOT)),'sha256':sha(tif),'masked_raster':str(lerc.relative_to(ROOT)),'masked_sha256':sha(lerc),'export_metadata':str(meta.relative_to(ROOT)),'lerc_export_metadata':str(lm.relative_to(ROOT)),'source_service':base,'vertical_units':'metre','vertical_datum':'NAVD88','geoid_model':'GEOID12B','source_horizontal_frame':'unresolved genericNAD83 vs NAD83(2011)','source_capture_period':['2017-05-03','2017-07-26'],'source_description_evidence':'data/raw/stage3/catalog/NYC_TopoBathymetric_2017_1_meter.json','processing':'actual257x257 server bilinear resampling; LERC validity mask; display step2; not native resolution'}
        metadata={'authority':['EPSG','32118'],'geotransform':info['geoTransform'],'numpy_file':str(prefix.relative_to(ROOT))+'.npy','lerc_mask_applied':True,'height_and_mask_source':spec['masked_raster']}
        atomic_json(str(prefix)+'.json',metadata);raster=BareEarthRaster(str(prefix)+'.json',spec);lod=raster.lod(2)
        cx,cy=lod['local_origin_projected_m'];x,y=raster.coordinate(0,0);xx,yy=raster.coordinate(256,256);metric_bounds=[min(x,xx),min(y,yy),max(x,xx),max(y,yy)]
        samples=[]
        for row in range(0,257,32):
            for col in range(0,257,32):
                h=float(values[row,col])
                if not np.isfinite(h):continue
                x,y=raster.coordinate(row,col);samples.append({'local_m':[x-cx,y-cy,h],'height_m':h,'datum':'NAVD88','longitude_latitude_deg':list(metric_to_geographic(x,y))})
        scene={'schema_version':1,'id':id,'scene_kind':'local_projected_orthometric_inspector','world_placement_allowed':False,'datum_issue':'service/index realization conflict, no geoid or fixed offset applied','terrain':lod,'water':[],'footprints':[],'ground_samples':samples,'source':spec,'vertical_exaggeration':1,'full_city_coverage':False,'park_boundary_source':f['id'],'lake_water_level':'unknown; no fabricated lake surface','context_reference':'world reference layers remain separate; terrain has no invented park paths/furniture'}
        atomic_json(ROOT/f'assets/environment/terrain/{id}.json',scene)
        datasets.append({'id':id,'terrain':f'../environment/terrain/{id}.json','bounds_metric_m':metric_bounds,'valid_dem_samples':int(np.isfinite(values).sum()),'height_range_navd88_m':[float(np.nanmin(values)),float(np.nanmax(values))]});specs.append(spec)
        print('PARK DEM',id,datasets[-1],flush=True)
    atomic_json(ROOT/'data/manifests/stage7/park-dem.json',specs)
    old=json.loads((ROOT/'assets/foundation/manifest.json').read_text())
    old['datasets']+=datasets;old['scope']='six existing source crops plus two full park bounding extents; separate NAVD88 scenes'
    atomic_json(ROOT/'assets/environment/terrain-manifest.json',old)


if __name__=='__main__':main()
