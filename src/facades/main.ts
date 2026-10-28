import {Viewer,EllipsoidTerrainProvider,Color,Cartesian3,Cartesian2,DirectionalLight,Cesium3DTileset,
 Cesium3DTileStyle,BoundingSphere,HeadingPitchRange,ScreenSpaceEventHandler,ScreenSpaceEventType,
 SceneTransforms,Matrix4} from 'cesium';
import {referencePosition,localEnuToWorld} from '../geo/coordinates';
import type {Manifest,Area,Building,Facade,Street} from './types';
import 'cesium/Build/Cesium/Widgets/widgets.css';
import './style.css';
window.CESIUM_BASE_URL=new URL('./cesium/',document.baseURI).href;
const $=(id:string)=>document.getElementById(id)!;
const esc=(x:unknown)=>String(x??'未知').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
document.getElementById('app')!.innerHTML=`<header><a href="index.html">NYC / 来源档案</a><span>06 · ORDINARY BUILDINGS</span><a href="landmarks.html">地标检视 ↗</a></header>
<aside><p class="eyebrow">12 WINDOWS INTO THE CITY</p><h1>一条街，<br>逐面核对。</h1><p>不把正面复制到背面。<br>资料年代、遮挡和未知，留在每一面。</p>
<div class="metrics"><div><b id="area-count">—</b><span>真实研究范围</span></div><div><b id="source-count">—</b><span>来源建筑</span></div><div><b id="verified-count">0</b><span>现状立面完成</span></div></div>
<label>样区<select id="area"></select></label><p id="theme"></p>
<fieldset><legend>表示模式</legend><p id="mode">证据模式 · 仅已知来源轮廓</p><label class="check"><input type="checkbox" id="history">查看1936年历史立面片段</label><p>须明确开启。四栋各用自己的照片区域；不是2026现状、完整体量或地面配准。未知像素用中性色遮罩。</p><label class="check"><input type="checkbox" id="boundary" checked>显示明确样区边界</label><p>没有程序化随机补全，也没有共享砖材冒充逐楼复刻。</p></fieldset>
<section><h2>固定观察路径</h2><div id="path" class="views"></div><button id="walk">依次检查机位</button><p id="path-note"></p></section>
<section><h2>建筑与立面证据</h2><label>来源对象<select id="building"></select></label><div id="building-info"></div><div id="face-evidence"></div><div id="faces"></div></section>
<details><summary>统计口径与来源</summary><div id="coverage"></div><p>分母是来源实体与俯视边界的候选边，含可能共墙；不是已实测物理立面数。主题是样区筛选目的，不按年代或地块用途推定每栋外观。</p><a href="datasets/facades/manifest.json" target="_blank" rel="noopener">完整清单 ↗</a><button id="reference">查看已取得的原始参考</button></details></aside>
<main><div id="globe"></div><div id="banner">正在读取真实样区清单…</div><div id="loading"><progress></progress><span id="load-text">本地资料读取中…</span></div><div id="error" role="alert" hidden></div><div id="selected"></div><div id="base-note">轮廓在椭球显示参考面；地面基准未解决。未知楼高不生成墙体。</div></main>
<footer><span id="status">载入中</span><button id="collapse" aria-expanded="true">收起面板</button></footer>
<dialog id="reference-dialog"><button id="close-reference">关闭</button><h2>真实参考，保留年代。</h2><div class="reference-actions"><button id="photo">1936年街段照片</button><button id="drawing">仅4号的测绘图</button></div><img id="reference-image" alt="Grove Street HABS原始参考的缩小预览"><p id="credit"></p><p>HABS 原创政府摄影/测绘图；公有领域条款已读取。照片：Arnold Moses，1936-08-25。原始TIFF、SHA、裁切控制点和遮罩处理在本地清单中保留。图纸日期未独立确认，不能用一张4号图纸代表其余三栋。</p><a href="https://www.loc.gov/item/ny0381/" target="_blank" rel="noopener">Library of Congress · 原始记录 ↗</a></dialog>`;
const viewer=new Viewer('globe',{baseLayer:false,baseLayerPicker:false,terrainProvider:new EllipsoidTerrainProvider(),
 geocoder:false,animation:false,timeline:false,homeButton:false,navigationHelpButton:false,sceneModePicker:false,
 fullscreenButton:false,infoBox:false,selectionIndicator:false,skyBox:false,skyAtmosphere:false,
 requestRenderMode:true,maximumRenderTimeChange:Infinity});
viewer.scene.globe.show=false;viewer.scene.backgroundColor=Color.fromCssColorString('#dbe1df');
viewer.scene.fog.enabled=false;viewer.scene.highDynamicRange=false;viewer.scene.postProcessStages.bloom.enabled=false;
viewer.scene.light=new DirectionalLight({direction:new Cartesian3(-.45,-.5,-.74),color:Color.WHITE,intensity:1.4});
if(viewer.scene.sun)viewer.scene.sun.show=false;if(viewer.scene.moon)viewer.scene.moon.show=false;
viewer.resolutionScale=.9;viewer.scene.screenSpaceCameraController.enableCollisionDetection=false;
let manifest:Manifest,area:Area,street:Street,outline:Cesium3DTileset|undefined,history:Cesium3DTileset|undefined;
let selected:Building|undefined,selectedFace:Facade|undefined,generation=0,historyGeneration=0,flight=0;
let outlineLoads=0,historyLoads=0,cameraFlying=false,view='overview',walking=false,walkToken=0;
const errors:string[]=[];const root='datasets/facades/';
const historyOn=()=>($('history') as HTMLInputElement).checked;
async function get<T>(path:string):Promise<T>{const r=await fetch(new URL(root+path,document.baseURI));if(!r.ok)throw new Error(path+': HTTP '+r.status);return r.json();}
function fail(e:unknown){const message=String(e);errors.push(message);$('error').hidden=false;$('error').textContent=message;$('loading').hidden=true;}
viewer.scene.renderError.addEventListener((_scene:unknown,error:unknown)=>{cameraFlying=false;fail(error);});
function updateMode(){
 $('mode').textContent=historyOn()?'历史参考模式 · 1936年，局部照片面':'证据模式 · 仅已知来源轮廓';
 $('banner').textContent=historyOn()?'1936历史片段 · 4个独立照片面，非完整建筑 / 非2026现状':area.summary.name+' · 真实轮廓，未知外观留白';
 $('path-note').textContent=historyOn()?'背面检查会显示缺口，不会复制正面。近景门廊、栏杆与屋顶实体尚未完成。':'机位和中性日光固定。当前轮廓没有已核验楼高，不能据此验收窗格或街墙。';
 const stops=historyOn()?street.fixed_path:area.fixed_observation_path;
 $('path').innerHTML=stops.map(s=>`<button data-view="${s.id}" aria-pressed="${view===s.id}">${esc(s.label)}</button>`).join('');
 $('path').querySelectorAll<HTMLButtonElement>('button').forEach(b=>b.onclick=()=>{walking=false;walkToken++;void camera(b.dataset.view!);});
}
function fly(destination:Cartesian3,direction:Cartesian3,up:Cartesian3,animate:boolean){
 const token=++flight;cameraFlying=true;
 viewer.camera.flyTo({destination,orientation:{direction,up},duration:animate?.45:0,
  complete:()=>{if(token===flight)cameraFlying=false;},cancel:()=>{if(token===flight)cameraFlying=false;}});
 viewer.scene.requestRender();
}
async function camera(id:string,animate=true){
 view=id;
 if(historyOn()){
  const p=street.fixed_path.find(s=>s.id===id)??street.fixed_path[0];
  const dest=localEnuToWorld(street.frame,p.enu_camera),target=localEnuToWorld(street.frame,p.enu_target);
  const origin=localEnuToWorld(street.frame,[0,0,0]),upPoint=localEnuToWorld(street.frame,[0,0,1]);
  fly(dest,Cartesian3.normalize(Cartesian3.subtract(target,dest,new Cartesian3()),new Cartesian3()),
   Cartesian3.normalize(Cartesian3.subtract(upPoint,origin,new Cartesian3()),new Cartesian3()),animate);
 }else{
  const b=area.summary.bbox,centre=referencePosition([(b[0]+b[2])/2,(b[1]+b[3])/2]);
  const stop=area.fixed_observation_path.find(p=>p.id===id)??area.fixed_observation_path.at(-1)!;
  const radius=area.summary.id==='manhattan-grove'?stop.range_m*.25:stop.range_m;
  const token=++flight;cameraFlying=true;
  viewer.camera.flyToBoundingSphere(new BoundingSphere(centre,15),{offset:new HeadingPitchRange(stop.azimuth_deg*Math.PI/180,stop.pitch_deg*Math.PI/180,radius),duration:animate?.45:0,complete:()=>{if(token===flight)cameraFlying=false;},cancel:()=>{if(token===flight)cameraFlying=false;}});
 }
 document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===id)));
}
function showBuilding(id:string){
 selected=area.buildings.find(b=>b.id===id);selectedFace=undefined;if(!selected)return;
 $('face-evidence').replaceChildren();
 ($('building') as HTMLSelectElement).value=selected.id;
 const h=selected.archival_front;
 $('building-info').innerHTML=`<p class="stable-id">${esc(selected.id)}</p><p>BIN ${esc(selected.bin)} · BBL ${esc(selected.base_bbl)}<br>现状立面：0 / ${selected.facades.length}候选边；楼高未知。</p>${h?`<p class="archive-note">有1936年正面片段；其余方向仍未知。照片平面与当前来源前沿宽度差 ${h.width_conflict_m.toFixed(3)}m，非实测误差，未强行拉伸对齐。</p>`:'<p>未取得逐面照片；材料、窗格、入口和设备均未知。</p>'}`;
 $('faces').innerHTML=selected.facades.map(f=>`<button class="face" data-face="${esc(f.id)}"><span>${f.outward_azimuth_degrees.toFixed(0)}° · ${f.width_projected_m.toFixed(2)}m 候选边</span><small>${f.historical_evidence?'1936部分正面证据 / 现状未知':'现状未知 / 未概括材料'}</small></button>`).join('');
 $('faces').querySelectorAll<HTMLButtonElement>('[data-face]').forEach(b=>b.onclick=()=>{
  selectedFace=selected!.facades.find(f=>f.id===b.dataset.face);
  $('selected').textContent=selectedFace?selectedFace.id+' · 材料、窗格、楼层、檐口、入口、门廊、阳台、消防梯与设备：现状均未知':'';
  const h=selectedFace?.historical_evidence;
  $('face-evidence').innerHTML=h?`<p class="archive-note">此候选边有${esc(h.date)}部分正面资料，现状仍未知。<br>外墙：${esc(h.material.value)}<br>窗格：仅原图可见开口推导；下部入口被遮挡。<br>门廊、栏杆和屋顶设备尚无完整度量几何，未生成。</p>`:'<p>此候选边九项构件均无逐面证据；未使用共享概括材料或程序化细节。</p>';
 });
 $('selected').textContent=selected.id+' · 当前整栋外观未核验';
}
async function enableHistory(){
 const token=++historyGeneration;
 if(!historyOn()){
  if(history){viewer.scene.primitives.remove(history);history=undefined;}
  historyLoads=0;walking=false;walkToken++;updateMode();await camera('overview');return;
 }
 if(area.summary.id!=='manhattan-grove')return;
 try{
  $('loading').hidden=false;$('load-text').textContent='载入四个不同的1936年照片片段…';
  const model=await Cesium3DTileset.fromUrl(new URL(root+manifest.history_tileset,document.baseURI).href);
  if(token!==historyGeneration||!historyOn()){model.destroy();return;}
  history=model;model.tileLoad.addEventListener(()=>{historyLoads++;$('loading').hidden=true;});
  model.tileFailed.addEventListener((e:{message:string})=>fail(e.message));viewer.scene.primitives.add(model);
  updateMode();await camera('front');
 }catch(e){fail(e);}
}
async function choose(id:string){
 const token=++generation;historyGeneration++;walking=false;walkToken++;cameraFlying=false;outlineLoads=0;historyLoads=0;
 for(const t of [outline,history])if(t)viewer.scene.primitives.remove(t);
 outline=undefined;history=undefined;selected=undefined;selectedFace=undefined;viewer.entities.removeAll();
 ($('history') as HTMLInputElement).checked=false;($('history') as HTMLInputElement).disabled=id!=='manhattan-grove';
 $('loading').hidden=false;$('error').hidden=true;
 try{
  const summary=manifest.areas.find(a=>a.id===id)!;const details=await get<Area>(summary.details);
  if(token!==generation)return;area=details;$('theme').textContent=summary.category+' · 样区研究主题，单楼用途另待核验';
  const b=summary.bbox;
  viewer.entities.add({id:'research-boundary',polyline:{positions:[[b[0],b[1]],[b[2],b[1]],[b[2],b[3]],[b[0],b[3]],[b[0],b[1]]].map(p=>referencePosition(p,.7)),width:2,material:Color.fromCssColorString('#a77a37')},show:($('boundary')as HTMLInputElement).checked});
  ($('building')as HTMLSelectElement).replaceChildren(...area.buildings.map(b=>new Option((b.archival_front?'1936前面资料 · ':'')+b.id,b.id)));
  showBuilding(area.buildings.find(b=>b.id==='nyc:footprints:doitt:233256')?.id??area.buildings[0].id);
  $('coverage').innerHTML=`<p>本范围：${summary.building_denominator}个来源实体 / ${summary.facade_candidate_denominator}条候选边。<br>现状外观核验0；完整现状街段0。<br>全项目12范围，${manifest.unique_source_buildings}个唯一来源对象。</p>`;
  const model=await Cesium3DTileset.fromUrl(new URL(root+summary.tileset,document.baseURI).href);
  if(token!==generation){model.destroy();return;}
  outline=model;model.style=new Cesium3DTileStyle({color:"color('#285264')"});
  model.tileLoad.addEventListener(()=>{outlineLoads++;$('loading').hidden=true;$('status').textContent=summary.name+' · 已加载真实轮廓';});
  model.tileFailed.addEventListener((e:{message:string})=>fail(e.message));viewer.scene.primitives.add(model);
  view='overview';updateMode();await camera('overview',false);
 }catch(e){if(token===generation)fail(e);}
}
const picker=new ScreenSpaceEventHandler(viewer.scene.canvas);
picker.setInputAction((e:{position:Cartesian2})=>{const p=viewer.scene.pick(e.position);if(p&&typeof p.getProperty==='function'){const id=String(p.getProperty('id'));if(area.buildings.some(b=>b.id===id))showBuilding(id);}},ScreenSpaceEventType.LEFT_CLICK);
$('area').onchange=()=>void choose(($('area')as HTMLSelectElement).value);
$('building').onchange=()=>showBuilding(($('building')as HTMLSelectElement).value);
$('history').onchange=()=>void enableHistory();
$('boundary').onchange=()=>{const e=viewer.entities.getById('research-boundary');if(e)e.show=($('boundary')as HTMLInputElement).checked;viewer.scene.requestRender();};
$('walk').onclick=async()=>{walking=!walking;const token=++walkToken;if(!walking)return;const stops=historyOn()?street.fixed_path:area.fixed_observation_path;for(const stop of stops){if(token!==walkToken)return;await camera(stop.id);await new Promise(r=>setTimeout(r,1100));}if(token===walkToken)walking=false;};
$('collapse').onclick=()=>{const closed=$('app').classList.toggle('collapsed');$('collapse').textContent=closed?'展开面板':'收起面板';$('collapse').setAttribute('aria-expanded',String(!closed));viewer.resize();viewer.scene.requestRender();};
const dialog=$('reference-dialog')as HTMLDialogElement;
$('reference').onclick=()=>{($('reference-image')as HTMLImageElement).src=root+'grove-1936/source-photo.jpg';$('credit').textContent=street.credit;dialog.showModal();};
$('close-reference').onclick=()=>dialog.close();
$('photo').onclick=()=>{($('reference-image')as HTMLImageElement).src=root+'grove-1936/source-photo.jpg';};
$('drawing').onclick=()=>{($('reference-image')as HTMLImageElement).src=root+'grove-1936/source-drawing.jpg';};
async function init(){try{[manifest,street]=await Promise.all([get<Manifest>('manifest.json'),get<Street>('grove-1936/street.json')]);$('area-count').textContent=String(manifest.area_count);$('source-count').textContent=String(manifest.unique_source_buildings);($('area')as HTMLSelectElement).replaceChildren(...manifest.areas.map(a=>new Option(a.name,a.id)));await choose(manifest.areas[0].id);}catch(e){fail(e);}}
if(new URLSearchParams(location.search).has('diagnostics'))Object.defineProperty(window,'__NYC_FACADES__',{value:{snapshot:()=>({
 area:area?.summary.id,outlineLoads,historyLoads,mode:historyOn()?'historical-reference':'evidence',
 currentVerified:manifest?.current_verified_facades,completedStreets:manifest?.current_complete_streets,
 procedural:manifest?.procedural_facades,historyLoaded:!!history,outlineLoaded:!!outline,
 sourceBuildingCount:area?.buildings.length,selected:selected?.id,selectedFace:selectedFace?.id,
 facadeCandidates:selected?.facades.length,view,cameraFlying,errors:[...errors],
 primitiveCount:viewer.scene.primitives.length,dataSources:viewer.dataSources.length,entities:viewer.entities.values.length,
 bloom:viewer.scene.postProcessStages.bloom.enabled,worldGroundRegistered:false,
 historyFrame:street?.frame,cameraWorld:[viewer.camera.positionWC.x,viewer.camera.positionWC.y,viewer.camera.positionWC.z],
 historicalPickPoints:street?.fronts.flatMap(f=>{const p=SceneTransforms.worldToWindowCoordinates(viewer.scene,localEnuToWorld(street.frame,f.pick_point_local_enu_m));return p?[{id:f.building_id,x:p.x,y:p.y}]:[];})??[],
 pickPoints:selected?.facades.slice(0,12).flatMap(f=>{const p=f.endpoints_lon_lat;const q=SceneTransforms.worldToWindowCoordinates(viewer.scene,referencePosition([(p[0][0]+p[1][0])/2,(p[0][1]+p[1][1])/2],.25));return q?[{x:q.x,y:q.y}]:[];})??[]
 })}});
void init();
