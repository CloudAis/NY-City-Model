import {chromium} from 'playwright-core';
import {spawn} from 'node:child_process';
import {writeFile,mkdir} from 'node:fs/promises';
import {setTimeout as delay} from 'node:timers/promises';
import assert from 'node:assert/strict';
const origin='http://127.0.0.1:4195',report=process.env.NYC_REPORT_DIR??'reports/stage9';
const server=spawn(process.execPath,['node_modules/vite/bin/vite.js','preview','--host','127.0.0.1','--port','4195','--strictPort'],{stdio:'ignore'});
let browser,page,phase='normal';const checks=[],errors=[],expectedConsole=[],requests=[],observations={};
const snap=()=>page.evaluate(()=>window.__NYC_INSPECTION__.snapshot());
async function ready(id){await page.waitForFunction(id=>{const s=window.__NYC_INSPECTION__?.snapshot();return s?.preset===id&&!s.flying&&s.layerStates.some(l=>l.key==='roads'&&l.loaded>0);},id,{timeout:120000});}
async function check(name,fn){if(!phase.startsWith('expected-'))phase='normal:'+name;await fn();checks.push(name);console.log('PASS',name);}
try{
 for(let i=0;i<100;i++){try{if((await fetch(origin)).ok)break;}catch{}await delay(100);}
 browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const context=await browser.newContext({viewport:{width:1440,height:1000}});await context.route('**/*',r=>new URL(r.request().url()).origin===origin?r.continue():r.abort());
 page=await context.newPage();page.on('pageerror',e=>errors.push({phase,error:e.stack??e.message}));page.on('console',m=>{if(m.type()==='error')(phase.startsWith('expected-')?expectedConsole:errors).push({phase,error:m.text()});});page.on('request',r=>requests.push(r.url()));
 await page.goto(origin+'/inspection.html?diagnostics=1');await ready('brooklyn-span');
 await check('quality tiers preserve original models; auto is opt-in and manual selection takes priority',async()=>{
  for(const q of ['high','low','medium']){await page.locator('#quality').selectOption(q);assert.equal((await snap()).quality,q);}
  await page.locator('#auto-quality').check();assert.equal((await snap()).runtime.adaptive.enabled,true);await page.locator('#quality').selectOption('high');assert.equal((await snap()).runtime.adaptive.enabled,false);await page.locator('#quality').selectOption('medium');
  assert.equal((await snap()).runtime.creationBudget.applied,true);
 });
 await check('rapid cross-borough switching discards stale roots and keeps ownership and root concurrency bounded',async()=>{
  for(let i=0;i<16;i++)await page.locator('#preset').selectOption(['central-south','queensboro-head','bruckner','grove-street'][i%4]);await ready('grove-street');
  await delay(1000);const s=await snap();assert.ok(s.primitives<=18);assert.ok(s.runtime.queue.active<=2);assert.ok(s.runtime.created-s.runtime.destroyed<=18);assert.deepEqual(s.errors,[]);
 });
 await check('Worker query cancellation does not allow older results to replace current identity',async()=>{
  await page.locator('#query').fill('1000');await page.locator('#search-form button').click();await page.locator('#query').fill('id:233256');await page.locator('#search-form button').click();
  await page.waitForFunction(()=>document.getElementById('results').textContent.includes('233256'));await page.locator('#results [data-id]').click();
  await page.waitForFunction(()=>document.getElementById('details').textContent.includes('规范楼高'));const s=await snap();assert.equal(s.selectedId,'nyc:footprints:doitt:233256');assert.ok(s.runtime.search.workerCache.entries<=14);assert.ok(s.runtime.search.workerCache.estimatedBytes<=8388608);
 });
 phase='expected-404';await check('404 stops finite retries while other layers continue',async()=>{
  const pattern='**/environment/gowanus/roads.glb';await page.route(pattern,r=>r.fulfill({status:404,body:'intentional404'}));await page.locator('#preset').selectOption('gowanus');
  await page.waitForFunction(()=>window.__NYC_INSPECTION__.snapshot().tileFailures.some(x=>x.includes('gowanus/roads.glb')),null,{timeout:30000});const before=requests.filter(x=>x.endsWith('/gowanus/roads.glb')).length;await delay(1500);assert.equal(requests.filter(x=>x.endsWith('/gowanus/roads.glb')).length,before);assert.ok(before<=2);await page.unroute(pattern);
 });
 phase='expected-corrupt';await check('corrupt GLB is isolated without per-frame retry or unhandled rejection',async()=>{
  const pattern='**/environment/grove-street/roads.glb';await page.route(pattern,r=>r.fulfill({status:200,contentType:'model/gltf-binary',body:'corrupt-model-test'}));await page.locator('#preset').selectOption('grove-street');
  await page.waitForFunction(()=>window.__NYC_INSPECTION__.snapshot().tileFailures.some(x=>x.includes('grove-street/roads.glb')),null,{timeout:30000});const before=requests.filter(x=>x.endsWith('/grove-street/roads.glb')).length;await delay(1200);assert.equal(requests.filter(x=>x.endsWith('/grove-street/roads.glb')).length,before);await page.unroute(pattern);
 });
 phase='expected-timeout';await check('root timeout aborts after12seconds and leaves a recoverable failed layer',async()=>{
  const pattern='**/environment/highbridge/roads.json';await page.route(pattern,r=>{setTimeout(()=>r.abort().catch(()=>{}),16000);});await page.locator('#preset').selectOption('highbridge');
  await page.waitForFunction(()=>window.__NYC_INSPECTION__.snapshot().layerStates.some(x=>x.key==='roads'&&x.state==='failed'&&x.message.includes('超时')),null,{timeout:22000});await page.unroute(pattern);
 });
 phase='expected-content-timeout';await check('content XHR timeout uses a finite retry and then reports failure',async()=>{
  const pattern='**/environment/queens-plaza/roads.glb';await page.route(pattern,r=>{setTimeout(()=>r.abort().catch(()=>{}),18000);});await page.locator('#preset').selectOption('queens-plaza');
  await page.waitForFunction(()=>window.__NYC_INSPECTION__.snapshot().tileFailures.some(x=>x.includes('queens-plaza/roads.glb')),null,{timeout:42000});const attempts=requests.filter(x=>x.endsWith('/queens-plaza/roads.glb')).length;assert.ok(attempts>=1&&attempts<=2);await delay(1000);assert.equal(requests.filter(x=>x.endsWith('/queens-plaza/roads.glb')).length,attempts);await page.unroute(pattern);
 });
 phase='expected-offline';await check('offline failure retains world state and recovers through explicit cooled retry',async()=>{
  await context.setOffline(true);await page.locator('#preset').selectOption('forest-hills');await page.waitForFunction(()=>window.__NYC_INSPECTION__.snapshot().layerStates.some(x=>x.state==='failed'),null,{timeout:20000});
  await context.setOffline(false);await page.locator('summary').filter({hasText:'来源与诊断'}).click();await page.locator('#retry-layers').click();await ready('forest-hills');assert.ok((await snap()).primitives<=18);
 });phase='normal';
 await check('actual freeze/resume and resize clear input; background visibility observation is recorded',async()=>{
  observations.visibilityBefore=await page.evaluate(()=>document.visibilityState);const second=await context.newPage();await second.goto('about:blank');await second.bringToFront();await delay(500);observations.visibilityWithSecondTab=await page.evaluate(()=>document.visibilityState);await page.bringToFront();await second.close();
  const cdp=await context.newCDPSession(page);await cdp.send('Page.setWebLifecycleState',{state:'frozen'});await delay(500);await cdp.send('Page.setWebLifecycleState',{state:'active'});await page.setViewportSize({width:390,height:844});await page.setViewportSize({width:1440,height:1000});assert.deepEqual((await snap()).keys,[]);
 });
 await check('actual WebGL context loss and restoration reconstruct the viewer and recover the saved view',async()=>{
  const before=await snap();const navigation=page.waitForEvent('framenavigated',{predicate:f=>f===page.mainFrame()});
  const supported=await page.evaluate(()=>{const gl=document.querySelector('#globe canvas').getContext('webgl2'),ext=gl.getExtension('WEBGL_lose_context');if(!ext)return false;setTimeout(()=>ext.restoreContext(),700);ext.loseContext();return true;});assert.equal(supported,true);
  await navigation;await ready(before.preset);await page.waitForFunction(()=>document.getElementById('notice').textContent.includes('图形上下文已重建'));const after=await snap();assert.equal(after.quality,before.quality);assert.equal(after.selectedId,before.selectedId);assert.ok(Math.hypot(...before.cameraWorld.map((x,i)=>x-after.cameraWorld[i]))<1);assert.deepEqual(after.errors,[]);
 });
 await check('local terrain context loss restores only a collision-validated saved ground position',async()=>{
  await page.locator('#mode').selectOption('walk');await page.waitForFunction(()=>document.getElementById('local-view').contentWindow?.__NYC_TERRAIN__?.snapshot().walk.ready,null,{timeout:30000});
  const child=page.frameLocator('#local-view'),before=await child.locator('body').evaluate(()=>window.__NYC_TERRAIN__.snapshot());
  await child.locator('body').evaluate(()=>{const gl=document.querySelector('canvas').getContext('webgl2'),ext=gl.getExtension('WEBGL_lose_context');setTimeout(()=>ext.restoreContext(),700);ext.loseContext();});
  await delay(1000);await page.waitForFunction(()=>document.getElementById('local-view').contentWindow?.__NYC_TERRAIN__?.snapshot().walk.ready,null,{timeout:30000});const after=await child.locator('body').evaluate(()=>window.__NYC_TERRAIN__.snapshot());assert.ok(Math.hypot(...before.walk.position.map((v,i)=>v-after.walk.position[i]))<.01);assert.equal(after.webglError,0);
 });
 assert.deepEqual(errors,[]);await page.screenshot({path:report+'/faults-final.png'});await writeFile(report+'/faults.json',JSON.stringify({at_utc:new Date().toISOString(),checks,errors,expectedConsole,observations,real_mobile_hardware:false,context_recovery:'actual WEBGL_lose_context/restore followed by browser reload and validated view restoration; not in-place GPU restoration',requests},null,2)+'\n');
 console.log('COMPLETE',checks.length,'checks,0unexpected errors');
}catch(e){await writeFile(report+'/faults-failure.json',JSON.stringify({phase,error:String(e),checks,errors,snapshot:page?await snap().catch(()=>null):null},null,2));if(page)await page.screenshot({path:report+'/faults-failure.png'});throw e;}finally{await browser?.close();server.kill();}
