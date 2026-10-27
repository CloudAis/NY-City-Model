import {Viewer,EllipsoidTerrainProvider,Color,Cartesian2,Cartesian3,BoundingSphere,HeadingPitchRange,Cesium3DTileset,ScreenSpaceEventHandler,ScreenSpaceEventType,SceneTransforms} from 'cesium';
import {referencePosition} from '../geo/coordinates';
import 'cesium/Build/Cesium/Widgets/widgets.css';
import './style.css';
window.CESIUM_BASE_URL=new URL('./cesium/',document.baseURI).href;
type Borough={id:string;records:number;outlines:number;tiles:number;bounds_wgs84:number[];strict:string;hypothesis:string;index:string};
type Manifest={schema_version:number;source:{version:string};boroughs:Borough[];canonical_building_solids:number};
type Tile={id:string;entities:number;bounds_wgs84:number[];metadata:string};
type Evidence={id:string;bin:string|null;name:string|null;semantic_level:string;relative_height_raw_ft:number|null;height_hypothesis_m:number|null;part_ids:string[];interior_rings:number;reasons:string[];reference_pick_points:number[][];raw_record:{path:string;sha256:string};geometry_sha256:string};
const collections=[{id:'pilot-lower',title:'下城 · 真实样区',path:'buildings-pilot-lower'},{id:'pilot-midtown',title:'中城 · 真实样区',path:'buildings-pilot-midtown'},{id:'city',title:'五区 · 全部来源记录',path:'buildings-city'}];
const labels:Record<string,string>={manhattan:'曼哈顿',bronx:'布朗克斯',brooklyn:'布鲁克林',queens:'皇后区','staten-island':'史泰登岛'};
document.getElementById('app')!.innerHTML=`<header><a href="index.html">NYC / 测绘档案</a><span>04 · 建筑证据与主体检视</span><a href="terrain.html">正高地形 ↗</a></header><aside><h1>形体，须有依据。</h1><p>完整来源轮廓，不以方盒替代。<br>屋顶、基底与高度单位尚待核实。</p><label>数据范围<select id="collection">${collections.map(d=>`<option value="${d.id}">${d.title}</option>`).join('')}</select></label><label>行政区<select id="borough"></select></label><button id="fit">定位已取得的真实对象</button><fieldset><legend>表示与证据分开</legend><label class="check"><input id="hypothesis" type="checkbox">开启来源高度假设包络</label><p>默认严格模式仅显示俯视轮廓。假设包络使用来源 HEIGHT_ROOF × 0.3048，英尺种类未核实；不代表墙线、真实基底、屋顶或可靠建筑主体。无数据不补高度，屋顶未知不封顶。</p><label class="check"><input id="bounds" type="checkbox">瓦片包围框</label></fieldset><dl id="counts"></dl><section><h2>点击对象查看证据</h2><div id="details">选择一条来源轮廓或已明确标记的假设包络。</div></section><details><summary>来源、统计与缺口</summary><a href="datasets/buildings-city/sources.json" target="_blank" rel="noopener">来源与处理清单 ↗</a><a href="datasets/buildings-city/quality-report.json" target="_blank" rel="noopener">全市质量报告 ↗</a><a href="https://github.com/CityOfNewYork/nyc-geo-metadata/blob/main/Metadata/Metadata_BuildingFootprints.md" target="_blank" rel="noopener">官方字段与采集说明 ↗</a><p>来源是俯视外轮廓，不是经证实的地面墙线。2014旧模型没有当前建筑匹配；LAS/LAZ尚未取得。楼高不证明退台、塔楼、机房、立面或现状年代。</p></details></aside><main><div id="globe"></div><div id="banner" role="status">严格模式 · 真实俯视轮廓 / 未知留白</div><div id="zoom-note" hidden>全城俯视：详细轮廓暂停加载。请放大至街区，或点击定位。</div><div id="loading" role="status"><progress></progress><span id="load-text">读取本地清单…</span></div><div id="error" role="alert" hidden></div><div id="reference-note">WGS84 椭球显示参考 +0.25 m；不是实际地面。所有高度均未作为已核验世界高程。</div></main><footer><span id="status">读取中</span><button id="collapse" aria-expanded="true">收起面板</button></footer>`;
const $=(id:string)=>document.getElementById(id)!;
const esc=(x:unknown)=>String(x??'未知').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
const viewer=new Viewer('globe',{baseLayer:false,baseLayerPicker:false,terrainProvider:new EllipsoidTerrainProvider(),geocoder:false,animation:false,timeline:false,homeButton:false,navigationHelpButton:false,sceneModePicker:false,fullscreenButton:false,infoBox:false,selectionIndicator:false,skyBox:false,skyAtmosphere:false,requestRenderMode:true,maximumRenderTimeChange:Infinity});
viewer.scene.globe.baseColor=Color.fromCssColorString('#1c2c35');viewer.scene.backgroundColor=Color.fromCssColorString('#101c23');viewer.scene.globe.enableLighting=false;viewer.scene.fog.enabled=false;if(viewer.scene.sun)viewer.scene.sun.show=false;if(viewer.scene.moon)viewer.scene.moon.show=false;viewer.resolutionScale=.85;
let generation=0,collection=collections[0],manifest:Manifest,borough:Borough,tiles:Tile[]=[],tileset:Cesium3DTileset|undefined,selected:Evidence|undefined,errors:string[]=[],loadedContent=0,pending=0,mode='strict',focusEvidence:Evidence[]=[],selectionGeneration=0;
const metadata=new Map<string,Evidence[]>();let currentHighlight:{color:Color}|undefined,oldColor:Color|undefined;
async function json<T>(path:string):Promise<T>{const r=await fetch(new URL(path,document.baseURI));if(!r.ok)throw new Error(`${path}: HTTP ${r.status}`);return r.json();}
function fail(e:unknown){const s=String(e);errors.push(s);$('error').hidden=false;$('error').textContent=`载入失败：${s}。没有补造缺失数据。`;}
const base=()=>`datasets/${collection.path}/`;
function fit(){if(!tiles.length)return;const tile=[...tiles].sort((a,b)=>b.entities-a.entities||a.id.localeCompare(b.id))[0];const [w,s,e,n]=tile.bounds_wgs84;const ps=[referencePosition([w,s],100),referencePosition([e,n],100)];viewer.camera.flyToBoundingSphere(BoundingSphere.fromPoints(ps),{duration:.4,offset:new HeadingPitchRange(.15,-.73,Math.max(1100,Cartesian3.distance(ps[0],ps[1])*1.5))});}
function zoomPolicy(){if(!tileset)return;const close=viewer.camera.positionCartographic.height<7000;tileset.show=close;$('zoom-note').hidden=close;viewer.scene.requestRender();}
viewer.camera.changed.addEventListener(zoomPolicy);
function counts(){$('counts').innerHTML=`<dt>来源记录</dt><dd>${borough.records.toLocaleString()}</dd><dt>来源轮廓实体</dt><dd>${borough.outlines.toLocaleString()}</dd><dt>已核验米制主体</dt><dd>0</dd><dt>可靠屋顶 / 精细立面</dt><dd>0 / 0</dd>`;}
async function load(preserveCamera=false){
 const token=++generation;selectionGeneration++;selected=undefined;focusEvidence=[];metadata.clear();currentHighlight=undefined;oldColor=undefined;loadedContent=0;pending=0;$('loading').hidden=false;$('error').hidden=true;$('details').textContent='选择来源轮廓，查看逐项证据。';
 const path=base();mode=($('hypothesis')as HTMLInputElement).checked?'hypothesis':'strict';
 $('banner').textContent=mode==='strict'?'严格模式 · 真实俯视轮廓 / 未知留白':'假设包络 · 单位、墙线与基底未核实 / 无屋顶';$('banner').classList.toggle('hypothesis',mode==='hypothesis');
 if(tileset){viewer.scene.primitives.remove(tileset);tileset=undefined;}
 try{
  $('load-text').textContent='读取范围与对象数量…';const m=await json<Manifest>(path+'manifest.json');if(token!==generation)return;manifest=m;if(m.schema_version!==4)throw new Error('未知建筑发布版本');
  const chosen=($('borough')as HTMLSelectElement).value;borough=m.boroughs.find(d=>d.id===chosen)??m.boroughs[0];($('borough')as HTMLSelectElement).replaceChildren(...m.boroughs.map(d=>new Option(labels[d.id]??d.id,d.id,d.id===borough.id,d.id===borough.id)));counts();
  const tileRows=await json<Tile[]>(path+borough.index);if(token!==generation)return;tiles=tileRows;
  const t=await Cesium3DTileset.fromUrl(new URL(path+borough[mode as 'strict'|'hypothesis'],document.baseURI).href,{maximumScreenSpaceError:12,cacheBytes:128*1024*1024,maximumCacheOverflowBytes:64*1024*1024,enableCollision:false});
  if(token!==generation){t.destroy();return;}tileset=t;viewer.scene.primitives.add(t);t.debugShowBoundingVolume=($('bounds')as HTMLInputElement).checked;
  t.tileLoad.addEventListener(()=>{loadedContent++;$('status').textContent=`${labels[borough.id]} · 完成 ${loadedContent} 块 · 来源 ${manifest.source.version}`;});
  t.loadProgress.addEventListener((requests:number,processing:number)=>{pending=requests+processing;$('load-text').textContent=`网络请求 ${requests} / 解析 ${processing} / 完成 ${loadedContent}`;if(loadedContent&&pending===0)$('loading').hidden=true;});
  t.tileFailed.addEventListener((e:{message:string})=>fail(e.message));
  if(!preserveCamera)fit();zoomPolicy();$('load-text').textContent='等待视野内真实瓦片…';
  const seed=[...tiles].sort((a,b)=>b.entities-a.entities||a.id.localeCompare(b.id))[0];const rows=await json<{objects:Evidence[]}>(path+borough.id+'/'+seed.metadata);if(token!==generation)return;metadata.set(seed.id,rows.objects);focusEvidence=rows.objects.slice(0,24);
 }catch(e){if(token===generation){fail(e);$('loading').hidden=true;}}
}
function display(e:Evidence){
 selected=e;$('details').innerHTML=`<h3>${esc(e.name??e.bin??e.id)}</h3><code>${esc(e.id)}</code><dl><dt>语义证据等级</dt><dd>${esc(e.semantic_level)}</dd><dt>来源高度</dt><dd>${esc(e.relative_height_raw_ft)} ft · 种类未核</dd><dt>可信米制高度</dt><dd>未知</dd><dt>部件 / 内洞</dt><dd>${e.part_ids.length} / ${e.interior_rings}</dd><dt>屋顶 / 立面</dt><dd>未知 / 未取得</dd></dl><p>当前${mode==='strict'?'仅为来源轮廓':'仅为显式高度假设包络'}。没有自动生成退台、附楼、机房、屋顶或室内。</p><details><summary>处理原因与原始记录</summary><p>${e.reasons.map(esc).join('<br>')}</p><code>${esc(e.raw_record.path)}</code><code>${esc(e.raw_record.sha256)}</code><p>几何 SHA256</p><code>${esc(e.geometry_sha256)}</code></details>`;
}
const picker=new ScreenSpaceEventHandler(viewer.scene.canvas);
picker.setInputAction(async(click:{position:Cartesian2})=>{
 const token=++selectionGeneration,worldToken=generation;if(currentHighlight&&oldColor)currentHighlight.color=oldColor;currentHighlight=undefined;selected=undefined;const p=viewer.scene.pick(click.position);if(!p||typeof p.getProperty!=='function')return;const id=p.getProperty('id');if(typeof id!=='string')return;
 try{
  const filename=new URL(String(p.content?.url??p.content?._url??''),document.baseURI).pathname.split('/').pop()??'';const tileid=filename.replace(/-(strict|hypothesis)\.glb$/,'');if(!/^\d+_\d+_\d+$/.test(tileid))throw new Error('无法核对瓦片来源');
  let rows=metadata.get(tileid);if(!rows){rows=(await json<{objects:Evidence[]}>(base()+borough.id+'/'+tileid+'.json')).objects;if(worldToken!==generation||token!==selectionGeneration)return;metadata.set(tileid,rows);}
  const evidence=rows.find(r=>r.id===id);if(!evidence)throw new Error('拾取编号缺少关联表');display(evidence);oldColor=Color.clone(p.color);currentHighlight=p;p.color=Color.fromCssColorString('#edcc85');viewer.scene.requestRender();
 }catch(e){if(worldToken===generation)fail(e);}
},ScreenSpaceEventType.LEFT_CLICK);
$('fit').onclick=fit;$('collection').onchange=()=>{collection=collections.find(d=>d.id===($('collection')as HTMLSelectElement).value)!;void load();};$('borough').onchange=()=>void load();$('hypothesis').onchange=()=>void load(true);$('bounds').onchange=()=>{if(tileset){tileset.debugShowBoundingVolume=($('bounds')as HTMLInputElement).checked;viewer.scene.requestRender();}};$('collapse').onclick=()=>{const close=document.getElementById('app')!.classList.toggle('collapsed');$('collapse').textContent=close?'展开面板':'收起面板';$('collapse').setAttribute('aria-expanded',String(!close));};
if(new URLSearchParams(location.search).has('diagnostics'))Object.defineProperty(window,'__NYC_BUILDINGS__',{value:{snapshot:()=>({generation,collection:collection.id,borough:borough?.id,mode,canonicalSolids:manifest?.canonical_building_solids,records:borough?.records,outlines:borough?.outlines,loadedContent,pending,selected:selected?.id,errors:[...errors],show:tileset?.show,primitives:viewer.scene.primitives.length,cameraHeight:viewer.camera.positionCartographic.height,pickPoints:focusEvidence.flatMap(e=>e.reference_pick_points.map(ll=>{const p=SceneTransforms.worldToWindowCoordinates(viewer.scene,referencePosition(ll,.25+(mode==='hypothesis'?(e.height_hypothesis_m??0)/2:0)));return p?{id:e.id,x:p.x,y:p.y}:null;}).filter(Boolean))}),overview:()=>viewer.camera.flyTo({destination:referencePosition([-74,40.72],55000),duration:.3}),viewer}});
void load();
