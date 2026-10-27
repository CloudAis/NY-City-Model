import {Viewer,CustomDataSource,Color,PolygonHierarchy,Cartesian3,Matrix4,Cesium3DTileset,SceneTransforms,BoundingSphere,HeadingPitchRange,Rectangle,Cartesian2,Cartographic,Entity,LabelStyle} from 'cesium';
import {degrees,geodesicMetres,localEnuToWorld,referencePosition} from '../geo/coordinates';
import type {FoundationManifest,GlobeOverlays,ContextFeature} from './types';

type Layer='water'|'roads'|'grid'|'samples'|'bounds';
const root='datasets/foundation/';
async function json<T>(path:string):Promise<T>{const r=await fetch(new URL(root+path,document.baseURI));if(!r.ok)throw new Error(`坐标基础 ${path}: ${r.status}`);return r.json();}
function polygons(f:ContextFeature):number[][][][] {return f.geometry.type==='Polygon'?[f.geometry.coordinates as number[][][]]:f.geometry.coordinates as number[][][][];}

export class FoundationLayers {
 private layers=new Map<Layer,CustomDataSource>();private generation=0;private data?:GlobeOverlays;private axes?:Cesium3DTileset;private axisLabels:Entity[]=[];private axesContentLoaded=false;private active='';private checked=new Map<Layer,boolean>();private manifest!:FoundationManifest;private north=true;private cache=new Map<string,GlobeOverlays>();
 constructor(private viewer:Viewer,private report:(error:unknown)=>void){}
 async init(){
  this.manifest=await json<FoundationManifest>('manifest.json');
  this.axes=await Cesium3DTileset.fromUrl(new URL(root+this.manifest.axes.tileset,document.baseURI).href);this.axes.show=false;this.axes.tileLoad.addEventListener(()=>{this.axesContentLoaded=true;});this.axes.tileFailed.addEventListener((e:{message:string})=>this.report(e.message));this.viewer.scene.primitives.add(this.axes);
  for(const [axis,vector]of Object.entries(this.manifest.axes.endpoints_enu_m))this.axisLabels.push(this.viewer.entities.add({id:'axis-label:'+axis,show:false,position:localEnuToWorld(this.manifest.axes.frame,vector.map(v=>v*1.12)),label:{text:axis+' · 100m诊断',font:'12px monospace',fillColor:Color.fromCssColorString('#fff0c1'),outlineColor:Color.fromCssColorString('#10242f'),outlineWidth:2,style:LabelStyle.FILL_AND_OUTLINE}}));
  for(const key of ['water','roads','grid','samples','bounds']as Layer[]){this.checked.set(key,false);const input=document.getElementById('layer-'+key)as HTMLInputElement;input.onchange=()=>{this.checked.set(key,input.checked);const ds=this.layers.get(key);if(ds)ds.show=input.checked;this.viewer.scene.requestRender();};}
  (document.getElementById('layer-axes')as HTMLInputElement).onchange=e=>this.showAxes((e.target as HTMLInputElement).checked);
  (document.getElementById('layer-north')as HTMLInputElement).onchange=e=>{this.north=(e.target as HTMLInputElement).checked;document.getElementById('north-indicator')!.hidden=!this.north;document.getElementById('metric-scale')!.hidden=!this.north;};
  document.getElementById('fit-axes')!.onclick=()=>{(document.getElementById('layer-axes')as HTMLInputElement).checked=true;this.showAxes(true);const p=Cartesian3.fromArray(this.manifest.axes.frame.origin_ecef_m);this.viewer.camera.flyToBoundingSphere(new BoundingSphere(p,130),{duration:.4,offset:new HeadingPitchRange(.42,-.55,650)});};
  document.getElementById('city-overview')!.onclick=()=>this.viewer.camera.flyTo({destination:Rectangle.fromDegrees(-74.28,40.47,-73.68,40.94),duration:.6});
  this.viewer.camera.changed.addEventListener(()=>this.updateCameraReadouts());this.viewer.camera.percentageChanged=.005;this.updateCameraReadouts();
 }
 private showAxes(show:boolean){this.axes!.show=show;for(const label of this.axisLabels)label.show=show;this.viewer.scene.requestRender();}
 async switchArea(id:string){
  const generation=++this.generation;this.active='';
  for(const ds of this.layers.values())this.viewer.dataSources.remove(ds,true);this.layers.clear();this.data=undefined;
  try{
   let data=this.cache.get(id);if(!data){data=await json<GlobeOverlays>(id+'-overlays.json');this.cache.set(id,data);}if(generation!==this.generation)return;
   const next=new Map<Layer,CustomDataSource>(),adds:Promise<CustomDataSource>[]=[];
   const make=(key:Layer)=>{const ds=new CustomDataSource(`foundation:${key}:${id}`);ds.show=false;adds.push(this.viewer.dataSources.add(ds));next.set(key,ds);return ds.entities;};
   const water=make('water');
   for(const f of data.water)for(const [part,rings]of polygons(f).entries()){
    if(!f.fill_allowed)continue;const outer=rings[0].map(p=>referencePosition(p));const holes=rings.slice(1).map(r=>new PolygonHierarchy(r.map(p=>referencePosition(p))));
    water.add({id:`${f.id}:${part}`,polygon:{hierarchy:new PolygonHierarchy(outer,holes),height:.04,material:Color.fromCssColorString('#3a91a6').withAlpha(.75)},properties:{sourceId:f.id,displayHeight:'ellipsoid reference h=0 + .04m visual lift; NOT a tide or NAVD88 conversion'}});
   }
   const roads=make('roads');for(const f of data.roads)for(const [p,rings]of polygons(f).entries())for(const [r,line]of rings.entries())roads.add({id:`${f.id}:${p}:${r}`,polyline:{positions:line.map(x=>referencePosition(x,.13)),width:1,material:Color.fromCssColorString('#9aa8a1')},properties:{sourceId:f.id,deckHeight:null,heightStatus:'2D reference outline, bridge deck unresolved; no road surface generated'}});
   const grid=make('grid');for(const [i,line]of data.grid_lines_longitude_latitude_deg.entries())grid.add({id:`grid:${i}`,polyline:{positions:line.map(p=>referencePosition(p,.18)),width:1,material:Color.fromCssColorString('#a2c4a0').withAlpha(.45)}});
   const samples=make('samples');for(const p of data.ground_samples)samples.add({id:p.id,position:referencePosition(p.longitude_latitude_deg,.8),point:{pixelSize:4,color:Color.fromCssColorString('#f8ce7b'),disableDepthTestDistance:50000},properties:{heightNavd88M:p.height_m,ecefHeightM:null,source:'real bare-earth/topobathymetric DEM; including water-bottom points; marker shows reference XY only'}});
   const bounds=make('bounds');for(const [i,t]of data.tiles.entries()){
    const b=t.box_local_enu_m,m=Matrix4.fromArray(t.transform_enu_to_ecef);const ps:Cartesian3[]=[];
    for(let k=0;k<8;k++){const v=new Cartesian3(b[0]+(k&1?1:-1)*b[3],b[1]+(k&2?1:-1)*b[7],b[2]+(k&4?1:-1)*b[11]);ps.push(Matrix4.multiplyByPoint(m,v,new Cartesian3()));}
    for(let k=0;k<8;k++)for(const bit of [1,2,4])if(!(k&bit))bounds.add({id:`bounds:${i}:${k}:${bit}`,polyline:{positions:[ps[k],ps[k|bit]],width:1.5,material:Color.fromCssColorString('#f4bf68')}});
   }
   await Promise.all(adds);
   if(generation!==this.generation){for(const ds of next.values())this.viewer.dataSources.remove(ds,true);return;}
   this.layers=next;this.active=id;this.data=data;for(const [key,ds]of next)ds.show=this.checked.get(key)??false;
   this.viewer.scene.requestRender();this.updateCameraReadouts();
  }catch(e){this.report(e);}
 }
 private updateCameraReadouts(){
  const n=document.getElementById('north-indicator');if(n)n.style.transform=`rotate(${-this.viewer.camera.heading*180/Math.PI}deg)`;
  const canvas=this.viewer.scene.canvas,y=Math.min(canvas.clientHeight-75,canvas.clientHeight*.7),x=Math.max(100,canvas.clientWidth*.5);
  const a=this.viewer.camera.pickEllipsoid(new Cartesian2(x-50,y)),b=this.viewer.camera.pickEllipsoid(new Cartesian2(x+50,y));const el=document.getElementById('metric-scale');if(!el)return;
  if(!a||!b){el.textContent='标尺：当前无椭球交点';return;}
  const aa=Cartographic.fromCartesian(a),bb=Cartographic.fromCartesian(b);const span=geodesicMetres(degrees(aa.longitude*180/Math.PI,aa.latitude*180/Math.PI),degrees(bb.longitude*180/Math.PI,bb.latitude*180/Math.PI));
  const power=10**Math.floor(Math.log10(span));const distance=[1,2,5,10].map(v=>v*power).filter(v=>v<=span).at(-1)??power;const width=Math.max(1,100*distance/span);
  el.replaceChildren();const line=document.createElement('span');line.style.width=`${width}px`;line.className='scale-line';const text=document.createElement('small');text.textContent=`${distance>=1000?distance/1000+' km':distance+' m'} · 椭球测地标尺`;el.append(line,text);
 }
 snapshot(){
  const frame=this.manifest?.axes.frame;const axesPoints=frame?Object.entries(this.manifest.axes.endpoints_enu_m).map(([axis,end])=>{const mid=localEnuToWorld(frame,end.map(v=>v*.65));const screen=SceneTransforms.worldToWindowCoordinates(this.viewer.scene,mid);const picked=screen&&this.axes?.show&&this.axesContentLoaded?this.viewer.scene.pick(screen):null;return {axis,worldMidpoint:[mid.x,mid.y,mid.z],x:screen?.x,y:screen?.y,pickedAxis:typeof picked?.getProperty==='function'?picked.getProperty('id'):null};}):[];
  return {active:this.active,globalTerrainRegistered:false,verticalBlock:this.manifest?.global_terrain_block,axisGlbLoaded:this.axesContentLoaded&&this.axes?.tilesLoaded,axisVisible:this.axes?.show??false,axesPoints,layers:Object.fromEntries([...this.layers].map(([k,v])=>[k,{show:v.show,entities:v.entities.values.length}])),dataSourceCount:this.viewer.dataSources.length,north:this.north,terrainInspection:'terrain.html',sourceGroundSamples:this.data?.ground_samples.length??0};
 }
}
