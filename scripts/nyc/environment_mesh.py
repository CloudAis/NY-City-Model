"""Reference-only GLB environment layers with actual geometry and per-feature identity."""
import json
import struct
import numpy as np
from shapely.geometry import shape, Polygon
from .buildings import triangulate
from .coordinates import LocalFrame, metric_to_geographic, projected_vertices_to_local


def glb(features, origin, lift, colour, fill=False, points=False):
    frame=LocalFrame.at(*metric_to_geographic(*origin),0)
    lines=[];line_ids=[];triangles=[];tri_ids=[];dots=[];dot_ids=[]
    for feature,f in enumerate(features):
        g=shape(f["geometry_metric"])
        geometries=list(g.geoms)if hasattr(g,"geoms")else[g]
        for part in geometries:
            if part.geom_type=="Point":
                dots.append([part.x,part.y]);dot_ids.append(feature)
            elif part.geom_type in ["LineString","LinearRing"]:
                c=list(part.coords)
                for a,b in zip(c,c[1:]):lines.extend([a[:2],b[:2]]);line_ids.extend([feature]*2)
            elif isinstance(part,Polygon):
                for ring in [part.exterior,*part.interiors]:
                    c=list(ring.coords)
                    for a,b in zip(c,c[1:]):lines.extend([a[:2],b[:2]]);line_ids.extend([feature]*2)
                if fill and f.get("fill_allowed",True):
                    for tri in triangulate(part):triangles.extend([p[:2]for p in tri]);tri_ids.extend([feature]*3)
    blob=bytearray();views=[];accessors=[];primitives=[];clouds=[]
    def buf(data,target=None):
        blob.extend(b"\0"*(-len(blob)%4));start=len(blob);blob.extend(data)
        views.append({"buffer":0,"byteOffset":start,"byteLength":len(data),**({"target":target}if target else{})})
        return len(views)-1
    def attr(data,kind,dtype,component):
        a=np.asarray(data,dtype=dtype);v={"bufferView":buf(a.tobytes(),34962),"componentType":component,"type":kind,"count":len(a)}
        if kind=="VEC3":v.update(min=a.min(axis=0).tolist(),max=a.max(axis=0).tolist())
        accessors.append(v);return len(accessors)-1
    for xy,ids,mode in [(triangles,tri_ids,4),(lines,line_ids,1),(dots,dot_ids,0)]:
        if not xy:continue
        enu=projected_vertices_to_local(xy,lift,frame)
        p=(enu[:,[0,2,1]]*[1,1,-1]).astype("<f4");clouds.append(p)
        attrs={"POSITION":attr(p,"VEC3","<f4",5126),"_FEATURE_ID_0":attr(ids,"SCALAR","<u4",5125)}
        indices=np.arange(len(p),dtype="<u4")
        accessors.append({"bufferView":buf(indices.tobytes(),34963),"componentType":5125,"type":"SCALAR","count":len(indices)})
        primitives.append({"attributes":attrs,"indices":len(accessors)-1,"mode":mode,"material":0,
            "extensions":{"EXT_mesh_features":{"featureIds":[{"attribute":0,"featureCount":len(features),"propertyTable":0,"label":"feature"}]}}})
    if not clouds:return None
    props={};schema={}
    for key in ["id","kind","name","source_period","vertical_state"]:
        data=bytearray();offsets=[0]
        for f in features:data.extend(str(f.get(key)or"unknown").encode());offsets.append(len(data))
        props[key]={"values":buf(data),"stringOffsets":buf(np.asarray(offsets,dtype="<u4").tobytes()),"stringOffsetType":"UINT32"}
        schema[key]={"type":"STRING"}
    p=np.vstack(clouds);lo=p.min(axis=0);hi=p.max(axis=0)
    a=[float(lo[0]),float(-hi[2]),float(lo[1])];b=[float(hi[0]),float(-lo[2]),float(hi[1])]
    c=[(x+y)/2 for x,y in zip(a,b)];h=[max(.1,(y-x)/2)for x,y in zip(a,b)]
    bounds=c+[h[0],0,0,0,h[1],0,0,0,h[2]]
    obj={"asset":{"version":"2.0","generator":"NYC environment projection-reference7"},
      "extensionsUsed":["EXT_mesh_features","EXT_structural_metadata","KHR_materials_unlit"],
      "extensions":{"EXT_structural_metadata":{"schema":{"id":"environment","classes":{"feature":{"properties":schema}}},
       "propertyTables":[{"class":"feature","count":len(features),"properties":props}]}},
      "buffers":[{"byteLength":len(blob)}],"bufferViews":views,"accessors":accessors,
      "materials":[{"name":"explicit_reference_NOT_physical_surface","pbrMetallicRoughness":{"baseColorFactor":colour,"metallicFactor":0,"roughnessFactor":1},"doubleSided":True,"extensions":{"KHR_materials_unlit":{}}}],
      "meshes":[{"primitives":primitives}],"nodes":[{"mesh":0}],"scenes":[{"nodes":[0]}],"scene":0,
      "extras":{"frame":frame.manifest(),"physical_world_surface":False,"canonical_height_m":None,
       "visual_reference_ellipsoid_height_m":lift,"lift_is_only_draw_order":True,
       "no_ground_or_deck_datum_conversion":True,"source_features":len(features)}}
    j=json.dumps(obj,separators=(",",":")).encode();j+=b" "*(-len(j)%4);blob.extend(b"\0"*(-len(blob)%4))
    result=struct.pack("<4sII",b"glTF",2,28+len(j)+len(blob))+struct.pack("<II",len(j),0x4e4f534a)+j+struct.pack("<II",len(blob),0x004e4942)+blob
    return result,frame.manifest(),bounds
