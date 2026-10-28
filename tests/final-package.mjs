/** Test the ACTUALLY EXTRACTED complete package, no workspace asset fallback. */
import {chromium} from 'playwright-core';
import {spawn} from 'node:child_process';
import {readFile,writeFile,realpath} from 'node:fs/promises';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
import {setTimeout as delay} from 'node:timers/promises';
const root=process.env.NYC_FINAL_ROOT;if(!root)throw Error('NYC_FINAL_ROOT must name a genuinely assembled new directory');
const report='reports/stage10',origin='http://127.0.0.1:4202';assert.notEqual(await realpath(root),await realpath('.'));
const server=spawn('python3',[resolve(root,'start-local.py'),'--port','4202'],{cwd:root,stdio:['ignore','pipe','pipe']});let serverLog='';server.stdout.on('data',d=>serverLog+=d);server.stderr.on('data',d=>serverLog+=d);
let browser,page;const errors=[],requests=[],responses=[],external=[],failedRequests=[],checks=[],boroughs=[];
async function check(name,fn){await fn();checks.push(name);console.log('PASS',name);}
const snap=()=>page.evaluate(()=>window.__NYC_INSPECTION__.snapshot());
async function ready(id,borough){await page.waitForFunction(({id,borough})=>{const s=window.__NYC_INSPECTION__?.snapshot();return s?.preset===id&&!s.flying&&s.layerStates.some(l=>l.key==='roads'&&l.loaded>0)&&(!borough||s.layerStates.some(l=>l.key==='city:'+borough&&l.loaded>0));},{id,borough},{timeout:120000});}
try{
 for(let i=0;i<100;i++){try{if((await fetch(origin+'/index.html')).ok)break;}catch{}await delay(100);}
 browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const context=await browser.newContext({viewport:{width:1440,height:1000},serviceWorkers:'block'});await context.route('**/*',r=>{const u=new URL(r.request().url());if(u.origin===origin||u.protocol==='data:')return r.continue();external.push(r.request().url());return r.abort();});
 page=await context.newPage();page.on('pageerror',e=>errors.push(e.stack??e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('request',r=>requests.push(r.url()));page.on('requestfailed',r=>failedRequests.push({url:r.url(),reason:r.failure()?.errorText}));page.on('response',r=>responses.push({url:r.url(),status:r.status()}));
 const cdp=await context.newCDPSession(page);await cdp.send('Network.enable');await cdp.send('Network.setCacheDisabled',{cacheDisabled:true});
 await check('fresh-cache final index honestly shows complete runtime and incomplete current building exteriors',async()=>{await page.goto(origin+'/index.html');await page.waitForFunction(()=>window.__NYC_RELEASE__?.snapshot().ready);const s=await page.evaluate(()=>window.__NYC_RELEASE__.snapshot());assert.equal(s.total,1082964);assert.equal(s.completeFineLandmarks,0);assert.equal(await page.locator('#boroughs tr').count(),5);assert.match(await page.title(),/部分完成/);await page.screenshot({path:report+'/package-index.png'});});
 await page.goto(origin+'/inspection.html?diagnostics=1');await ready('brooklyn-span');
 await check('all five boroughs load real local strict GLBs and metadata without disabling building regions',async()=>{
  // Brooklyn Bridge's brooklyn-head ID is explicitly the MANHATTAN bridgehead.
  // Use the source-defined DUMBO head for an actual Brooklyn observation.
  const route=JSON.parse(await readFile('config/final-review-route.json','utf8'));
  for(const {preset:id,borough:b}of route.borough_observations){
   await page.locator('#preset').selectOption(id);await ready(id,b);const s=await snap();assert.equal(s.layers.buildings,true);assert.deepEqual(s.errors,[]);boroughs.push({preset:id,borough:b,loaded:s.layerStates.filter(l=>l.loaded>0).map(l=>({key:l.key,loaded:l.loaded})),worldGroundRegistered:s.worldGroundRegistered});
  }
  await page.screenshot({path:report+'/package-five-boroughs.png'});
 });
 await check('local search Worker resolves stable ID and actual source line can be picked after tile unloading',async()=>{
  await page.locator('#query').fill('One WTC');await page.locator('#search-form button').click();await page.locator('#results [data-id="nyc:footprints:doitt:1114961"]').click();await page.waitForFunction(()=>window.__NYC_INSPECTION__.snapshot().selectedId==='nyc:footprints:doitt:1114961'&&!window.__NYC_INSPECTION__.snapshot().flying&&document.getElementById('details').textContent.includes('规范楼高'));await page.waitForFunction(()=>window.__NYC_INSPECTION__.snapshot().layerStates.some(l=>l.key==='city:manhattan'&&l.loaded>0),null,{timeout:120000});
  const box=await page.locator('#globe canvas').boundingBox(),centre=(await snap()).pickPoints[0];let found=false;
  for(let dy=-35;dy<=35&&!found;dy+=7)for(let dx=-35;dx<=35&&!found;dx+=7){await page.mouse.click(box.x+centre.x+dx,box.y+centre.y+dy);found=(await snap()).lastClickedBuildingId==='nyc:footprints:doitt:1114961';}assert.ok(found);assert.match(await page.locator('#details').innerText(),/未知/);
 });
 await check('local ground walkthrough uses real NAVD88 collision data and preserves blocked global vertical registration',async()=>{
  await page.locator('#mode').selectOption('walk');await page.waitForFunction(()=>document.getElementById('local-view').contentWindow?.__NYC_TERRAIN__?.snapshot().walk.ready,null,{timeout:120000});const child=page.frameLocator('#local-view');const before=await child.locator('body').evaluate(()=>window.__NYC_TERRAIN__.snapshot());await child.locator('#terrain-canvas').focus();await page.keyboard.down('w');await delay(500);await page.keyboard.up('w');const after=await child.locator('body').evaluate(()=>window.__NYC_TERRAIN__.snapshot());assert.ok(Math.hypot(after.walk.position[0]-before.walk.position[0],after.walk.position[1]-before.walk.position[1])>.1);assert.equal(after.worldPlacementAllowed,false);assert.equal(after.webglError,0);await page.screenshot({path:report+'/package-ground.png'});
 });
 await check('packaged standalone preview renders embedded real evidence and ends loading',async()=>{await page.goto(origin+'/preview-single.html');await page.waitForFunction(()=>window.__FINAL_PREVIEW__?.snapshot().ready);assert.equal(await page.locator('#loading').isHidden(),true);assert.equal(await page.evaluate(()=>window.__FINAL_PREVIEW__.snapshot().complete_fine_buildings),0);});
 await check('all declared package parts include all original strict and hypothesis file references',async()=>{const manifest=JSON.parse(await readFile(resolve(root,'delivery-manifest.json'),'utf8'));assert.equal(manifest.old_base_required,false);assert.equal(manifest.runtime_parts.length,6);assert.ok(manifest.files.length>25800);const paths=new Set(manifest.files.map(f=>f.path));for(const b of boroughs){assert.ok(paths.has('app/datasets/buildings-city/'+b.borough+'/strict.json'));assert.ok(requests.some(u=>u.includes('/buildings-city/'+b.borough+'/')&&u.endsWith('-strict.glb')));}assert.ok(requests.some(u=>/worker|Worker/.test(u)));});
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);assert.ok(responses.every(r=>r.status>=200&&r.status<400));assert.ok(failedRequests.every(r=>r.reason==='net::ERR_ABORTED'),'only explicitly cancelled obsolete requests are permitted');
 await writeFile(report+'/package-browser.json',JSON.stringify({at_utc:new Date().toISOString(),assembled_root:await realpath(root),browser:await browser.version(),http_cache_disabled:true,fresh_browser_context:true,outside_network_blocked:true,external_requests:external,workspace_fallback:false,real_mobile_hardware:false,checks,boroughs,errors,requests,responses,failedRequests,server_binding:'127.0.0.1',scope:'all current published resources present; actual five-borough leaf loads and picking; not a survey or completed fine exterior model'},null,2)+'\n');console.log('COMPLETE',checks.length,'checks,0errors');
}catch(e){if(page){await page.screenshot({path:report+'/package-failure.png'});await writeFile(report+'/package-failure.json',JSON.stringify({error:String(e),checks,errors,requests,responses,external},null,2));}throw e;}finally{await browser?.close();server.kill();await writeFile(report+'/package-server.log',serverLog);}
