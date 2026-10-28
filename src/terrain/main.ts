import {Matrix4,Cartesian3,Cartesian4} from 'cesium';
import type {FoundationManifest,OrthometricScene,TerrainTile} from '../foundation/types';
import {GroundCollider,type CollisionSpec} from '../inspection/ground';
import {localMeasurement} from '../inspection/core';
import './style.css';

const app=document.getElementById('terrain-app')!;
app.innerHTML=`<header><a href="index.html">← 纽约 · 测绘档案</a><span>真实 DEM / NAVD88 正高检视</span><button id="terrain-panel" aria-expanded="true">收起面板</button></header><aside id="terrain-controls"><div class="eyebrow">LOCAL ORTHOMETRIC INSPECTION / 03</div><h1>地面，<br>也需要证据。</h1><p class="explain">真实 2017 裸地与水底 DEM。<br>局部投影米制坐标，垂直比例 1:1。</p><label for="terrain-area">真实样区</label><select id="terrain-area"></select><div class="datum-warning"><b>NAVD88 正高 · 米</b><p>源数据 NAD83 实现仍有冲突。此场景保留原始正高，尚未叠加到地球椭球面，也未采用全城固定偏移。</p></div><div class="checks"><label><input id="terrain-surface" type="checkbox" checked>真实裸地 / 水底地形</label><label><input id="terrain-water" type="checkbox" checked>真实水系范围内的展示水面</label><label><input id="terrain-outlines" type="checkbox" checked>来源建筑轮廓投影（非建筑体量）</label><label><input id="terrain-north" type="checkbox" checked>北向与米制标尺</label><label><input id="terrain-grid" type="checkbox">100m 投影坐标网</label><label><input id="terrain-samples" type="checkbox">DEM 采样点（含水底）</label><label><input id="terrain-bounds" type="checkbox">四块局部地形边界</label></div><button id="terrain-fit">定位全部有效地形</button><div id="terrain-stats"></div><p class="explain">水面为 NAVD88 H=0m 的选定展示水位，非实时潮位。只填河流与海湾；湖塘水位未知，湿地、沙滩不当作水面填充。</p><p class="explain">黄色线是来源轮廓在 DEM 上的检视参考，不证明基础接地。没有生成楼体、桥面或室内；道路、桥面高程不足时不贴地补齐。</p><a id="terrain-source" target="_blank" rel="noopener">官方 DEM 服务 ↗</a><a href="datasets/foundation/registration.json" target="_blank" rel="noopener">检查点与配准报告 ↗</a></aside><main><canvas id="terrain-canvas" aria-label="真实地形三维视口"></canvas><div id="terrain-name">读取本地真实地形…</div><div id="terrain-north-label">N ↑</div><div id="terrain-scale"></div><div id="terrain-readout">拖动旋转 · 右键/Shift拖动平移 · 滚轮/双指缩放 · 点击地形取样</div><div id="terrain-error" role="alert" hidden></div><div id="terrain-loading" role="status">读取实际 DEM 与源水系…</div></main><footer>局部米制 / NAVD88 · 2017 采集资料 · 未解决的全球垂直配准保留阻塞</footer>`;
const $=(id:string)=>document.getElementById(id)!;const canvas=$('terrain-canvas')as HTMLCanvasElement;
const params=new URLSearchParams(location.search);
if(params.has('embedded'))app.classList.add('embedded');
canvas.tabIndex=0;
const hud=document.createElement('div');hud.id='walk-hud';hud.hidden=true;
hud.innerHTML='<b>局部 DEM 检查漫游 · NAVD88 / 2017</b><span id="walk-message"></span><div><button data-walk-key="KeyA">←</button><button data-walk-key="KeyW">↑</button><button data-walk-key="KeyS">↓</button><button data-walk-key="KeyD">→</button><button id="walk-leave">返回俯视</button></div>';
canvas.parentElement!.append(hud);
let collider:GroundCollider|undefined,walkMode=false,walkReady=false,walkBlocked=false;
const walker={position:[0,0,0],yaw:0,pitch:-.15,fov:.85},walkKeys=new Set<string>();
let localTool='point',localMeasurements:number[][]=[];
let activeLoad:AbortController|undefined,terrainDisposed=false,contextLost=false;
let walkFrame=0,walkTime=0;
const gl=canvas.getContext('webgl2',{alpha:false,antialias:true,preserveDrawingBuffer:true});if(!gl)throw new Error('需要WebGL2，未用虚构地形代替');
type Mesh={position:WebGLBuffer;normal:WebGLBuffer;indices:WebGLBuffer|null;count:number;mode:number;color:number[];offset:number[];layer:string};
let terrainFrame=0;
let meshes:Mesh[]=[],scene:OrthometricScene|undefined,framePending=false,manifest:FoundationManifest,loadGeneration=0,draws=0,error='',lastPick:unknown=null,lastMvp=new Matrix4();
const flags:Record<string,boolean>={surface:true,water:true,outlines:true,north:true,grid:false,samples:false,bounds:false};
const camera={yaw:.55,pitch:.82,distance:3000,pan:[0,0],targetHeight:0};
function shader(type:number,source:string){const s=gl!.createShader(type)!;gl!.shaderSource(s,source);gl!.compileShader(s);if(!gl!.getShaderParameter(s,gl!.COMPILE_STATUS))throw new Error(gl!.getShaderInfoLog(s)??'shader error');return s;}
const program=gl.createProgram()!;gl.attachShader(program,shader(gl.VERTEX_SHADER,`#version 300 es
in vec3 a_position;in vec3 a_normal;uniform mat4 u_mvp;uniform vec3 u_offset;uniform float u_point_size;out float v_light;
void main(){gl_Position=u_mvp*vec4(a_position+u_offset,1.0);gl_PointSize=u_point_size;v_light=.58+.42*max(0.0,dot(normalize(a_normal),normalize(vec3(-.4,-.5,1.0))));}`));
gl.attachShader(program,shader(gl.FRAGMENT_SHADER,`#version 300 es
precision highp float;in float v_light;uniform vec4 u_color;out vec4 color;void main(){color=vec4(u_color.rgb*v_light,u_color.a);}`));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw new Error(gl.getProgramInfoLog(program)??'program error');
const posAttr=gl.getAttribLocation(program,'a_position'),normalAttr=gl.getAttribLocation(program,'a_normal');const mvpUniform=gl.getUniformLocation(program,'u_mvp'),offsetUniform=gl.getUniformLocation(program,'u_offset'),colorUniform=gl.getUniformLocation(program,'u_color'),pointUniform=gl.getUniformLocation(program,'u_point_size');

function mesh(vertices:number[],indices:number[]|null,mode:number,color:number[],layer:string,offset=[0,0,0],normals?:number[]){
 if(!vertices.length)return;const position=gl!.createBuffer()!,normal=gl!.createBuffer()!;gl!.bindBuffer(gl!.ARRAY_BUFFER,position);gl!.bufferData(gl!.ARRAY_BUFFER,new Float32Array(vertices),gl!.STATIC_DRAW);gl!.bindBuffer(gl!.ARRAY_BUFFER,normal);gl!.bufferData(gl!.ARRAY_BUFFER,new Float32Array(normals??vertices.map((_,i)=>i%3===2?1:0)),gl!.STATIC_DRAW);let element:WebGLBuffer|null=null;
 if(indices){element=gl!.createBuffer()!;gl!.bindBuffer(gl!.ELEMENT_ARRAY_BUFFER,element);gl!.bufferData(gl!.ELEMENT_ARRAY_BUFFER,new Uint32Array(indices),gl!.STATIC_DRAW);}meshes.push({position,normal,indices:element,count:indices?indices.length:vertices.length/3,mode,color,offset,layer});
}
function releaseMeshes(){for(const m of meshes){gl!.deleteBuffer(m.position);gl!.deleteBuffer(m.normal);if(m.indices)gl!.deleteBuffer(m.indices);}meshes=[];}
function terrainSample(x:number,y:number):number|null {
 if(!scene)return null;const t=scene.terrain,w=t.width,h=t.height,v=t.vertices;const stepX=v[3]-v[0],stepY=v[w*3+1]-v[1],c=(x-v[0])/stepX,r=(y-v[1])/stepY;
 if(!(c>=0&&c<=w-1&&r>=0&&r<=h-1))return null;const a=Math.floor(r),b=Math.floor(c),aa=Math.min(a+1,h-1),bb=Math.min(b+1,w-1),values=[t.heights[a*w+b],t.heights[a*w+bb],t.heights[aa*w+b],t.heights[aa*w+bb]];if(values.some(z=>z===null))return null;const u=c-b,q=r-a;return values[0]!*(1-u)*(1-q)+values[1]!*u*(1-q)+values[2]!*(1-u)*q+values[3]!*u*q;
}
function prepare(data:OrthometricScene){
 releaseMeshes();scene=data;const t=data.terrain,v=t.vertices,w=t.width,normals:number[]=[];
 for(let i=0;i<t.heights.length;i++){
  const r=Math.floor(i/w),c=i%w,left=r*w+Math.max(0,c-1),right=r*w+Math.min(w-1,c+1),up=Math.max(0,r-1)*w+c,down=Math.min(t.height-1,r+1)*w+c;
  const dx=(t.heights[right]??t.heights[i]??0)-(t.heights[left]??t.heights[i]??0),dy=(t.heights[down]??t.heights[i]??0)-(t.heights[up]??t.heights[i]??0),sx=v[right*3]-v[left*3],sy=v[down*3+1]-v[up*3+1];const nx=-dx/(sx||1),ny=-dy/(sy||1),length=Math.hypot(nx,ny,1);normals.push(nx/length,ny/length,1/length);
 }
 for(const tile of t.tiles){
  const ranges=tile as TerrainTile&{source_lod_row_range:number[];source_lod_column_range:number[]};const [r0,r1]=ranges.source_lod_row_range,[c0,c1]=ranges.source_lod_column_range;const localNormals:number[]=[];
  for(let r=r0;r<=r1;r++)for(let c=c0;c<=c1;c++)localNormals.push(...normals.slice((r*w+c)*3,(r*w+c)*3+3));
  mesh(tile.vertices,tile.indices,gl!.TRIANGLES,[.39,.52,.39,1],'surface',[tile.origin_projected_m[0]-t.local_origin_projected_m[0],tile.origin_projected_m[1]-t.local_origin_projected_m[1],0],localNormals);
 }
 mesh(data.water.flatMap(x=>x.vertices),null,gl!.TRIANGLES,[.15,.52,.65,.78],'water');mesh(data.footprints.flatMap(x=>x.lines),null,gl!.LINES,[.96,.84,.52,1],'outlines');mesh(data.ground_samples.flatMap(p=>p.local_m.map((v,i)=>i===2?v+.18:v)),null,gl!.POINTS,[1,.58,.25,1],'samples');
 const xs=v.filter((_,i)=>i%3===0),ys=v.filter((_,i)=>i%3===1),minx=Math.min(...xs),maxx=Math.max(...xs),miny=Math.min(...ys),maxy=Math.max(...ys),grid:number[]=[];
 const addLine=(a:number[],b:number[],out:number[])=>{const steps=Math.max(1,Math.ceil(Math.hypot(a[0]-b[0],a[1]-b[1])/25));for(let i=0;i<steps;i++){const q=[a[0]+(b[0]-a[0])*i/steps,a[1]+(b[1]-a[1])*i/steps],s=[a[0]+(b[0]-a[0])*(i+1)/steps,a[1]+(b[1]-a[1])*(i+1)/steps],z=terrainSample(...q as [number,number]),zz=terrainSample(...s as [number,number]);if(z!==null&&zz!==null)out.push(q[0],q[1],z+.12,s[0],s[1],zz+.12);}};
 for(let x=Math.ceil(minx/100)*100;x<=maxx;x+=100)addLine([x,miny],[x,maxy],grid);for(let y=Math.ceil(miny/100)*100;y<=maxy;y+=100)addLine([minx,y],[maxx,y],grid);mesh(grid,null,gl!.LINES,[.68,.82,.68,1],'grid');
 const bounds:number[]=[];for(const tile of t.tiles){const x=tile.origin_projected_m[0]-t.local_origin_projected_m[0],y=tile.origin_projected_m[1]-t.local_origin_projected_m[1],p=tile.vertices,tx=p.filter((_,i)=>i%3===0),ty=p.filter((_,i)=>i%3===1),a=Math.min(...tx)+x,b=Math.max(...tx)+x,c=Math.min(...ty)+y,d=Math.max(...ty)+y;for(const [s,e]of [[[a,c],[b,c]],[[b,c],[b,d]],[[b,d],[a,d]],[[a,d],[a,c]]])addLine(s,e,bounds);}mesh(bounds,null,gl!.LINES,[1,.46,.22,1],'bounds');
 let best=Infinity,focus:number[]|undefined;for(let i=0;i<t.indices.length;i+=3){const p=[0,0,0];for(const index of t.indices.slice(i,i+3))for(let k=0;k<3;k++)p[k]+=t.vertices[index*3+k]/3;const distance=p[0]**2+p[1]**2;if(distance<best){best=distance;focus=p;}}
 if(!focus)throw new Error('本范围没有可发布的有效地形单元；未用零高程补齐');camera.pan=focus.slice(0,2);camera.targetHeight=focus[2];camera.distance=Math.max(maxx-minx,maxy-miny)*1.45;
 $('terrain-stats').textContent=`${t.width} × ${t.height} 显示网格 · ${t.tiles.length}个局部块 · ${t.indices.length/3}三角形。高程 ${Math.min(...t.heights.filter((v):v is number=>v!==null)).toFixed(1)}—${Math.max(...t.heights.filter((v):v is number=>v!==null)).toFixed(1)}m；显示抽稀 ${t.display_decimation}×，原始裁剪采样约 ${t.source_resolution_m[0].toFixed(2)}m。`;
 $('terrain-name').textContent=`${data.id} / NAVD88 · metres · 2017`;
 ($('terrain-source')as HTMLAnchorElement).href=data.source.source_service+'?f=pjson';requestFrame();
}
function render(){
 framePending=false;if(terrainDisposed||contextLost||!scene||canvas.clientWidth<1||canvas.clientHeight<1)return;const ratio=Math.min(devicePixelRatio,1.5),width=Math.floor(canvas.clientWidth*ratio),height=Math.floor(canvas.clientHeight*ratio);if(canvas.width!==width||canvas.height!==height){canvas.width=width;canvas.height=height;}gl!.viewport(0,0,width,height);gl!.clearColor(.055,.12,.15,1);gl!.clear(gl!.COLOR_BUFFER_BIT|gl!.DEPTH_BUFFER_BIT);gl!.enable(gl!.DEPTH_TEST);gl!.depthFunc(gl!.LEQUAL);gl!.useProgram(program);
 const sampled=terrainSample(camera.pan[0],camera.pan[1]);if(sampled!==null)camera.targetHeight=sampled;
 const target=new Cartesian3(camera.pan[0],camera.pan[1],camera.targetHeight),horizontal=camera.distance*Math.cos(camera.pitch);let eye=new Cartesian3(target.x+Math.sin(camera.yaw)*horizontal,target.y-Math.cos(camera.yaw)*horizontal,target.z+Math.sin(camera.pitch)*camera.distance);if(walkMode){eye=Cartesian3.fromArray([walker.position[0],walker.position[1],walker.position[2]+1.7]);target.x=eye.x+Math.sin(walker.yaw)*Math.cos(walker.pitch);target.y=eye.y+Math.cos(walker.yaw)*Math.cos(walker.pitch);target.z=eye.z+Math.sin(walker.pitch);}else{const floor=terrainSample(eye.x,eye.y);if(floor!==null)eye.z=Math.max(eye.z,floor+3);}
 const direction=Cartesian3.normalize(Cartesian3.subtract(target,eye,new Cartesian3()),new Cartesian3()),right=Cartesian3.normalize(Cartesian3.cross(direction,Cartesian3.UNIT_Z,new Cartesian3()),new Cartesian3()),up=Cartesian3.cross(right,direction,new Cartesian3());const view=Matrix4.computeView(eye,direction,up,right,new Matrix4()),projection=Matrix4.computePerspectiveFieldOfView(walkMode?walker.fov:.85,width/height,walkMode?.1:Math.max(.25,camera.distance/15000),camera.distance*8+10000,new Matrix4());lastMvp=Matrix4.multiply(projection,view,new Matrix4());gl!.uniformMatrix4fv(mvpUniform,false,new Float32Array(Matrix4.toArray(lastMvp)));gl!.uniform1f(pointUniform,4*ratio);
 for(const m of meshes){if(!flags[m.layer])continue;gl!.uniform3fv(offsetUniform,m.offset);gl!.uniform4fv(colorUniform,m.color);gl!.bindBuffer(gl!.ARRAY_BUFFER,m.position);gl!.enableVertexAttribArray(posAttr);gl!.vertexAttribPointer(posAttr,3,gl!.FLOAT,false,0,0);gl!.bindBuffer(gl!.ARRAY_BUFFER,m.normal);gl!.enableVertexAttribArray(normalAttr);gl!.vertexAttribPointer(normalAttr,3,gl!.FLOAT,false,0,0);
  if(m.layer==='surface'){gl!.enable(gl!.POLYGON_OFFSET_FILL);gl!.polygonOffset(1,2);}else gl!.disable(gl!.POLYGON_OFFSET_FILL);
  if(m.color[3]<1){gl!.enable(gl!.BLEND);gl!.blendFunc(gl!.SRC_ALPHA,gl!.ONE_MINUS_SRC_ALPHA);gl!.depthMask(false);}else{gl!.disable(gl!.BLEND);gl!.depthMask(true);}
  // Source outlines/grid are explicitly inspection overlays, not physical walls or foundations.
  if(['outlines','grid','bounds','samples'].includes(m.layer))gl!.disable(gl!.DEPTH_TEST);else gl!.enable(gl!.DEPTH_TEST);
  if(m.indices){gl!.bindBuffer(gl!.ELEMENT_ARRAY_BUFFER,m.indices);gl!.drawElements(m.mode,m.count,gl!.UNSIGNED_INT,0);}else gl!.drawArrays(m.mode,0,m.count);
 }
 gl!.depthMask(true);gl!.disable(gl!.POLYGON_OFFSET_FILL);draws++;$('terrain-north-label').hidden=!flags.north;$('terrain-scale').hidden=!flags.north;$('terrain-north-label').style.transform=`rotate(${-camera.yaw*180/Math.PI}deg)`;
 const span=2*camera.distance*Math.tan(.85/2),unit=10**Math.floor(Math.log10(span/8)),metres=[1,2,5,10].map(v=>v*unit).filter(v=>v<span/4).at(-1)??unit;$('terrain-scale').innerHTML=`<span style="width:${metres/span*canvas.clientWidth}px"></span><small>${metres>=1000?metres/1000+' km':metres+' m'} · 局部米制参考</small>`;
}
function requestFrame(){if(terrainDisposed||contextLost)return;if(!framePending){framePending=true;terrainFrame=requestAnimationFrame(render);}}
const pointers=new Map<number,{x:number;y:number}>();let dragDistance=0;
canvas.oncontextmenu=e=>e.preventDefault();canvas.addEventListener('pointerdown',e=>{canvas.focus();canvas.setPointerCapture(e.pointerId);pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});dragDistance=0;});
canvas.addEventListener('pointermove',e=>{const old=pointers.get(e.pointerId);if(!old)return;const dx=e.clientX-old.x,dy=e.clientY-old.y;dragDistance+=Math.hypot(dx,dy);
 if(walkMode&&pointers.size===1){walker.yaw+=dx*.006;walker.pitch=Math.max(-.8,Math.min(.8,walker.pitch-dy*.005));pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});requestFrame();return;}
 if(pointers.size===2){const other=[...pointers.entries()].find(([id])=>id!==e.pointerId)![1];const before=Math.hypot(old.x-other.x,old.y-other.y),after=Math.hypot(e.clientX-other.x,e.clientY-other.y);if(after>0){if(walkMode)walker.fov=Math.max(.6,Math.min(1.2,walker.fov*before/after));else camera.distance*=before/after;}}
 else if(e.buttons===2||e.shiftKey){const scale=camera.distance/canvas.clientHeight;camera.pan[0]+=(-dx*Math.cos(camera.yaw)-dy*Math.sin(camera.yaw))*scale;camera.pan[1]+=(-dx*Math.sin(camera.yaw)+dy*Math.cos(camera.yaw))*scale;}
 else{camera.yaw+=dx*.006;camera.pitch=Math.max(.12,Math.min(1.5,camera.pitch+dy*.005));}
 camera.distance=Math.max(20,Math.min(15000,camera.distance));pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});requestFrame();});
function pick(clientX:number,clientY:number){
 if(!scene)return;const rect=canvas.getBoundingClientRect(),x=(clientX-rect.x)/rect.width*2-1,y=1-(clientY-rect.y)/rect.height*2,inv=Matrix4.inverse(lastMvp,new Matrix4());const unproject=(z:number)=>{const a=Matrix4.multiplyByVector(inv,new Cartesian4(x,y,z,1),new Cartesian4());return new Cartesian3(a.x/a.w,a.y/a.w,a.z/a.w);};const start=unproject(-1),end=unproject(1),dir=Cartesian3.normalize(Cartesian3.subtract(end,start,new Cartesian3()),new Cartesian3());let closest=Infinity,point:Cartesian3|undefined;const t=scene.terrain;
 for(let i=0;i<t.indices.length;i+=3){const a=Cartesian3.fromArray(t.vertices,t.indices[i]*3),b=Cartesian3.fromArray(t.vertices,t.indices[i+1]*3),c=Cartesian3.fromArray(t.vertices,t.indices[i+2]*3),e1=Cartesian3.subtract(b,a,new Cartesian3()),e2=Cartesian3.subtract(c,a,new Cartesian3()),h=Cartesian3.cross(dir,e2,new Cartesian3()),det=Cartesian3.dot(e1,h);if(Math.abs(det)<1e-10)continue;const f=1/det,s=Cartesian3.subtract(start,a,new Cartesian3()),u=f*Cartesian3.dot(s,h);if(u<0||u>1)continue;const q=Cartesian3.cross(s,e1,new Cartesian3()),v=f*Cartesian3.dot(dir,q);if(v<0||u+v>1)continue;const distance=f*Cartesian3.dot(e2,q);if(distance>0&&distance<closest){closest=distance;point=Cartesian3.add(start,Cartesian3.multiplyByScalar(dir,distance,new Cartesian3()),new Cartesian3());}}
 if(point){const xy=[point.x+t.local_origin_projected_m[0],point.y+t.local_origin_projected_m[1]];lastPick={projected_m:xy,orthometric_height_m:point.z,datum:'NAVD88',source:'LOD triangle derived from actual 2017 DEM with explicit LERC validity mask',independently_measured:false};let text=`E ≈${Math.round(xy[0])}m · N ≈${Math.round(xy[1])}m · H ≈${Math.round(point.z)}m NAVD88（2017 DEM显示网格，非独立实测）`;if(localTool==='measure'){localMeasurements.push([point.x,point.y,point.z]);if(localMeasurements.length>2)localMeasurements=localMeasurements.slice(-1);if(localMeasurements.length===2){const m=localMeasurement(localMeasurements[0],localMeasurements[1]);text=`局部水平≈${Math.round(m.horizontal)}m · 空间≈${Math.round(m.space)}m · 高差≈${Math.round(m.difference)}m（同一NAVD88网格，来源精度未知）`;}}$('terrain-readout').textContent=text;if(parent!==window)parent.postMessage({type:'nyc-local-measurement',text},location.origin);}else{lastPick=null;$('terrain-readout').textContent='此处没有已知地形高度。未把缺失值或展示水位当作零高程地面。';}
}
canvas.addEventListener('pointerup',e=>{if(dragDistance<5&&pointers.size===1&&e.button===0)pick(e.clientX,e.clientY);pointers.delete(e.pointerId);});canvas.addEventListener('pointercancel',()=>{pointers.clear();stopWalkInput();});canvas.addEventListener('lostpointercapture',()=>{pointers.clear();stopWalkInput();});canvas.addEventListener('wheel',e=>{e.preventDefault();if(walkMode)walker.fov=Math.max(.6,Math.min(1.2,walker.fov*Math.exp(e.deltaY*.0005)));else camera.distance=Math.max(20,Math.min(15000,camera.distance*Math.exp(e.deltaY*.001)));requestFrame();},{passive:false});
for(const key of Object.keys(flags))($('terrain-'+key)as HTMLInputElement).onchange=e=>{flags[key]=(e.target as HTMLInputElement).checked;requestFrame();};
$('terrain-fit').onclick=()=>{if(scene)prepare(scene);};$('terrain-panel').onclick=()=>{const collapsed=app.classList.toggle('collapsed');$('terrain-panel').textContent=collapsed?'展开面板':'收起面板';$('terrain-panel').setAttribute('aria-expanded',String(!collapsed));requestFrame();};new ResizeObserver(requestFrame).observe(canvas);
async function load(id:string){activeLoad?.abort();activeLoad=new AbortController();const generation=++loadGeneration;$('terrain-loading').hidden=false;try{const r=await fetch(new URL(`datasets/foundation/${manifest.datasets.find(d=>d.id===id)?.terrain??id+'.json'}`,document.baseURI),{signal:activeLoad.signal});if(!r.ok)throw new Error(`DEM ${id}: HTTP ${r.status}`);const data=await r.json()as OrthometricScene;if(data.scene_kind!=='local_projected_orthometric_inspector'||data.terrain.height_datum!=='NAVD88'||data.terrain.vertical_exaggeration!==1||data.world_placement_allowed!==false)throw new Error('地形坐标或高程声明不符合检视契约');if(generation!==loadGeneration||terrainDisposed)return;stopWalkInput();walkMode=false;walkReady=false;collider=undefined;prepare(data);$('terrain-loading').hidden=true;if(params.has('walk'))await enterWalk();}catch(e){if(terrainDisposed||activeLoad?.signal.aborted)return;error=String(e);$('terrain-error').textContent=error;$('terrain-error').hidden=false;$('terrain-loading').hidden=true;}}
async function init(){try{const r=await fetch(new URL(params.has('extended')?'datasets/environment/terrain-manifest.json':'datasets/foundation/manifest.json',document.baseURI));if(!r.ok)throw new Error('本地地形清单缺失');manifest=await r.json();const select=$('terrain-area')as HTMLSelectElement;for(const d of manifest.datasets)select.add(new Option(d.id,d.id));select.onchange=()=>void load(select.value);const requested=params.get('area');select.value=manifest.datasets.some(d=>d.id===requested)?requested!:manifest.datasets[0].id;await load(select.value);}catch(e){if(terrainDisposed||activeLoad?.signal.aborted)return;error=String(e);$('terrain-error').textContent=error;$('terrain-error').hidden=false;$('terrain-loading').hidden=true;}}
if(new URLSearchParams(location.search).has('diagnostics'))Object.defineProperty(window,'__NYC_TERRAIN__',{value:{snapshot:()=>({id:scene?.id,sceneKind:scene?.scene_kind,worldPlacementAllowed:scene?.world_placement_allowed,datum:scene?.terrain.height_datum,exaggeration:1,triangles:scene?scene.terrain.indices.length/3:0,tiles:scene?.terrain.tiles.length,sourceRaster:scene?.source.masked_raster??scene?.source.raster,flags:{...flags},camera:{...camera,pan:[...camera.pan]},buffers:meshes.length*2+meshes.filter(m=>m.indices).length,draws,error,lastPick,walk:{enabled:walkMode,ready:walkReady,position:[...walker.position],eyeHeight:1.7,yaw:walker.yaw,pitch:walker.pitch,blocked:walkBlocked,keys:[...walkKeys],layer:'ground',collisionTriangles:collider?.spec.allowed_triangle_offsets.length??0},webglError:gl!.getError(),heightRange:scene?[Math.min(...scene.terrain.heights.filter((v):v is number=>v!==null)),Math.max(...scene.terrain.heights.filter((v):v is number=>v!==null))]:null,sceneDataShaIdentity:scene?.source.masked_raster??scene?.source.raster})}});
function stopWalkInput(){walkKeys.clear();walkTime=0;if(walkFrame)cancelAnimationFrame(walkFrame);walkFrame=0;}
function walkTick(time:number){
 walkFrame=0;if(!walkMode||!collider||!walkKeys.size){walkTime=0;return;}
 const elapsed=walkTime?(time-walkTime)/1000:0;walkTime=time;
 if(elapsed>1){stopWalkInput();return;}
 const forward=Number(walkKeys.has('KeyW'))-Number(walkKeys.has('KeyS')),right=Number(walkKeys.has('KeyD'))-Number(walkKeys.has('KeyA'));
 const norm=Math.hypot(forward,right);
 if(norm){const d=collider.spec.speed_m_per_s*elapsed/norm;
  const delta=[(Math.sin(walker.yaw)*forward+Math.cos(walker.yaw)*right)*d,(Math.cos(walker.yaw)*forward-Math.sin(walker.yaw)*right)*d];
  const next=collider.move(walker.position,delta);walker.position=next.position;walkBlocked=next.blocked;
  $('walk-message').textContent=walkBlocked?'前方未知、障碍或无可靠碰撞；停在原地。':'1.4m/s · 眼高1.7m · 地面层，桥面/桥下及道路区域禁止进入';
  requestFrame();
 }
 walkFrame=requestAnimationFrame(walkTick);
}
async function enterWalk(){
 if(!scene)return;const id=scene.id,token=loadGeneration;
 const r=await fetch(new URL('datasets/environment/collision/'+id+'.json',document.baseURI),{signal:activeLoad?.signal});
 if(!r.ok)throw new Error('本区域未提供可靠的局部碰撞');
 const spec=await r.json()as CollisionSpec;
 if(token!==loadGeneration)return;
 collider=new GroundCollider(scene.terrain,spec);
 if(!spec.spawn||collider.sample(spec.spawn[0],spec.spawn[1])===null)throw new Error('本样区没有可进入的受限地面');
 walker.position=[...spec.spawn];walkMode=true;walkReady=true;hud.hidden=false;
 $('walk-message').textContent='WASD移动 · 拖动转向 · 2017 DEM受限检查；不是当前实地通行验证';
 const recovery=sessionStorage.getItem('nyc-terrain-recovery');if(recovery){sessionStorage.removeItem('nyc-terrain-recovery');const saved=JSON.parse(recovery);if(saved.id===id&&Array.isArray(saved.position)&&saved.position.length===3&&saved.position.every(Number.isFinite)){const z=collider.sample(saved.position[0],saved.position[1]);if(z!==null){walker.position=[saved.position[0],saved.position[1],z];walker.yaw=saved.yaw;walker.pitch=saved.pitch;}}}
 requestFrame();
 sendState();
}
function walkState(){return {area:scene?.id,position:[...walker.position],yaw:walker.yaw,pitch:walker.pitch,ready:walkReady,enabled:walkMode,blocked:walkBlocked};}
function sendState(requestId?:number){if(parent!==window)parent.postMessage({type:'nyc-walk-state',state:walkState(),requestId},location.origin);}
addEventListener('keydown',e=>{
 if(e.code==='Escape'&&walkMode){stopWalkInput();walkMode=false;hud.hidden=true;requestFrame();if(parent!==window)parent.postMessage({type:'nyc-walk-exit'},location.origin);return;}
 if(walkMode&&['KeyW','KeyA','KeyS','KeyD'].includes(e.code)&&e.target===canvas){e.preventDefault();walkKeys.add(e.code);if(!walkFrame){walkTime=performance.now();walkFrame=requestAnimationFrame(walkTick);}}
});
addEventListener('keyup',e=>walkKeys.delete(e.code));addEventListener('blur',stopWalkInput);
canvas.addEventListener('blur',stopWalkInput);
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopWalkInput();});
addEventListener('orientationchange',()=>{stopWalkInput();pointers.clear();requestFrame();});
addEventListener('message',e=>{
 if(e.origin!==location.origin||e.source!==parent||!e.data||typeof e.data!=='object')return;
 if(e.data.type==='nyc-walk-pause')stopWalkInput();
 if(e.data.type==='nyc-walk-snapshot')sendState(e.data.requestId);
 if(e.data.type==='nyc-walk-tool'&&['point','measure','select'].includes(e.data.tool)){localTool=e.data.tool;localMeasurements=[];}
 if(e.data.type==='nyc-walk-restore'&&collider&&e.data.state?.area===scene?.id){
  const s=e.data.state,p=s.position;
  if(Array.isArray(p)&&p.length===3&&p.every(Number.isFinite)&&collider.sample(p[0],p[1])!==null&&Number.isFinite(s.yaw)&&Number.isFinite(s.pitch)){
   const z=collider.sample(p[0],p[1])!;walker.position=[p[0],p[1],z];walker.yaw=s.yaw;walker.pitch=Math.max(-.8,Math.min(.8,s.pitch));requestFrame();sendState();
  }else $('walk-message').textContent='书签位置不在可靠地面内，保持当前位置。';
 }
});
$('walk-leave').onclick=()=>{stopWalkInput();walkMode=false;hud.hidden=true;requestFrame();if(parent!==window)parent.postMessage({type:'nyc-walk-exit'},location.origin);};
hud.querySelectorAll<HTMLButtonElement>('[data-walk-key]').forEach(b=>{
 b.onpointerdown=e=>{e.preventDefault();e.stopPropagation();b.setPointerCapture(e.pointerId);walkKeys.add(b.dataset.walkKey!);if(!walkFrame){walkTime=performance.now();walkFrame=requestAnimationFrame(walkTick);}};
 for(const event of ['pointerup','pointercancel','lostpointercapture'])b.addEventListener(event,()=>stopWalkInput());
});
canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();contextLost=true;stopWalkInput();activeLoad?.abort();sessionStorage.setItem('nyc-terrain-recovery',JSON.stringify({id:scene?.id,position:walker.position,yaw:walker.yaw,pitch:walker.pitch}));$('terrain-error').hidden=false;$('terrain-error').textContent='局部图形上下文丢失；恢复后重新加载并核对保存的地面位置。';},{capture:true});
canvas.addEventListener('webglcontextrestored',()=>location.reload());
addEventListener('pagehide',()=>{terrainDisposed=true;if(terrainFrame)cancelAnimationFrame(terrainFrame);loadGeneration++;activeLoad?.abort();stopWalkInput();releaseMeshes();gl!.deleteProgram(program);});void init();
