/** A real wall-clock continuous browser run. No virtual time or accelerated simulation. */
import {chromium} from 'playwright-core';
import {spawn,execFileSync} from 'node:child_process';
import {readFile,writeFile,appendFile,mkdir,readdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {setTimeout as delay} from 'node:timers/promises';
import assert from 'node:assert/strict';
import {installProbe} from './probe.mjs';
const seconds=Number(process.env.NYC_SOAK_SECONDS??1800);assert.ok(seconds>0);
const report='reports/stage9/soak',origin='http://127.0.0.1:4196';await mkdir(report,{recursive:true});
async function fingerprint(){const result={};for(const p of (await readdir('dist/assets')).sort())result[p]=createHash('sha256').update(await readFile('dist/assets/'+p)).digest('hex');return result;}
const codeFingerprint=await fingerprint(),commit=execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim();
const server=spawn('python3',['-m','http.server','4196','--bind','127.0.0.1'],{cwd:'dist',stdio:'ignore'});
let browser,page,timer,started=0,navigations=0,requestCount=0,failedRequests=0;const errors=[],cycles=[],heartbeats=[];
const snap=()=>page.evaluate(()=>window.__NYC_INSPECTION__.snapshot());
async function ready(id){await page.waitForFunction(id=>{const s=window.__NYC_INSPECTION__?.snapshot();return s?.preset===id&&!s.flying&&s.layerStates.some(l=>l.key==='roads'&&l.loaded>0);},id,{timeout:45000});}
try{
 for(let i=0;i<100;i++){try{if((await fetch(origin)).ok)break;}catch{}await delay(100);}
 browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader','--enable-precise-memory-info']});
 const context=await browser.newContext({viewport:{width:1440,height:1000},deviceScaleFactor:1});await context.addInitScript(installProbe);
 await context.route('**/*',r=>new URL(r.request().url()).origin===origin?r.continue():r.abort());page=await context.newPage();
 page.on('pageerror',e=>errors.push({at_utc:new Date().toISOString(),error:e.message}));page.on('console',m=>{if(m.type()==='error')errors.push({at_utc:new Date().toISOString(),error:m.text()});});
 page.on('request',()=>requestCount++);page.on('requestfailed',()=>failedRequests++);page.on('crash',()=>errors.push({at_utc:new Date().toISOString(),error:'page crash'}));page.on('framenavigated',f=>{if(f===page.mainFrame())navigations++;});
 const cdp=await context.newCDPSession(page);await cdp.send('Performance.enable');
 await page.goto(origin+'/inspection.html?diagnostics=1');await ready('brooklyn-span');await page.locator('#quality').selectOption('medium');started=Date.now();
 const startedUtc=new Date(started).toISOString();await writeFile(report+'/started.json',JSON.stringify({started_utc:startedUtc,required_real_seconds:seconds,code_commit:commit,codeFingerprint,virtual_time:false,quality:'medium',viewport:[1440,1000],dpr:1},null,2)+'\n');
 timer=setInterval(()=>{const row={at_utc:new Date().toISOString(),elapsed_real_seconds:Math.round((Date.now()-started)/1000),cycles:cycles.length};heartbeats.push(row);console.log('HEARTBEAT',JSON.stringify(row));},30000);
 const extras=['pier40','central-reservoir','prospect-north','queens-plaza','morningside-slope','highbridge','forest-hills','grove-street','manhattan-head','williamsburg-head'];
 while(Date.now()-started<seconds*1000){
  const cycle=cycles.length,begin=Date.now(),probeMark=await page.evaluate(()=>window.__PERF_PROBE__.mark());
  await page.locator('#city-reset').click();await delay(4000);
  await page.locator('#preset').selectOption('central-south');await ready('central-south');
  const canvas=page.locator('#globe canvas'),b=await canvas.boundingBox();await page.mouse.move(b.x+b.width*.5,b.y+b.height*.5);await page.mouse.wheel(0,110);await delay(300);await page.mouse.wheel(0,-110);await page.mouse.down();await page.mouse.move(b.x+b.width*.53,b.y+b.height*.52,{steps:10});await page.mouse.up();await delay(3500);
  await page.locator('#query').fill('id:233256');await page.locator('#search-form button').click();await page.locator('#results [data-id]').first().click();await page.locator('#mode').selectOption('top');
  await page.waitForFunction(()=>document.getElementById('details').textContent.includes('规范楼高'));assert.equal((await snap()).selectedId,'nyc:footprints:doitt:233256');await delay(1500);
  await page.locator('#mode').selectOption('walk');await page.locator('#walk-area').selectOption(cycle%3===0?'central-park':'midtown');
  await page.waitForFunction(()=>document.getElementById('local-view').contentWindow?.__NYC_TERRAIN__?.snapshot().walk.ready,null,{timeout:45000});
  const ground=page.frameLocator('#local-view').locator('#terrain-canvas');await ground.focus();await page.keyboard.down('w');await delay(650);await page.keyboard.up('w');await delay(3000);
  const local=await page.frameLocator('#local-view').locator('body').evaluate(()=>window.__NYC_TERRAIN__.snapshot());assert.equal(local.walk.layer,'ground');assert.equal(local.webglError,0);
  for(const id of ['brooklyn-head','queensboro-head','bruckner','st-george-ferry',extras[cycle%extras.length]]){await page.locator('#preset').selectOption(id);await ready(id);await delay(2500);}
  await page.locator('[data-layer=water]').uncheck();await delay(500);await page.locator('[data-layer=water]').check();
  if(cycle%3===0){await page.locator('[data-layer=trees]').check();await delay(800);await page.locator('[data-layer=trees]').uncheck();}
  if(cycle%2===0){await page.locator('#preset').selectOption('brooklyn-span');await page.locator('#cancel-flight').click();assert.equal((await snap()).flying,false);}
  await page.locator('#preset').selectOption('central-south');await ready('central-south');await delay(1200);
  const beforeGC=await cdp.send('Runtime.getHeapUsage');await cdp.send('HeapProfiler.collectGarbage');const afterGC=await cdp.send('Runtime.getHeapUsage');
  const s=await snap(),probe=await page.evaluate(mark=>window.__PERF_PROBE__.snapshot(mark),probeMark),sorted=probe.frames.map(f=>f.ms).sort((a,b)=>a-b),q=p=>sorted[Math.min(sorted.length-1,Math.floor(sorted.length*p))]??null;
  assert.deepEqual(s.errors,[]);assert.ok(s.primitives<=18);assert.ok(s.runtime.queue.active<=2);assert.ok(s.cameraHeight>=799);assert.ok(s.runtime.created-s.runtime.destroyed<=18);assert.equal(navigations,1,'continuous run must not hide a crash through page reload');
  const row={cycle,at_utc:new Date().toISOString(),elapsed_real_seconds:(Date.now()-started)/1000,cycle_seconds:(Date.now()-begin)/1000,visibility:probe.visibility,raf_ms:{p50:q(.5),p95:q(.95),p99:q(.99)},frame_samples:probe.frames.length,render_intervals:probe.frames.filter(f=>f.calls>0).length,submitted_triangles:probe.frames.reduce((n,f)=>n+f.triangles,0),draw_calls:probe.frames.reduce((n,f)=>n+f.calls,0),longTasks:probe.longTasks,resources:probe.resources,jsHeapBeforeForcedGC:beforeGC,jsHeapAfterForcedGC:afterGC,estimatedCesiumResourceBytes:s.layerStates.reduce((n,e)=>n+e.memoryEstimateBytes,0),runtime:s.runtime,loadedTotal:s.loadedTotal,unloadedTotal:s.unloadedTotal,requests:requestCount,failedRequests,localGround:{id:local.id,position:local.walk.position,collisionTriangles:local.walk.collisionTriangles}};
  cycles.push(row);await appendFile(report+'/cycles.jsonl',JSON.stringify(row)+'\n');await writeFile(report+'/progress.json',JSON.stringify({started_utc:startedUtc,latest:row,errors},null,2)+'\n');
  if(cycle%5===0)await page.screenshot({path:report+'/cycle-'+cycle+'.png'});console.log('CYCLE',cycle,JSON.stringify({elapsed:row.elapsed_real_seconds,heapAfterGC:afterGC.usedSize,estimate:row.estimatedCesiumResourceBytes,loaded:s.loadedTotal,unloaded:s.unloadedTotal}));
  if(errors.length)throw Error('unexpected browser errors');
 }
 clearInterval(timer);timer=undefined;const elapsed=(Date.now()-started)/1000,sameCode=JSON.stringify(codeFingerprint)===JSON.stringify(await fingerprint());assert.ok(sameCode,'candidate changed during continuous run');
 const result={started_utc:startedUtc,completed_utc:new Date().toISOString(),elapsed_real_seconds:elapsed,required_real_seconds:1800,completed_required_duration:seconds>=1800&&elapsed>=1800,requested_seconds:seconds,virtual_time:false,continuous_main_document:navigations===1,code_commit:commit,codeFingerprint,same_code_entire_run:sameCode,browser:await browser.version(),software_webgl:true,real_mobile_hardware:false,quality:'medium',viewport:[1440,1000],dpr:1,cycles,heartbeats,errors,requestCount,failedRequests,gpu_vram_measured_bytes:null,memory_note:'CDP main-isolate JS heap, before/after explicitly forced GC per repeated cycle; Cesium and WebGL allocations are estimates, not measured VRAM',scope_limit:'street inspection is restricted local2017DEM; current complete street/bridge/canonical building bodies remain unavailable'};
 await writeFile(report+'/result.json',JSON.stringify(result,null,2)+'\n');console.log('COMPLETE',elapsed,'real seconds;',cycles.length,'cycles;',errors.length,'errors');
}catch(e){if(timer)clearInterval(timer);await writeFile(report+'/failure.json',JSON.stringify({at_utc:new Date().toISOString(),elapsed_real_seconds:started?(Date.now()-started)/1000:0,error:String(e),cycles,errors},null,2));if(page)await page.screenshot({path:report+'/failure.png'});throw e;}finally{await browser?.close();server.kill();}
