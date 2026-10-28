/** Test-only WebGL/rAF instrumentation, used identically before and after. */
export function installProbe(){
 const frames=[],tasks=[],contexts=[],limits=12000,domWrites={diagnosticPanel:0,statusLabels:0};let calls=0,triangles=0,lines=0,last=0,firstReal=null;
 const contextState=new WeakMap();
 for(const Type of [globalThis.WebGLRenderingContext,globalThis.WebGL2RenderingContext]){
  if(!Type)continue;const p=Type.prototype;
  const wrap=(key,fn)=>{const d=Object.getOwnPropertyDescriptor(p,key);if(!d?.value||d.value.__perfWrapped)return;const original=d.value;const f=function(...a){return fn(this,original,a);};f.__perfWrapped=true;Object.defineProperty(p,key,{...d,value:f});};
  function state(gl){let s=contextState.get(gl);if(!s){s={buffers:new WeakMap(),bufferCount:0,bufferBytes:0,bound:new Map(),textures:new WeakSet(),textureCount:0,programs:new WeakSet(),programCount:0,lost:false};contextState.set(gl,s);contexts.push(s);}return s;}
  wrap('createBuffer',(gl,f,a)=>{const b=f.apply(gl,a);state(gl).buffers.set(b,0);state(gl).bufferCount++;return b;});
  wrap('bindBuffer',(gl,f,a)=>{state(gl).bound.set(a[0],a[1]);return f.apply(gl,a);});
  wrap('bufferData',(gl,f,a)=>{const s=state(gl),b=s.bound.get(a[0]),size=typeof a[1]==='number'?a[1]:a[1]?.byteLength??0;if(b){s.bufferBytes+=size-(s.buffers.get(b)??0);s.buffers.set(b,size);}return f.apply(gl,a);});
  wrap('deleteBuffer',(gl,f,a)=>{const s=state(gl);if(s.buffers.has(a[0])){s.bufferBytes-=s.buffers.get(a[0]);s.bufferCount--;s.buffers.delete(a[0]);}for(const [key,value]of s.bound)if(value===a[0])s.bound.delete(key);return f.apply(gl,a);});
  wrap('createTexture',(gl,f,a)=>{const b=f.apply(gl,a);state(gl).textures.add(b);state(gl).textureCount++;return b;});
  wrap('deleteTexture',(gl,f,a)=>{const s=state(gl);if(s.textures.delete(a[0]))s.textureCount--;return f.apply(gl,a);});
  wrap('createProgram',(gl,f,a)=>{const b=f.apply(gl,a);state(gl).programs.add(b);state(gl).programCount++;return b;});
  wrap('deleteProgram',(gl,f,a)=>{const s=state(gl);if(s.programs.delete(a[0]))s.programCount--;return f.apply(gl,a);});
  for(const key of ['drawArrays','drawElements','drawArraysInstanced','drawElementsInstanced'])wrap(key,(gl,f,a)=>{
   const n=key.includes('Arrays')?a[2]:a[1],instances=key.includes('Instanced')?a.at(-1):1;calls++;
   if(a[0]===gl.TRIANGLES)triangles+=n/3*instances;
   else if(a[0]===gl.TRIANGLE_STRIP||a[0]===gl.TRIANGLE_FAN)triangles+=Math.max(0,n-2)*instances;
   else if(a[0]===gl.LINES)lines+=n/2*instances;
   if(firstReal===null&&n>0)firstReal=performance.now();return f.apply(gl,a);
  });
 }
 try{new PerformanceObserver(list=>{for(const x of list.getEntries()){tasks.push({start:x.startTime,duration:x.duration});if(tasks.length>2000)tasks.shift();}}).observe({type:'longtask',buffered:true});}catch{}
 new MutationObserver(records=>{for(const r of records){const id=r.target.id;if(id==='layer-status')domWrites.diagnosticPanel++;if(['status','load-text','perf-status'].includes(id))domWrites.statusLabels++;}}).observe(document,{subtree:true,childList:true,characterData:true});
 const resources=()=>contexts.reduce((r,s)=>({known_buffer_bytes:r.known_buffer_bytes+s.bufferBytes,buffers:r.buffers+s.bufferCount,textures:r.textures+s.textureCount,programs:r.programs+s.programCount}),{known_buffer_bytes:0,buffers:0,textures:0,programs:0});
 function tick(t){if(last){frames.push({at:t,ms:t-last,calls,triangles,lines});if(frames.length>limits)frames.shift();}calls=triangles=lines=0;last=t;requestAnimationFrame(tick);}requestAnimationFrame(tick);
 Object.defineProperty(window,'__PERF_PROBE__',{value:{snapshot:(since=0)=>({probeVersion:2,domWrites:{...domWrites},now:performance.now(),firstDrawAt:firstReal,frames:frames.filter(f=>f.at>=since),longTasks:tasks.filter(t=>t.start>=since),resources:resources(),jsHeap:performance.memory?{used:performance.memory.usedJSHeapSize,total:performance.memory.totalJSHeapSize,limit:performance.memory.jsHeapSizeLimit}:null,gpu_vram_measured_bytes:null,gpu_estimate_note:'known WebGL buffer allocations only; texture/driver/framebuffer memory not measured',visibility:document.visibilityState,dpr:devicePixelRatio,viewport:[innerWidth,innerHeight]}),mark:()=>performance.now()}});
}
