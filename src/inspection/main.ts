import {Viewer,EllipsoidTerrainProvider,Color,Cartesian2,Cartesian3,Cartographic,Math as CMath,
 Cesium3DTileset,Cesium3DTileStyle,ScreenSpaceEventHandler,ScreenSpaceEventType,HeadingPitchRange,
 BoundingSphere,JulianDate,Matrix4,CameraEventType,SceneTransforms} from 'cesium';
import {referencePosition,geodesicMetres,degrees} from '../geo/coordinates';
import {movement,stableId,validateBookmark,MIN_WORLD_HEIGHT,MAX_WORLD_HEIGHT,type Bookmark,type Layers} from './core';
import {search,byId,type BuildingRecord} from './search';
import 'cesium/Build/Cesium/Widgets/widgets.css';
import './style.css';
window.CESIUM_BASE_URL=new URL('./cesium/',document.baseURI).href;
type Preset={id:string;name:string;kind:string;borough:string;lon:number;lat:number;heading:number;pitch:number;range_m:number;layers:Record<string,{state:string;features:number;tileset?:string;scope?:string}>;context:string};
type Manifest={observations:Preset[];parks:{tileset:string};walks:{id:string;available:boolean;allowed_triangles:number}[];global_vertical_registered:false};
type LayerEntry={key:string;model?:Cesium3DTileset;state:string;loaded:number;pending:number;processing:number;failures:number;message:string;url:string};
const $=(id:string)=>document.getElementById(id)!;
const esc=(v:unknown)=>String(v??'未知').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
const labels:Record<string,string>={manhattan:'曼哈顿',brooklyn:'布鲁克林',queens:'皇后区',bronx:'布朗克斯','staten-island':'史泰登岛'};
const layerNames:Record<string,string>={buildings:'建筑资料（当前为来源轮廓）',roads:'道路面投影',sidewalk:'人行道投影',median:'中央分隔带',water:'水系与岸线',parks:'真实公园边界',transport:'桥梁 / 隧道口投影',piers:'码头 / 海堤投影',rail:'铁路层级参考（无轨条）','rail-structure':'车站 / 入口投影',trees:'2015–2016树木点（非树冠）',outlines:'观察区原始轮廓',evidence:'证据状态着色'};
const layers:Layers={buildings:true,roads:true,sidewalk:false,median:false,water:true,parks:true,transport:true,piers:true,rail:false,'rail-structure':false,trees:false,outlines:false,evidence:false};
document.getElementById('inspection-app')!.innerHTML=`<header><a href="index.html">NYC / 可追溯城市</a><span>07 + 08 · SPACE / INSPECTION</span><button id="collapse" aria-expanded="true">收起面板</button></header>
<aside><h1>观察城市，<br>也核对依据。</h1><form id="search-form"><label for="query">建筑查询</label><div class="search-row"><input id="query" placeholder="真实名称、地址、BIN、ID" autocomplete="off"><button type="submit">查找</button></div><select id="borough"><option value="">五区 · 全部</option>${Object.entries(labels).map(([id,n])=>`<option value="${id}">${n}</option>`).join('')}</select></form><div id="search-status">全市来源索引读取中…</div><div id="results"></div>
<section><label>观察预设<select id="preset"></select></label><div class="toolbar"><button id="city-reset">全城概览</button><button id="camera-reset">相机复位</button><button id="return-selected">返回选中</button></div><label>模式<select id="mode"><option value="city">全城概览</option><option value="orbit">环绕 · 当前中心</option><option value="top">俯视</option><option value="fly">自由飞行 · WASD / QE</option><option value="walk">受限地面检查 · NAVD88</option></select></label><div id="walk-controls" hidden><select id="walk-area"></select><p>仅八个真实DEM局部范围（含两公园）；禁止道路、桥面/桥下、隧道与楼内。使用地面层，不向高处桥面吸附。</p></div><button id="cancel-flight">取消飞行 / Esc</button><p id="camera-note">世界视图距椭球参考面至少800m；真实楼体与地面未完成配准。</p></section>
<details open><summary>图层与画质</summary><div id="layers">${Object.entries(layerNames).map(([id,n])=>`<label><input type="checkbox" data-layer="${id}" ${layers[id]?'checked':''}>${n}</label>`).join('')}<button id="open-terrain">真实地形 / 地面检查</button></div><label>画质<select id="quality"><option value="low">低 · 0.65×</option><option value="medium" selected>中 · 0.9×</option><option value="high">高 · 1×</option></select></label><p>固定中性日光，无浓雾/泛光；没有日期驱动日照或艺术夜景。</p></details>
<section><h2>选中对象</h2><div id="details">点击或悬停查看稳定ID；缺失名称不补造。</div></section>
<details><summary>读取与量测</summary><div class="toolbar"><button id="point-tool">点位读取</button><button id="measure-tool">两点量距</button><button id="clear-measure">清空量测</button></div><div id="measurement">全球只量水平测地距离；空间距离/高差须有同基准高度。</div></details>
<details><summary>相机书签</summary><input id="bookmark-name" maxlength="100" placeholder="书签名称"><div class="toolbar"><button id="save-bookmark">保存</button><button id="export-bookmarks">导出</button><label class="button">导入<input id="import-bookmarks" type="file" accept="application/json" hidden></label></div><div id="bookmarks"></div><p>记录位置、朝向、模式、图层、画质与保存时间；照明时间为null，表示固定中性光。</p></details>
<details><summary>来源与诊断</summary><p>NYC OTI / Open Data；NYC Parks；NYS ITS 2017 DEM。下载日不等于观测日。当前桥面标高、全球地形和楼体基底仍未解决。</p><a href="datasets/environment/bridges.json" target="_blank" rel="noopener">五座桥梁资料与未知项 ↗</a><a href="datasets/environment/manifest.json" target="_blank" rel="noopener">环境范围 / 来源入口 ↗</a><a href="landmarks.html">地标局部检视 ↗</a><a href="facades.html">逐立面资料 ↗</a><div id="layer-status"></div></details></aside>
<main><div id="globe"></div><iframe id="local-view" title="局部NAVD88地面检查" hidden></iframe><div id="banner">全城概览 · 来源轮廓按距离加载</div><div id="loading" role="status"><progress></progress><span id="load-text">读取本地清单…</span></div><div id="notice" role="status"></div><div id="hover"></div><div id="error" role="alert" hidden></div><button id="screenshot">导出带署名截图</button><div id="reference-note">全球：WGS84椭球展示参考；道路/桥梁是投影，不是已核验实体表面。</div></main>
<footer><span id="status">载入中</span><span>拖动旋转 · 右键平移 · 双指缩放/平移 · Esc取消</span></footer>`;
const viewer=new Viewer('globe',{baseLayer:false,baseLayerPicker:false,terrainProvider:new EllipsoidTerrainProvider(),geocoder:false,animation:false,timeline:false,homeButton:false,navigationHelpButton:false,sceneModePicker:false,fullscreenButton:false,infoBox:false,selectionIndicator:false,skyBox:false,skyAtmosphere:false,requestRenderMode:true,maximumRenderTimeChange:Infinity,contextOptions:{webgl:{preserveDrawingBuffer:true}}});
viewer.scene.globe.baseColor=Color.fromCssColorString('#d8ded8');viewer.scene.backgroundColor=Color.fromCssColorString('#d8ded8');
// No unregistered physical ground is rendered underneath reference polygons.
viewer.scene.globe.show=false;
viewer.scene.globe.enableLighting=false;viewer.scene.fog.enabled=false;viewer.scene.highDynamicRange=false;viewer.scene.postProcessStages.bloom.enabled=false;viewer.clock.shouldAnimate=false;viewer.shadows=false;
if(viewer.scene.sun)viewer.scene.sun.show=false;if(viewer.scene.moon)viewer.scene.moon.show=false;
viewer.resolutionScale=.9;viewer.scene.screenSpaceCameraController.minimumZoomDistance=800;viewer.scene.screenSpaceCameraController.maximumZoomDistance=250000;
const ssc=viewer.scene.screenSpaceCameraController;ssc.inertiaSpin=0;ssc.inertiaTranslate=0;ssc.inertiaZoom=0;
ssc.tiltEventTypes=[CameraEventType.MIDDLE_DRAG,CameraEventType.PINCH];viewer.scene.canvas.tabIndex=0;
let manifest:Manifest,preset:Preset,mode='city',quality='medium',selectedId:string|null=null,selected:BuildingRecord|null=null;
let generation=0,selectionGeneration=0,queryGeneration=0,flightGeneration=0,flying=false,lastTime=0,searchController:AbortController|undefined;
let inputFrame=0,hoverId:string|null=null,dragged=false,dragUntil=0,worldClampCount=0,loadedTotal=0,unloadedTotal=0,tool='select',lastExportCredit='';
let lastClickedBuildingId:string|null=null;
let bookmarkList:Bookmark[]=[],measurementPoints:number[][]=[],lastPick:unknown=null,localWalkState:Bookmark['localWalk'];
let pendingWalkRestore:Bookmark['localWalk'];
let walkRequest=0;
const snapshotRequests=new Map<number,(state:Bookmark['localWalk'])=>void>();
const bank=new Map<string,LayerEntry>(),held=new Set<string>(),pointers=new Map<number,{x:number;y:number;startX:number;startY:number;type:string}>(),errors:string[]=[],expectedFailures:string[]=[];
let touchGesture:{distance:number;x:number;y:number}|undefined;
const iframe=$('local-view')as HTMLIFrameElement;
const cityPaths=['manhattan','brooklyn','queens','bronx','staten-island'];
const statusText=(t:string)=>{$('notice').textContent=t;};
async function json<T>(path:string):Promise<T>{const r=await fetch(new URL('datasets/'+path,document.baseURI));if(!r.ok)throw new Error(path+': HTTP '+r.status);return r.json();}
function fail(e:unknown){const t=String(e);errors.push(t);$('error').hidden=false;$('error').textContent=t;}
viewer.scene.renderError.addEventListener((_s:unknown,e:unknown)=>{clearInput();flying=false;fail(e);});
function stats(){
 const list=[...bank.values()],pending=list.reduce((n,v)=>n+v.pending+v.processing,0),fetching=list.filter(v=>v.state==='loading').length;
 $('loading').hidden=!fetching&&!pending;
 $('load-text').textContent=`资料请求${fetching} · 等待瓦片${pending} · 实际解析${loadedTotal}（无预估百分比）`;
 $('status').textContent=mode==='walk'?'局部NAVD88地面检查 / 禁止未核验结构':'已解析'+loadedTotal+'个真实瓦片 · 释放'+unloadedTotal+'次';
 $('layer-status').innerHTML=list.map(v=>`<p><b>${esc(v.key)}</b> · ${esc(v.state)} · 实际解析${v.loaded}${v.failures?' · 失败'+v.failures:''}<small>${esc(v.message)}</small></p>`).join('');
}
function visible(key:string){
 if(key.startsWith('city:'))return layers.buildings&&viewer.camera.positionCartographic.height<7500&&(!($('borough')as HTMLSelectElement).value||key.slice(5)===($('borough')as HTMLSelectElement).value);
 return !!layers[key];
}
function applyStyle(){
 const condition=(id:string)=>'${id} === '+JSON.stringify(id);
 for(const [key,entry]of bank){const m=entry.model;if(!m)continue;m.show=visible(key)&&mode!=='walk';
  if(key.startsWith('city:'))m.style=new Cesium3DTileStyle({color:{conditions:[
   ...(selectedId?[[condition(selectedId),"color('#d5a54c')"]]:[]),
   ...(hoverId?[[condition(hoverId),"color('#f1d7a3')"]]:[]),
   ['true',layers.evidence?"color('#9e8764')":"color('#365b66')"]]}});
 }
 viewer.scene.requestRender();stats();
}
async function loadLayer(key:string,url:string,token:number,message=''){
 const entry:LayerEntry={key,state:'loading',loaded:0,pending:0,processing:0,failures:0,message,url};bank.set(key,entry);stats();
 try{
  const model=await Cesium3DTileset.fromUrl(new URL('datasets/'+url,document.baseURI).href,{maximumScreenSpaceError:quality==='high'?6:quality==='low'?24:12,cacheBytes:48*1024*1024,maximumCacheOverflowBytes:16*1024*1024});
  if((key!=='parks'&&!key.startsWith('city:')&&token!==generation)||bank.get(key)!==entry){model.destroy();return;}
  entry.model=model;entry.state=visible(key)?'ready':'hidden';
  model.tileLoad.addEventListener(()=>{entry.loaded++;loadedTotal++;entry.state=visible(key)?'ready':'hidden';stats();});
  model.tileUnload.addEventListener(()=>{unloadedTotal++;stats();});
  model.loadProgress.addEventListener((n:number,m:number)=>{entry.pending=n;entry.processing=m;stats();});
  model.tileFailed.addEventListener((e:{url:string;message:string})=>{entry.failures++;entry.state='partial-failure';entry.message=e.message;expectedFailures.push(e.url);statusText('单瓦片加载失败，其余内容可继续浏览：'+e.url);stats();});
  viewer.scene.primitives.add(model);applyStyle();
 }catch(e){if(bank.get(key)===entry){entry.state='failed';entry.failures++;entry.message=String(e);expectedFailures.push(url);statusText(key+'资料加载失败，其他图层继续可用');stats();}}
}
function removeEnvironment(){
 for(const [key,e]of bank)if(!key.startsWith('city:')&&key!=='parks'){
  if(e.model)viewer.scene.primitives.remove(e.model);bank.delete(key);
 }
}
function cancelFlight(){++flightGeneration;viewer.camera.cancelFlight();flying=false;clearInput();statusText('飞行已取消');}
function configureMode(value:string){
 mode=value;($('mode')as HTMLSelectElement).value=value;
 ssc.enableLook=value==='fly';ssc.enableRotate=value!=='fly';ssc.enableTranslate=value!=='fly';ssc.enableTilt=value!=='top';ssc.lookEventTypes=CameraEventType.LEFT_DRAG;
 $('walk-controls').hidden=value!=='walk';applyStyle();
}
function fly(target:number[],range:number,heading:number,pitch:number,duration=1.1){
 clearInput();viewer.camera.cancelFlight();const token=++flightGeneration;flying=true;
 const centre=referencePosition(target),r=Math.max(1400,range);
 viewer.camera.flyToBoundingSphere(new BoundingSphere(centre,10),{offset:new HeadingPitchRange(CMath.toRadians(heading),CMath.toRadians(pitch),r),duration,
  complete:()=>{if(token===flightGeneration){flying=false;applyStyle();}},cancel:()=>{if(token===flightGeneration)flying=false;}});
}
function cityReset(){
 exitWalk();configureMode('city');selectedId=null;selected=null;hoverId=null;applyStyle();
 const token=++flightGeneration;flying=true;viewer.camera.flyTo({destination:Cartesian3.fromDegrees(-74.035,40.705,80000),orientation:{heading:0,pitch:-Math.PI/2,roll:0},duration:1,complete:()=>{if(token===flightGeneration)flying=false;},cancel:()=>{if(token===flightGeneration)flying=false;}});
 $('banner').textContent='全城概览 · 放大后加载既有五区来源轮廓；环境仅25观察区';
}
async function choosePreset(id:string){
 exitWalk();const p=manifest.observations.find(v=>v.id===id);if(!p)return;preset=p;
 ($('preset')as HTMLSelectElement).value=id;const token=++generation;removeEnvironment();configureMode('orbit');
 $('banner').textContent=p.name+' · 全球参考图层，非已配准路面/桥体';
 for(const [name,spec]of Object.entries(p.layers)){
  if(name==='parks')continue;
  if(spec.tileset)void loadLayer(name,'environment/'+spec.tileset,token,spec.scope??'真实来源几何投影，高程未解决');
  else bank.set(name,{key:name,state:'no-data',loaded:0,pending:0,processing:0,failures:0,message:'此观察范围没有已取得记录',url:''});
 }
 stats();fly([p.lon,p.lat],p.range_m,p.heading,p.pitch);
}
function recordHtml(r:BuildingRecord){
 return `<b>${esc(r.name??r.address??'来源对象 · 名称未知')}</b><p class="id">${esc(r.id)}</p><p>${esc(labels[r.borough])} · BIN ${esc(r.bin)}<br>地址：${esc(r.address)}<br>来源相对屋顶数值：${r.relative_height_raw_ft??'未知'} feet（种类未核）<br>规范楼高 / 基底：未知<br>屋顶：${esc(r.roof_status)} · 立面：${esc(r.facade_status)}<br>观测日：${esc(r.observation_date)}<br>记录编辑：${esc(r.last_edited_at)}<br>抓取版本：${esc(r.source_version)}</p><small>位置、轮廓来源明确，不代表整栋已复刻。原始引用：${esc(r.raw_record.path)}<br>SHA ${esc(r.raw_record.sha256)}</small>`;
}
async function selectBuilding(id:string,travel=false){
 const token=++selectionGeneration;selectedId=id;selected=null;applyStyle();$('details').textContent='读取稳定来源ID：'+id;
 try{
  const r=await byId(id);if(token!==selectionGeneration)return;
  if(!r){selectedId=null;$('details').textContent='没有这个建筑来源ID；场景保持可用。';applyStyle();return;}
  selected=r;$('details').innerHTML=recordHtml(r);applyStyle();
  if(travel){
   const filter=$('borough')as HTMLSelectElement;if(filter.value&&filter.value!==r.borough)filter.value=r.borough;
   exitWalk();configureMode('orbit');const b=r.bbox;
   const diagonal=geodesicMetres(degrees(b[0],b[1]),degrees(b[2],b[3]));
   fly([(b[0]+b[2])/2,(b[1]+b[3])/2],Math.max(1600,diagonal*2),25,-55);
   if(r.state==='excluded_placeholder')statusText('此来源是占位记录，未生成可见建筑。');
  }
 }catch(e){if(token===selectionGeneration){$('details').textContent='建筑档案加载失败：'+String(e);statusText('查询失败不改变其他图层');}}
}
async function runSearch(){
 const token=++queryGeneration;searchController?.abort();searchController=new AbortController();
 const q=($('query')as HTMLInputElement).value,borough=($('borough')as HTMLSelectElement).value;
 $('search-status').textContent=q.trim()?'正在读取真实索引…':'输入真实名称、地址、BIN≥4位或ID:来源号';$('results').replaceChildren();
 if(!q.trim())return;
 try{
  const records=await search(q,borough,searchController.signal);if(token!==queryGeneration)return;
  $('search-status').textContent=records.length?'匹配'+records.length+'条（当前仅少量来源有名称/地址）':'没有匹配的已取得名称、地址或编号；未补造';
  $('results').innerHTML=records.map(r=>`<button data-id="${esc(r.id)}"><b>${esc(r.name??r.address??r.bin??r.id)}</b><small>${esc(labels[r.borough])} · ${esc(r.id)}</small></button>`).join('');
  $('results').querySelectorAll<HTMLButtonElement>('[data-id]').forEach(b=>b.onclick=()=>void selectBuilding(b.dataset.id!,true));
 }catch(e){if(token===queryGeneration&&!searchController.signal.aborted)$('search-status').textContent='索引读取失败：'+String(e);}
}
function globalPoint(position:Cartesian2){
 const hit=viewer.camera.pickEllipsoid(position,viewer.scene.globe.ellipsoid);if(!hit)return null;
 const p=Cartographic.fromCartesian(hit);return [CMath.toDegrees(p.longitude),CMath.toDegrees(p.latitude),0];
}
const picker=new ScreenSpaceEventHandler(viewer.scene.canvas);
viewer.screenSpaceEventHandler.removeInputAction(ScreenSpaceEventType.LEFT_DOUBLE_CLICK);
picker.setInputAction((e:{position:Cartesian2})=>{
 if(performance.now()<dragUntil||dragged)return;
 if(tool!=='select'){
  const p=globalPoint(e.position);lastPick=p;if(!p){$('measurement').textContent='此处无地球参考面点位';return;}
  if(tool==='point')$('measurement').textContent=`导航经度${p[0].toFixed(5)}° / 纬度${p[1].toFixed(5)}°；真实高程未知（不是0m地面）`;
  else{measurementPoints.push(p);if(measurementPoints.length>2)measurementPoints=[p];
   if(measurementPoints.length===2){const d=geodesicMetres(degrees(...measurementPoints[0].slice(0,2)as[number,number]),degrees(...p.slice(0,2)as[number,number]));$('measurement').textContent=`水平测地距离≈${Math.round(d)}m；空间距离 / 高差不可用：同基准真实高度未解决。`;}else $('measurement').textContent='第一点已读，点击第二点。';
  }return;
 }
 const picked=viewer.scene.pick(e.position),id=stableId(picked);
 lastClickedBuildingId=id;
 if(id)void selectBuilding(id);
 else if(picked?.id?.id?.startsWith?.('preset:'))void choosePreset(picked.id.id.slice(7));
 else if(picked&&typeof picked.getProperty==='function'){
  try{$('details').innerHTML=`<b>${esc(picked.getProperty('name')??'环境来源对象')}</b><p class="id">${esc(picked.getProperty('id'))}</p><p>类型：${esc(picked.getProperty('kind'))}<br>年代：${esc(picked.getProperty('source_period'))}<br>高程：${esc(picked.getProperty('vertical_state'))}</p>`;}catch{}
 }
},ScreenSpaceEventType.LEFT_CLICK);
let hoverAt=0;
picker.setInputAction((e:{endPosition:Cartesian2})=>{
 if(pointers.size||performance.now()-hoverAt<80)return;hoverAt=performance.now();
 const id=stableId(viewer.scene.pick(e.endPosition));if(id!==hoverId){hoverId=id;$('hover').textContent=id??'';applyStyle();}
},ScreenSpaceEventType.MOUSE_MOVE);
function clearInput(){held.clear();pointers.clear();touchGesture=undefined;ssc.enableInputs=true;lastTime=0;if(inputFrame)cancelAnimationFrame(inputFrame);inputFrame=0;iframe.contentWindow?.postMessage({type:'nyc-walk-pause'},location.origin);}
viewer.scene.canvas.addEventListener('blur',clearInput);
function inputTick(time:number){
 inputFrame=0;if(mode!=='fly'||!held.size){lastTime=0;return;}
 const dt=lastTime?(time-lastTime)/1000:0;lastTime=time;
 if(dt>1){clearInput();return;}
 const axes=[Number(held.has('KeyW'))-Number(held.has('KeyS')),Number(held.has('KeyD'))-Number(held.has('KeyA')),Number(held.has('KeyE'))-Number(held.has('KeyQ'))];
 const d=movement(viewer.camera.positionCartographic.height,dt,axes,held.has('ShiftLeft')||held.has('ShiftRight'));
 viewer.camera.moveForward(d[0]);viewer.camera.moveRight(d[1]);viewer.camera.moveUp(d[2]);viewer.scene.requestRender();inputFrame=requestAnimationFrame(inputTick);
}
function touchState(){const p=[...pointers.values()].filter(p=>p.type==='touch');return p.length===2?{distance:Math.hypot(p[1].x-p[0].x,p[1].y-p[0].y),x:(p[0].x+p[1].x)/2,y:(p[0].y+p[1].y)/2}:undefined;}
viewer.scene.canvas.addEventListener('pointerdown',e=>{
 viewer.scene.canvas.focus();pointers.set(e.pointerId,{x:e.clientX,y:e.clientY,startX:e.clientX,startY:e.clientY,type:e.pointerType});dragged=false;
 const t=touchState();if(t){touchGesture=t;ssc.enableInputs=false;held.clear();lastTime=0;}
});
viewer.scene.canvas.addEventListener('pointermove',e=>{
 const p=pointers.get(e.pointerId);if(!p)return;
 if(Math.hypot(e.clientX-p.startX,e.clientY-p.startY)>6||pointers.size>1)dragged=true;
 pointers.set(e.pointerId,{...p,x:e.clientX,y:e.clientY});
 const next=touchState();
 if(touchGesture&&next){
  const h=viewer.camera.positionCartographic.height,scale=Math.max(1,h)/Math.max(1,viewer.scene.canvas.clientHeight);
  if(next.distance>1)viewer.camera.zoomIn(h*(1-touchGesture.distance/next.distance));
  viewer.camera.moveRight(-(next.x-touchGesture.x)*scale);viewer.camera.moveUp((next.y-touchGesture.y)*scale);
  touchGesture=next;dragUntil=performance.now()+150;viewer.scene.requestRender();e.preventDefault();
 }
});
viewer.scene.canvas.addEventListener('pointerup',e=>{
 if(dragged)dragUntil=performance.now()+150;pointers.delete(e.pointerId);
 if(touchGesture&&![...pointers.values()].some(p=>p.type==='touch')){touchGesture=undefined;ssc.enableInputs=true;}
});
viewer.scene.canvas.addEventListener('pointercancel',()=>{dragUntil=performance.now()+150;dragged=false;clearInput();});
viewer.scene.canvas.addEventListener('lostpointercapture',(e)=>{if(pointers.has(e.pointerId)){dragUntil=performance.now()+150;dragged=false;clearInput();}});
addEventListener('keydown',e=>{
 if(e.code==='Escape'){cancelFlight();if(mode==='walk')exitWalk();return;}
 if(mode==='fly'&&e.target===viewer.scene.canvas&&['KeyW','KeyS','KeyA','KeyD','KeyQ','KeyE','ShiftLeft','ShiftRight'].includes(e.code)){
  e.preventDefault();held.add(e.code);if(!inputFrame){lastTime=performance.now();inputFrame=requestAnimationFrame(inputTick);}
 }
});addEventListener('keyup',e=>held.delete(e.code));addEventListener('blur',clearInput);
document.addEventListener('visibilitychange',()=>{if(document.hidden){cancelFlight();clearInput();}});
addEventListener('orientationchange',()=>{clearInput();cancelFlight();viewer.resize();});
viewer.scene.postRender.addEventListener(()=>{
 if(mode==='walk')return;const p=viewer.camera.positionCartographic;
 if(p.height<MIN_WORLD_HEIGHT-.1||p.height>MAX_WORLD_HEIGHT+.1){
  const h=Math.max(MIN_WORLD_HEIGHT,Math.min(MAX_WORLD_HEIGHT,p.height));worldClampCount++;
  viewer.camera.setView({destination:Cartesian3.fromRadians(p.longitude,p.latitude,h),orientation:{heading:viewer.camera.heading,pitch:viewer.camera.pitch,roll:viewer.camera.roll}});
 }
});
viewer.camera.changed.addEventListener(()=>{for(const [key,e]of bank)if(e.model){e.model.show=visible(key)&&mode!=='walk';if(e.state!=='partial-failure')e.state=e.model.show?'ready':'hidden';}stats();});
function setQuality(q:string){quality=q;viewer.resolutionScale=q==='low'?.65:q==='high'?1:.9;for(const e of bank.values())if(e.model)e.model.maximumScreenSpaceError=q==='low'?24:q==='high'?6:12;viewer.scene.requestRender();}
function exitWalk(){if(mode!=='walk')return;clearInput();iframe.hidden=true;iframe.src='about:blank';$('globe').hidden=false;configureMode('orbit');localWalkState=undefined;}
function enterWalk(areaId?:string){
 cancelFlight();clearInput();const id=areaId??($('walk-area')as HTMLSelectElement).value;
 if(!manifest.walks.some(w=>w.id===id&&w.available)){statusText('此区域没有可靠的局部地面碰撞，禁止漫游');return;}
 configureMode('walk');$('globe').hidden=true;iframe.hidden=false;
 iframe.src='terrain.html?embedded=1&walk=1&extended=1&area='+encodeURIComponent(id)+(new URLSearchParams(location.search).has('diagnostics')?'&diagnostics=1':'');
 $('banner').textContent=id+' · 局部2017 DEM / NAVD88检查 · 不是全球地面配准';
}
addEventListener('message',e=>{
 if(e.origin!==location.origin||e.source!==iframe.contentWindow||!e.data||typeof e.data!=='object')return;
 if(e.data.type==='nyc-walk-exit')exitWalk();
 if(e.data.type==='nyc-walk-state'){
  localWalkState=e.data.state;
  const resolve=snapshotRequests.get(e.data.requestId);if(resolve){snapshotRequests.delete(e.data.requestId);resolve(e.data.state);}
  if(pendingWalkRestore&&e.data.state?.ready&&e.data.state.area===pendingWalkRestore.area){
   iframe.contentWindow?.postMessage({type:'nyc-walk-restore',state:pendingWalkRestore},location.origin);pendingWalkRestore=undefined;
  }
 }
 if(e.data.type==='nyc-local-measurement')$('measurement').textContent=String(e.data.text??'');
});
function renderBookmarks(){
 $('bookmarks').innerHTML=bookmarkList.map((b,i)=>`<button data-bookmark="${i}">${esc(b.name)}<small>${esc(b.savedAt)} · ${esc(b.mode)}</small></button>`).join('');
 $('bookmarks').querySelectorAll<HTMLButtonElement>('[data-bookmark]').forEach(b=>b.onclick=()=>void restore(bookmarkList[Number(b.dataset.bookmark)]));
}
async function saveBookmark(){
 if(mode==='walk'){
  const id=++walkRequest;
  localWalkState=await new Promise<Bookmark['localWalk']>(resolve=>{snapshotRequests.set(id,resolve);iframe.contentWindow?.postMessage({type:'nyc-walk-snapshot',requestId:id},location.origin);setTimeout(()=>{if(snapshotRequests.delete(id))resolve(undefined);},4000);});
  if(!localWalkState){statusText('局部相机尚未就绪，书签未保存');return;}
 }
 const p=viewer.camera.positionWC,b:Bookmark={schema:1,name:($('bookmark-name')as HTMLInputElement).value.trim()||'观察书签',savedAt:new Date().toISOString(),mode,preset:preset.id,quality,layers:{...layers},camera:{position:[p.x,p.y,p.z],heading:viewer.camera.heading,pitch:viewer.camera.pitch,roll:viewer.camera.roll},selectedId,lighting:{mode:'neutral-fixed',datetime:null,note:'No solar date simulation; savedAt is record time, not observation date'},...(mode==='walk'&&localWalkState?{localWalk:localWalkState}:{})};
 validateBookmark(b);bookmarkList=[b,...bookmarkList].slice(0,12);
 try{localStorage.setItem('nyc-inspection-bookmarks-v1',JSON.stringify(bookmarkList));renderBookmarks();statusText('书签已保存，未改变世界数据');}catch(e){statusText('书签存储失败：'+String(e));}
}
async function restore(b:Bookmark){
 try{
  validateBookmark(b);cancelFlight();exitWalk();await choosePreset(b.preset);
  cancelFlight();Object.assign(layers,b.layers);quality=b.quality;($('quality')as HTMLSelectElement).value=quality;setQuality(quality);
  document.querySelectorAll<HTMLInputElement>('[data-layer]').forEach(el=>el.checked=layers[el.dataset.layer!]);
  configureMode(b.mode==='walk'?'orbit':b.mode);viewer.camera.setView({destination:Cartesian3.fromArray(b.camera.position),orientation:{heading:b.camera.heading,pitch:b.camera.pitch,roll:b.camera.roll}});
  if(b.selectedId)await selectBuilding(b.selectedId);applyStyle();
  if(b.mode==='walk'&&b.localWalk){pendingWalkRestore=b.localWalk;enterWalk(b.localWalk.area);}
  statusText('书签已恢复；来源几何未修改');
 }catch(e){statusText('书签未应用：'+String(e));}
}
function download(blob:Blob,name:string){const a=document.createElement('a'),u=URL.createObjectURL(blob);a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}
$('export-bookmarks').onclick=()=>download(new Blob([JSON.stringify({schema:1,bookmarks:bookmarkList},null,2)],{type:'application/json'}),'nyc-camera-bookmarks.json');
$('save-bookmark').onclick=()=>void saveBookmark().catch(e=>statusText('书签保存失败：'+String(e)));
$('import-bookmarks').onchange=async e=>{
 try{
  const file=(e.target as HTMLInputElement).files?.[0];if(!file)return;if(file.size>1024*1024)throw new Error('书签文件过大');
  const value=JSON.parse(await file.text());if(value.schema!==1||!Array.isArray(value.bookmarks)||value.bookmarks.length>12)throw new Error('版本或数量无效');
  const checked=value.bookmarks.map(validateBookmark);localStorage.setItem('nyc-inspection-bookmarks-v1',JSON.stringify(checked));bookmarkList=checked;renderBookmarks();statusText('合法书签已导入；相机尚未替换');
 }catch(e){statusText('导入拒绝，原书签与场景保留：'+String(e));}
};
$('screenshot').onclick=()=>{
 try{
  const source=mode==='walk'?iframe.contentDocument?.querySelector('canvas'):viewer.scene.canvas;if(!source)throw new Error('视口未就绪');
  viewer.scene.render();const out=document.createElement('canvas');out.width=source.width;out.height=source.height+70;const c=out.getContext('2d')!;
  c.drawImage(source,0,0);c.fillStyle='#edf1e8';c.fillRect(0,source.height,out.width,70);c.fillStyle='#263d46';c.font='13px sans-serif';
  lastExportCredit=mode==='walk'?'NYS ITS / NYC2017 DEM · NAVD88 local inspection; NYC Open Data · not current walkability':'NYC OTI / NYC Open Data; NYC Parks2015–2016 census; CesiumJS Apache-2.0 · reference scene';
  c.fillText(lastExportCredit,12,source.height+24);c.fillText(preset.name+' | fixed neutral light | unresolved world elevations',12,source.height+49);
  out.toBlob(b=>{if(b)download(b,'nyc-inspection-attributed.png');});
 }catch(e){statusText('截图失败：'+String(e));}
};
$('search-form').onsubmit=e=>{e.preventDefault();void runSearch();};
$('borough').onchange=()=>{void runSearch();applyStyle();};
$('preset').onchange=()=>void choosePreset(($('preset')as HTMLSelectElement).value);
$('mode').onchange=()=>{
 const v=($('mode')as HTMLSelectElement).value;if(v==='walk'){enterWalk();return;}exitWalk();configureMode(v);
 if(v==='city')cityReset();else if(v==='top')fly([preset.lon,preset.lat],preset.range_m,0,-90);
 else if(v==='orbit')fly([preset.lon,preset.lat],preset.range_m,preset.heading,preset.pitch);
};
$('walk-area').onchange=()=>{if(mode==='walk')enterWalk(($('walk-area')as HTMLSelectElement).value);};
$('open-terrain').onclick=()=>enterWalk();
$('quality').onchange=()=>setQuality(($('quality')as HTMLSelectElement).value);
$('city-reset').onclick=cityReset;$('camera-reset').onclick=()=>void choosePreset(preset.id);
$('return-selected').onclick=()=>{if(selectedId)void selectBuilding(selectedId,true);else statusText('尚未选择建筑');};
$('cancel-flight').onclick=cancelFlight;
$('collapse').onclick=()=>{const hidden=$('inspection-app').classList.toggle('collapsed');$('collapse').textContent=hidden?'展开面板':'收起面板';$('collapse').setAttribute('aria-expanded',String(!hidden));clearInput();viewer.resize();viewer.scene.requestRender();};
document.querySelectorAll<HTMLInputElement>('[data-layer]').forEach(el=>el.onchange=()=>{layers[el.dataset.layer!]=el.checked;applyStyle();});
$('point-tool').onclick=()=>{tool='point';iframe.contentWindow?.postMessage({type:'nyc-walk-tool',tool},location.origin);statusText('点击读取导航点；不把参考面当真实高程');};
$('measure-tool').onclick=()=>{tool='measure';measurementPoints=[];iframe.contentWindow?.postMessage({type:'nyc-walk-tool',tool},location.origin);statusText('点击两个点；仅同基准局部DEM提供空间距离/高差');};
$('clear-measure').onclick=()=>{tool='select';measurementPoints=[];lastPick=null;iframe.contentWindow?.postMessage({type:'nyc-walk-tool',tool},location.origin);$('measurement').textContent='量测已清空';};
new ResizeObserver(()=>{clearInput();viewer.resize();viewer.scene.requestRender();}).observe($('globe'));
async function init(){
 try{
  const [m,index]=await Promise.all([json<Manifest>('environment/manifest.json'),json<{source_records:number;named_records:number}>('inspection/search/manifest.json')]);manifest=m;preset=m.observations[0];
  ($('preset')as HTMLSelectElement).replaceChildren(...m.observations.map(p=>new Option(p.name,p.id)));
  ($('walk-area')as HTMLSelectElement).replaceChildren(...m.walks.filter(w=>w.available).map(w=>new Option(w.id+' · '+w.allowed_triangles+'可检视三角形',w.id)));
  $('search-status').textContent='已索引'+index.source_records.toLocaleString()+'条来源；有名称/地址等'+index.named_records+'条';
  for(const p of m.observations)viewer.entities.add({id:'preset:'+p.id,position:referencePosition([p.lon,p.lat],2),point:{pixelSize:5,color:Color.fromCssColorString('#ab8545')}});
  void loadLayer('parks','environment/'+m.parks.tileset,generation,'Central Park / Prospect Park完整来源边界，非植被模型');
  for(const b of cityPaths)void loadLayer('city:'+b,'buildings-city/'+b+'/strict.json',generation,'全市来源轮廓；7500m以上隐藏完整细节');
  try{const raw=JSON.parse(localStorage.getItem('nyc-inspection-bookmarks-v1')??'[]');if(Array.isArray(raw))bookmarkList=raw.slice(0,12).map(validateBookmark);}catch{statusText('旧书签无法读取；当前场景保留');}
  renderBookmarks();cityReset();await choosePreset(preset.id);
  if(new URLSearchParams(location.search).get('start')==='city')cityReset();
 }catch(e){fail(e);$('loading').hidden=true;}
}
if(new URLSearchParams(location.search).has('diagnostics'))Object.defineProperty(window,'__NYC_INSPECTION__',{value:{snapshot:()=>({
 mode,preset:preset?.id,flying,layers:{...layers},quality,selectedId,hoverId,lastClickedBuildingId,selectedRecord:selected,keys:[...held],
 cameraHeight:viewer.camera.positionCartographic.height,cameraWorld:[viewer.camera.positionWC.x,viewer.camera.positionWC.y,viewer.camera.positionWC.z],
 heading:viewer.camera.heading,pitch:viewer.camera.pitch,worldClampCount,loadedTotal,unloadedTotal,
 layerStates:[...bank.values()].map(({model,...r})=>({...r,shown:model?.show})),primitives:viewer.scene.primitives.length,
 errors:[...errors],tileFailures:[...expectedFailures],bookmarks:bookmarkList,measurementPoints,lastPick,lastExportCredit,
 worldGroundRegistered:false,cityBodyEvidence:'outline only',localWalkState,lighting:'neutral-fixed',solarDatetime:null,
 pickPoints:selected?(()=>{const b=selected!.bbox;const p=SceneTransforms.worldToWindowCoordinates(viewer.scene,referencePosition([(b[0]+b[2])/2,(b[1]+b[3])/2],.25));return p?[{x:p.x,y:p.y}]:[];})():[]
 })}});
addEventListener('pagehide',()=>{clearInput();searchController?.abort();picker.destroy();viewer.destroy();});
void init();
