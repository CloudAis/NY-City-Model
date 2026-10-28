import {chromium} from 'playwright-core';
import {spawn,execFileSync} from 'node:child_process';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {setTimeout as delay} from 'node:timers/promises';
import {installProbe} from './probe.mjs';
const label=process.env.NYC_PERF_LABEL??'baseline',root=process.env.NYC_PERF_ROOT??'data/intermediate/stage9/baseline',port=4194;
const route=JSON.parse(await readFile('config/performance-route.json','utf8')),report='reports/stage9';
const server=spawn('python3',['-m','http.server',String(port),'--bind','127.0.0.1'],{cwd:root,stdio:'ignore'});
let browser,page;const errors=[],requests=[],steps=[];const origin=`http://127.0.0.1:${port}`;
const percentile=(a,p)=>a.length?[...a].sort((x,y)=>x-y)[Math.min(a.length-1,Math.floor(a.length*p))]:null;
const summarize=p=>({samples:p.frames.length,raf_ms:{p50:percentile(p.frames.map(f=>f.ms),.5),p95:percentile(p.frames.map(f=>f.ms),.95),p99:percentile(p.frames.map(f=>f.ms),.99)},render_intervals:p.frames.filter(f=>f.calls>0).length,draw_calls:{total:p.frames.reduce((n,f)=>n+f.calls,0),max_per_interval:Math.max(0,...p.frames.map(f=>f.calls))},submitted_triangles:p.frames.reduce((n,f)=>n+f.triangles,0),submitted_lines:p.frames.reduce((n,f)=>n+f.lines,0),long_tasks:{count:p.longTasks.length,total_ms:p.longTasks.reduce((n,t)=>n+t.duration,0),max_ms:Math.max(0,...p.longTasks.map(t=>t.duration))},render_active_raf_ms:{p50:percentile(p.frames.filter(f=>f.calls>0).map(f=>f.ms),.5),p95:percentile(p.frames.filter(f=>f.calls>0).map(f=>f.ms),.95),p99:percentile(p.frames.filter(f=>f.calls>0).map(f=>f.ms),.99)},domWrites:p.domWrites,resources:p.resources,jsHeap:p.jsHeap,gpu_vram_measured_bytes:null});
const snap=()=>page.evaluate(()=>window.__NYC_INSPECTION__.snapshot());
try{
 await mkdir(report,{recursive:true});for(let i=0;i<100;i++){try{if((await fetch(origin+'/inspection.html')).ok)break;}catch{}await delay(100);}
 browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader','--enable-precise-memory-info']});
 const context=await browser.newContext({viewport:{width:route.viewport.width,height:route.viewport.height},deviceScaleFactor:route.viewport.deviceScaleFactor});
 await context.addInitScript(installProbe);await context.route('**/*',r=>new URL(r.request().url()).origin===origin?r.continue():r.abort());
 page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('request',r=>requests.push({url:r.url(),at:Date.now()}));
 const cdp=await context.newCDPSession(page);await cdp.send('Network.enable');await cdp.send('Network.setCacheDisabled',{cacheDisabled:true});await cdp.send('Performance.enable');
 const start=Date.now();await page.goto(origin+'/inspection.html?diagnostics=1');
 await page.waitForFunction(()=>{const s=window.__NYC_INSPECTION__?.snapshot();return s?.layerStates.some(l=>l.key==='roads'&&l.loaded>0)&&window.__PERF_PROBE__.snapshot().frames.some(f=>f.calls>0);},null,{timeout:120000});
 const firstRealSceneMs=Date.now()-start;await page.locator('#quality').selectOption(route.quality);
 const hardware=await page.evaluate(()=>{const c=document.createElement('canvas'),gl=c.getContext('webgl2'),ext=gl?.getExtension('WEBGL_debug_renderer_info');return {userAgent:navigator.userAgent,hardwareConcurrency:navigator.hardwareConcurrency,deviceMemory:navigator.deviceMemory,dpr:devicePixelRatio,viewport:[innerWidth,innerHeight],renderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):null,vendor:ext?gl.getParameter(ext.UNMASKED_VENDOR_WEBGL):null};});
 for(const step of route.steps){
  const beforeRequests=requests.length,mark=await page.evaluate(()=>window.__PERF_PROBE__.mark());
  if(step.action==='city')await page.locator('#city-reset').click();
  if(step.action==='preset')await page.locator('#preset').selectOption(step.preset);
  if(step.action==='walk'){
   await page.locator('#mode').selectOption('walk');await page.locator('#walk-area').selectOption(step.area);
   await page.waitForFunction(area=>{const s=document.getElementById('local-view').contentWindow?.__NYC_TERRAIN__?.snapshot();return s?.id===area&&s.walk.ready;},step.area,{timeout:120000});
   await page.frameLocator('#local-view').locator('#terrain-canvas').focus();await page.keyboard.down('w');await delay(650);await page.keyboard.up('w');
  }else await page.waitForFunction(()=>!window.__NYC_INSPECTION__.snapshot().flying,null,{timeout:120000});
  if(step.action==='preset'){
   const canvas=page.locator('#globe canvas'),b=await canvas.boundingBox();await page.mouse.move(b.x+b.width*.5,b.y+b.height*.5);await page.mouse.down();await page.mouse.move(b.x+b.width*.53,b.y+b.height*.52,{steps:12});await page.mouse.up();
  }
  await delay(step.seconds*1000);
  const probe=await page.evaluate(mark=>window.__PERF_PROBE__.snapshot(mark),mark),s=await snap();
  let child=null;if(step.action==='walk')child=await page.frameLocator('#local-view').locator('body').evaluate(()=>({probe:window.__PERF_PROBE__.snapshot(),terrain:window.__NYC_TERRAIN__.snapshot()}));
  const metrics=(await cdp.send('Performance.getMetrics')).metrics;steps.push({id:step.id,actual_elapsed_ms:probe.now-mark,new_requests:requests.length-beforeRequests,measurement:summarize(probe),child:child?{measurement:summarize(child.probe),position:child.terrain.walk.position}:null,viewer:s,cdp_metrics:metrics,sample_trace:probe.frames.map(f=>[f.at,f.ms,f.calls,f.triangles,f.lines])});
  await page.screenshot({path:report+'/'+label+'-'+step.id+'.png'});console.log(label,step.id,JSON.stringify({raf:steps.at(-1).measurement.raf_ms,requests:requests.length-beforeRequests,heap:probe.jsHeap?.used}));
 }
 if(errors.length)throw Error('unexpected browser errors: '+JSON.stringify(errors));
 const result={at_utc:new Date().toISOString(),label,probe_version:2,build_root:root,code_commit:label.startsWith('baseline')?JSON.parse(await readFile('reports/stage9/baseline-version.json','utf8')).code_commit:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),test_harness_commit:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),browser:await browser.version(),hardware,route,quality:route.quality,http_cache_disabled:true,first_real_scene_ms:firstRealSceneMs,elapsed_wall_ms:Date.now()-start,steps,errors,requests,real_hardware_gpu:false,notes:['rAF quantiles are UI heartbeat including idle; rendered intervals and submitted calls reported separately','submitted triangles include repeated frames, not unique model triangles','buffer bytes are estimates of known WebGL allocations, no VRAM measurement','street step limited to existing local DEM; no current complete street models']};
 await writeFile(report+'/'+label+'.json',JSON.stringify(result,null,2)+'\n');console.log('COMPLETE',label,steps.length,'errors',errors.length);
}catch(e){await writeFile(report+'/'+label+'-failure.json',JSON.stringify({error:String(e),errors,steps},null,2));throw e;}finally{await browser?.close();server.kill();}
