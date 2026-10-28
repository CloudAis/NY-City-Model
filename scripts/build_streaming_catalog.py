"""Density-adaptive metadata hierarchy referencing every unchanged original strict GLB."""
import json,math,copy
from pathlib import Path
import numpy as np
from nyc.download import ROOT,sha,atomic_json,now


def sphere(tile):
    b=tile['boundingVolume']['box'];m=np.array(tile['transform']).reshape(4,4,order='F')
    centre=(m@np.array([*b[:3],1]))[:3]
    # Triangle inequality encloses every source OBB corner; conservative, never clips.
    radius=sum(np.linalg.norm((m[:3,:3]@np.array(b[3+i*3:6+i*3])))for i in range(3))+.01
    return centre,radius


def bounds(rows):
    lo=np.min([c-r for _,c,r in rows],axis=0);hi=np.max([c+r for _,c,r in rows],axis=0)
    centre=(lo+hi)/2;radius=max(float(np.linalg.norm(c-centre))+r for _,c,r in rows)
    return {'sphere':[*map(float,centre),radius]}


def main():
    out=ROOT/'assets/performance/city';summaries=[]
    for source in sorted((ROOT/'assets/buildings-city').glob('*/strict.json')):
        original=json.loads(source.read_text());borough=source.parent.name;rows=[];chunks=[]
        for tile in original['root']['children']:
            c,r=sphere(tile);rows.append((tile,c,r))
        def partition(part):
            metadata_bytes=sum(len(json.dumps(t,separators=(',',':')))for t,_,_ in part)
            if len(part)<=32 and metadata_bytes<=32000:
                name=f'page-{len(chunks):04}.json';children=[]
                for tile,_,_ in part:
                    leaf=copy.deepcopy(tile);leaf['content']['uri']='../../../buildings-city/'+borough+'/'+tile['content']['uri'];children.append(leaf)
                payload={'asset':original['asset'],'geometricError':500,'root':{'boundingVolume':bounds(part),'geometricError':500,'refine':'ADD','children':children}}
                atomic_json(out/borough/name,payload);chunks.append({'path':str((out/borough/name).relative_to(ROOT)),'leaves':len(part),'bytes':(out/borough/name).stat().st_size,'sha256':sha(out/borough/name)})
                return {'boundingVolume':bounds(part),'geometricError':500,'content':{'uri':name}}
            centres=np.array([c for _,c,_ in part]);axis=int(np.argmax(np.ptp(centres,axis=0)))
            ordered=sorted(part,key=lambda t:(float(t[1][axis]),t[0]['content']['uri']));mid=len(ordered)//2
            children=[partition(ordered[:mid]),partition(ordered[mid:])]
            enclosing=bounds([(None,np.array(n['boundingVolume']['sphere'][:3]),n['boundingVolume']['sphere'][3])for n in children])
            return {'boundingVolume':enclosing,'geometricError':500,'refine':'ADD','children':children}
        root=partition(rows)
        atomic_json(out/borough/'root.json',{'asset':original['asset'],'geometricError':original['geometricError'],'root':root})
        summaries.append({'borough':borough,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'original_leaf_count':len(rows),'published_leaf_count':sum(p['leaves']for p in chunks),'root':str((out/borough/'root.json').relative_to(ROOT)),'root_bytes':(out/borough/'root.json').stat().st_size,'pages':chunks})
        print('CATALOG',borough,len(rows),'leaves',len(chunks),'pages',flush=True)
    atomic_json(ROOT/'assets/performance/manifest.json',{'schema_version':9,'at_utc':now(),'algorithm':'median split by widest ECEF centre extent; <=32 original leaves/page and <=32k compact source metadata','boroughs':summaries,'geometry_modified':False,'vertices_or_ids_removed':0,'geometry_compression':'none','original_precise_models_retained':True,'original_whole_city_extent_retained':True,'processor_sha256':sha(Path(__file__))})


if __name__=='__main__':main()
