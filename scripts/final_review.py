"""Fresh stratified source-to-output checks; administrative evidence is separate from survey accuracy."""
import json,sqlite3,csv,math
from collections import Counter,OrderedDict
from pathlib import Path
import numpy as np
from shapely.geometry import shape,Polygon,MultiLineString
from shapely.ops import transform
from pyproj import Transformer
from nyc.download import ROOT,atomic_json,sha,now
from nyc.normalize import esri_polygon
from nyc.coordinates import geographic_to_metric,ecef_to_geographic
from nyc.buildings import triangulate
from audit_buildings import read_glb,array


def main():
    out=ROOT/'reports/stage10';selection=json.loads((out/'review-selection.json').read_text())['records'];db=sqlite3.connect('file:'+str(ROOT/'data/processed/building-stage4/city/associations.sqlite')+'?mode=ro&immutable=1',uri=True)
    targets={e['record']['id']for e in selection};owners={}
    for b in json.loads((ROOT/'assets/buildings-city/manifest.json').read_text())['boroughs']:
        for t in json.loads((ROOT/'assets/buildings-city'/b['index']).read_text()):
            for id in t['feature_ids']:
                if id in targets:owners[id]=ROOT/'assets/buildings-city'/b['id']/(t['id']+'-strict.glb')
    caches={k:OrderedDict()for k in ['raw','glb']}
    def cached(kind,key,loader):
        c=caches[kind]
        if key in c:v=c.pop(key);c[key]=v;return v
        v=loader();c[key]=v
        if len(c)>8:c.popitem(last=False)
        return v
    records=[];errors=[];strata=Counter();maxima={'raw_to_metric_m':0.,'source_to_gpu_outline_m':0.,'height_hypothesis_encoding_m':0.,'triangulation_area_m2':0.};maxobjects={}
    for e in selection:
        r=e['record'];id=r['id'];m,stored=db.execute('select metadata,geometry from objects where id=?',(id,)).fetchone();m=json.loads(m);g=shape(r['geometry']);strata[r['borough']+':'+e['selection_category']]+=1
        if json.loads(stored)!=r['geometry']:raise ValueError('normalized geometry changed')
        p=ROOT/r['raw_record']['path']
        def loadraw():
            if sha(p)!=r['raw_record']['sha256']:raise ValueError('raw SHA changed')
            return json.loads(p.read_text())
        page=cached('raw',str(p),loadraw);f=next(f for f in page['features']if f['attributes']['OBJECTID']==r['source_object_id']);sr=f['geometry'].get('spatialReference')or page['spatialReference'];wkid=sr.get('latestWkid')or sr['wkid']
        _,fixed,_=esri_polygon(f['geometry']['rings']);projected=transform(Transformer.from_crs(wkid,32118,always_xy=True).transform,fixed);delta=projected.hausdorff_distance(g)
        row={'id':id,'bin':r.get('bin'),'borough':r['borough'],'stratum':e['selection_category'],'source_version':'2026-10-27-city','raw_record':r['raw_record'],'source_parts':m['polygon_parts'],'source_holes':m['interior_rings'],'source_feature_code':m['feature_code'],'source_construction_year':r.get('construction_year'),'source_height_raw_ft':m['relative_height_raw_ft'],'canonical_height_m':m['canonical_height_m'],'source_footprint_equals_processed':True,'raw_to_metric_pipeline_deviation_m':delta,'current_physical_status':'unknown','source_observation_date':r.get('observation_date'),'current_roof_status':'unknown','current_facade_status':'unknown','independent_position_error_m':None,'independent_footprint_error_m':None,'independent_height_error_m':None,'unverified_reason':m['reasons']}
        if r['placeholder']:
            row['output_excluded_as_official_placeholder']=True;records.append(row);continue
        tile=owners[id]
        obj,data=cached('glb',str(tile),lambda:read_glb(tile));feature=obj['extras']['feature_ids'].index(id);matrix=np.array(obj['extras']['local_frame']['enu_to_ecef_column_major']).reshape((4,4),order='F');vertices=[]
        for prim in obj['meshes'][0]['primitives']:
            pos=array(obj,data,prim['attributes']['POSITION']);ids=array(obj,data,prim['attributes']['_FEATURE_ID_0']).flatten();ix=array(obj,data,prim['indices']).flatten()
            if len(ix)and ix.max()>=len(pos):raise ValueError('index outside vertex range')
            if prim['mode']!=1:raise ValueError('strict outline unexpectedly contains body or roof')
            selected=pos[ids==feature];enu=selected[:,[0,2,1]]*np.array([1,-1,1]);ecef=(matrix[:3,:3]@enu.T).T+matrix[:3,3]
            for world in ecef:
                lon,lat,h=ecef_to_geographic(*world);vertices.append(geographic_to_metric(lon,lat))
        lines=MultiLineString([vertices[i:i+2]for i in range(0,len(vertices),2)]);gpu=lines.hausdorff_distance(g.boundary)
        if gpu>.1 or delta>.1:errors.append({'id':id,'kind':'pipeline geometry deviation','raw_m':delta,'gpu_m':gpu})
        ps=list(g.geoms)if g.geom_type=='MultiPolygon'else[g];area=max(abs(sum(Polygon(t).area for t in triangulate(p))-p.area)for p in ps)
        row.update({'strict_output':str(tile.relative_to(ROOT)),'strict_feature_index':feature,'source_to_gpu_outline_deviation_m':gpu,'triangulation_test_area_delta_m2':area,'test_triangulation_is_not_generated_roof':True,'part_ids':m['part_ids'],'reality_accuracy_not_measured':True})
        # Existing estimated open envelope can be checked against its explicit assumption;
        # never call this canonical height or real building body verification.
        hpath=tile.with_name(tile.name.replace('-strict.glb','-hypothesis.glb'));hg,hdata=cached('glb',str(hpath),lambda:read_glb(hpath));hyp=m.get('height_hypothesis_m');world_heights=[];bad_normals=0
        for prim in hg['meshes'][0]['primitives']:
            pos=array(hg,hdata,prim['attributes']['POSITION']);ids=array(hg,hdata,prim['attributes']['_FEATURE_ID_0']).flatten();ix=array(hg,hdata,prim['indices']).flatten()
            if len(ix)and ix.max()>=len(pos):raise ValueError('hypothesis index outside vertex range')
            enu=pos[ids==feature][:,[0,2,1]]*np.array([1,-1,1]);ecef=(matrix[:3,:3]@enu.T).T+matrix[:3,3]
            world_heights.extend(ecef_to_geographic(*v)[2]for v in ecef)
            if prim['mode']==4:
                mask=array(hg,hdata,prim['attributes']['_FEATURE_ID_0']).flatten()[ix].reshape((-1,3))[:,0]==feature;tris=pos[ix].reshape((-1,3,3))[mask];norm=array(hg,hdata,prim['attributes']['NORMAL'])[ix].reshape((-1,3,3))[mask,0]
                if len(tris):bad_normals+=int(np.sum(np.sum(np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0])*norm,axis=1)<=0))
        herr=abs(max(world_heights)-min(world_heights)-(hyp or 0));row['hypothesis_height_span_encoding_error_m']=herr;row['hypothesis_is_not_verified_body']=True;row['inverted_hypothesis_triangles']=bad_normals
        if bad_normals or herr>.01:errors.append({'id':id,'kind':'hypothesis index/normal/span error'})
        for name,value in [('raw_to_metric_m',delta),('source_to_gpu_outline_m',gpu),('height_hypothesis_encoding_m',herr),('triangulation_area_m2',area)]:
            if value>maxima[name]:maxima[name]=value;maxobjects[name]=id
        records.append(row)
        if len(records)%30==0:print('FINAL_REVIEW',len(records),flush=True)
    atomic_json(out/'object-review.json',records)
    summary={'at_utc':now(),'sample_count':len(records),'strata':dict(strata),'max_pipeline_values':maxima,'max_pipeline_objects':maxobjects,'errors':errors,'independent_surveyed_geometry_samples':0,'independent_as_built_height_samples':0,'reality_max_error_m':None,'source_input_fidelity_only':True,'canonical_height_checked_as_known':0,'roof_reality_verified':0,'current_facade_reality_verified':0,'current_status_confirmed':0,'interpretation':'>=200 actual objects rechecked against retained raw source and originalGLB; DOB evidence separately supports identity/work history, not as-built geometric accuracy'}
    atomic_json(out/'review-summary.json',summary)
    with(out/'object-review.csv').open('w',newline='')as f:
        keys=['id','bin','borough','stratum','source_feature_code','source_height_raw_ft','canonical_height_m','raw_to_metric_pipeline_deviation_m','source_to_gpu_outline_deviation_m','hypothesis_height_span_encoding_error_m','current_physical_status','current_roof_status','current_facade_status'];w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows({k:r.get(k)for k in keys}for r in records)
    print('REVIEW_COMPLETE',len(records),'errors',len(errors),'max',maxima)
    if len(records)<200 or errors:raise SystemExit(1)


if __name__=='__main__':main()
