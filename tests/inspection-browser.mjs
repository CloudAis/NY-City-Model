import {chromium} from 'playwright-core';
import {spawn} from 'node:child_process';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {setTimeout as delay} from 'node:timers/promises';
const port=4190,base=`http://127.0.0.1:${port}/`,report='reports/stage8';
const server=spawn(process.execPath,['node_modules/vite/bin/vite.js','preview','--host','127.0.0.1','--port',String(port),'--strictPort'],{stdio:'ignore'});
let browser,page;const checks=[],errors=[],requests=[],observations=[],downloads=[],intentionalFailures=[];
const snap=()=>page.evaluate(()=>window.__NYC_INSPECTION__.snapshot());
async function check(name,fn){await fn();checks.push(name);console.log('PASS',name);}
async function ready(id){await page.waitForFunction(id=>{const s=window.__NYC_INSPECTION__?.snapshot();return s?.preset===id&&!s.flying&&s.layerStates.some(l=>l.key==='roads'&&l.loaded>0);},id,{timeout:120000});}
async function query(value){await page.locator('#query').fill(value);await page.locator('#search-form button').click();await page.waitForFunction(()=>!/正在/.test(document.getElementById('search-status').textContent));}
try{
 await mkdir(report+'/observations',{recursive:true});
 for(let i=0;i<80;i++){try{if((await fetch(base)).ok)break;}catch{}await delay(100);}
 browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
 await context.route('**/*',r=>new URL(r.request().url()).origin===new URL(base).origin?r.continue():r.abort());
 page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));
 page.on('console',m=>{if(m.type()==='error'&&!intentionalFailures.length)errors.push(m.text());});
 await page.goto(base+'inspection.html?diagnostics=1');await ready('brooklyn-span');
 await check('full source index,25 genuine presets and default reference limits are visible',async()=>{
  assert.equal(await page.locator('#preset option').count(),25);
  assert.match(await page.locator('#search-status').innerText(),/1,082,964/);
  const s=await snap();assert.equal(s.worldGroundRegistered,false);assert.equal(s.solarDatetime,null);assert.ok(s.cameraHeight>=799);
  await page.screenshot({path:report+'/initial.png'});
 });
 const manifest=JSON.parse(await readFile('assets/environment/manifest.json','utf8'));
 await check('25 river,bridgehead,pier,interchange,park and slope presets load actual local environment',async()=>{
  await page.locator('[data-layer=buildings]').uncheck();
  for(const p of manifest.observations){
   await page.locator('#preset').selectOption(p.id);await ready(p.id);await delay(150);
   const s=await snap();assert.ok(s.cameraHeight>=799);assert.ok(s.layerStates.filter(l=>!l.key.startsWith('city:')).length<=12);
   observations.push({id:p.id,kind:p.kind,cameraHeight:s.cameraHeight,actualLoaded:s.layerStates.filter(l=>l.loaded>0).map(l=>l.key),verticalPhysicalAcceptance:false});
   await page.screenshot({path:report+'/observations/'+p.id+'.png'});
  }
  await page.locator('[data-layer=buildings]').check();
  await writeFile('reports/stage7/observation-views.json',JSON.stringify({at_utc:new Date().toISOString(),observations,scope:'actual navigation/reference observations, not field surveys or verified bridge heights'},null,2)+'\n');
 });
 await check('BIN,name,alias,address andborough queries resolve stable IDs; missing records do not crash',async()=>{
  await query('One WTC');assert.ok(await page.locator('#results [data-id]').count());await page.locator('#results [data-id="nyc:footprints:doitt:1114961"]').click();await page.waitForFunction(()=>window.__NYC_INSPECTION__.snapshot().selectedId==='nyc:footprints:doitt:1114961'&&!window.__NYC_INSPECTION__.snapshot().flying&&document.getElementById('details').textContent.includes('规范楼高'));assert.match(await page.locator('#details').innerText(),/规范楼高 \/ 基底：未知/);
  await page.waitForFunction(()=>window.__NYC_INSPECTION__.snapshot().layerStates.some(l=>l.key==='city:manhattan'&&l.loaded>0),null,{timeout:120000});
  const box=await page.locator('#globe canvas').boundingBox(),centre=(await snap()).pickPoints[0];let clicked;
  for(let dy=-35;dy<=35&&!clicked;dy+=7)for(let dx=-35;dx<=35&&!clicked;dx+=7){await page.mouse.click(box.x+centre.x+dx,box.y+centre.y+dy);if((await snap()).lastClickedBuildingId==='nyc:footprints:doitt:1114961')clicked={x:box.x+centre.x+dx,y:box.y+centre.y+dy};}
  assert.ok(clicked,'actual source-line picking found target stableID');await page.mouse.move(clicked.x,clicked.y);await page.waitForFunction(()=>window.__NYC_INSPECTION__.snapshot().hoverId==='nyc:footprints:doitt:1114961');
  await query('4 Grove Street');assert.match(await page.locator('#results').innerText(),/233256/);
  await query('1088469');assert.ok(await page.locator('#results [data-id]').count());
  await page.locator('#borough').selectOption('queens');await page.waitForFunction(()=>!/正在/.test(document.getElementById('search-status').textContent));assert.equal(await page.locator('#results [data-id]').count(),0);
  await page.locator('#borough').selectOption('');await query('id:9999999999999');assert.equal(await page.locator('#results [data-id]').count(),0);
  await query('id:233256');await page.locator('#results [data-id]').click();await page.waitForFunction(()=>window.__NYC_INSPECTION__.snapshot().selectedId==='nyc:footprints:doitt:233256'&&!window.__NYC_INSPECTION__.snapshot().flying&&document.getElementById('details').textContent.includes('规范楼高'));
 });
 await check('flight cancellation,return selected,top andcity reset preserve camera limits and selection',async()=>{
  await page.locator('#preset').selectOption('central-reservoir');await page.locator('#cancel-flight').click();let s=await snap();assert.equal(s.flying,false);
  const before=s.cameraWorld;await delay(350);s=await snap();assert.ok(Math.hypot(...before.map((v,i)=>v-s.cameraWorld[i]))<1);
  await page.locator('#return-selected').click();await page.waitForFunction(()=>!window.__NYC_INSPECTION__.snapshot().flying);
  await page.locator('#mode').selectOption('top');await page.waitForFunction(()=>!window.__NYC_INSPECTION__.snapshot().flying);assert.ok((await snap()).pitch<-1.55);
  await page.locator('#city-reset').click();await page.waitForFunction(()=>!window.__NYC_INSPECTION__.snapshot().flying);assert.ok((await snap()).cameraHeight>50000);
  await page.screenshot({path:report+'/city.png'});
  await page.locator('#camera-reset').click();await ready('central-reservoir');
 });
 await check('freeflight uses actual keys and stops on keyup,blur,pointer cancellation andresize',async()=>{
  await page.locator('#mode').selectOption('fly');const canvas=page.locator('#globe canvas');await canvas.focus();const a=(await snap()).cameraWorld;
  await page.keyboard.down('w');await delay(450);await page.keyboard.up('w');const b=(await snap()).cameraWorld;assert.ok(Math.hypot(...a.map((v,i)=>v-b[i]))>3);
  const c=(await snap()).cameraWorld;await delay(250);const d=(await snap()).cameraWorld;assert.ok(Math.hypot(...c.map((v,i)=>v-d[i]))<.1);
  await canvas.focus();await page.keyboard.down('w');await delay(150);await page.locator('#query').focus();assert.deepEqual((await snap()).keys,[]);await page.keyboard.up('w');
  await canvas.focus();await page.keyboard.down('w');await page.dispatchEvent('#globe canvas','pointercancel',{pointerId:1});assert.deepEqual((await snap()).keys,[]);await page.keyboard.up('w');
  await page.setViewportSize({width:1360,height:900});await delay(100);assert.deepEqual((await snap()).keys,[]);
  await page.setViewportSize({width:1440,height:1000});
 });
 await check('point reading and two-point measurement distinguish unknown world height from horizontal distance',async()=>{
  await page.locator('#mode').selectOption('top');await page.waitForFunction(()=>!window.__NYC_INSPECTION__.snapshot().flying);
  await page.getByText('读取与量测',{exact:true}).click();await page.locator('#point-tool').click();
  const r=await page.locator('#globe canvas').boundingBox();await page.mouse.click(r.x+r.width*.4,r.y+r.height*.55);assert.match(await page.locator('#measurement').innerText(),/真实高程未知/);
  await page.locator('#measure-tool').click();await page.mouse.click(r.x+r.width*.38,r.y+r.height*.5);await page.mouse.click(r.x+r.width*.62,r.y+r.height*.5);assert.match(await page.locator('#measurement').innerText(),/水平测地距离≈/);assert.match(await page.locator('#measurement').innerText(),/高差不可用/);await page.locator('#clear-measure').click();
 });
 await check('camera bookmarks save and restore view,layers and quality; invalid import preserves current records',async()=>{
  await page.getByText('相机书签',{exact:true}).click();await page.locator('#bookmark-name').fill('verified test view');await page.locator('#quality').selectOption('low');await page.locator('[data-layer=water]').uncheck();
  await page.locator('#save-bookmark').click();await page.waitForFunction(()=>window.__NYC_INSPECTION__.snapshot().bookmarks.length===1);const b=(await snap()).bookmarks[0];
  await page.locator('#quality').selectOption('high');await page.locator('[data-layer=water]').check();await page.locator('[data-bookmark="0"]').click();await delay(300);let s=await snap();assert.equal(s.quality,'low');assert.equal(s.layers.water,false);assert.ok(Math.hypot(...b.camera.position.map((v,i)=>v-s.cameraWorld[i]))<1);
  await page.locator('#import-bookmarks').setInputFiles({name:'invalid.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify({schema:99,bookmarks:[]}))});assert.equal((await snap()).bookmarks.length,1);assert.match(await page.locator('#notice').innerText(),/导入拒绝/);
  const download=page.waitForEvent('download');await page.locator('#export-bookmarks').click();const file=await download;await file.saveAs(report+'/bookmarks.json');downloads.push(file.suggestedFilename());
 });
 await check('restricted local NAVD88 walk moves on actual ground and stops on blur without snapping to bridges',async()=>{
  await page.locator('#mode').selectOption('walk');
  await page.waitForFunction(()=>document.getElementById('local-view').contentWindow?.__NYC_TERRAIN__?.snapshot().walk.ready,null,{timeout:120000});
  const child=page.frameLocator('#local-view'),canvas=child.locator('#terrain-canvas');
  let s=await child.locator('body').evaluate(()=>window.__NYC_TERRAIN__.snapshot());assert.equal(s.datum,'NAVD88');assert.equal(s.walk.layer,'ground');assert.equal(s.walk.eyeHeight,1.7);assert.ok(s.walk.collisionTriangles>0);
  const a=s.walk.position;await canvas.focus();await page.keyboard.down('w');await delay(500);await page.keyboard.up('w');s=await child.locator('body').evaluate(()=>window.__NYC_TERRAIN__.snapshot());assert.ok(Math.hypot(s.walk.position[0]-a[0],s.walk.position[1]-a[1])>.1);assert.ok(Math.hypot(s.walk.position[0]-a[0],s.walk.position[1]-a[1])<1.1);
  await canvas.focus();await page.keyboard.down('d');await page.locator('#bookmark-name').focus();s=await child.locator('body').evaluate(()=>window.__NYC_TERRAIN__.snapshot());assert.deepEqual(s.walk.keys,[]);await page.keyboard.up('d');
  await page.locator('#bookmark-name').fill('local ground');await page.locator('#save-bookmark').click();await page.waitForFunction(()=>window.__NYC_INSPECTION__.snapshot().bookmarks.length===2);assert.ok((await snap()).bookmarks[0].localWalk);
  await page.screenshot({path:report+'/ground-walk.png'});
  for(const id of ['central-park','prospect-park']){await page.locator('#walk-area').selectOption(id);await page.waitForFunction(id=>{const s=document.getElementById('local-view').contentWindow?.__NYC_TERRAIN__?.snapshot();return s?.id===id&&s.walk.ready;},id,{timeout:120000});const p=await child.locator('body').evaluate(()=>window.__NYC_TERRAIN__.snapshot());assert.ok(p.walk.collisionTriangles>100);assert.equal(p.worldPlacementAllowed,false);await page.screenshot({path:report+'/'+id+'-ground.png'});}
  await page.locator('#mode').selectOption('orbit');
 });
 await check('layer toggles and rapid source switches keep stable IDs without unbounded stale loads',async()=>{
  for(const id of ['pier40','queensboro-head','st-george-slope','prospect-lake'])await page.locator('#preset').selectOption(id);
  await ready('prospect-lake');assert.equal((await snap()).preset,'prospect-lake');assert.ok((await snap()).primitives<=18);
  await page.locator('[data-layer=trees]').check();await page.waitForFunction(()=>window.__NYC_INSPECTION__.snapshot().layerStates.some(l=>l.key==='trees'&&l.loaded>0));await page.locator('[data-layer=trees]').uncheck();
  await page.screenshot({path:report+'/park.png'});
 });
 await check('screenshot export includes data attribution beyond the raw WebGL canvas',async()=>{
  const waiting=page.waitForEvent('download');await page.locator('#screenshot').click();const file=await waiting;await file.saveAs(report+'/attributed.png');assert.match((await snap()).lastExportCredit,/NYC OTI/);downloads.push(file.suggestedFilename());
 });
 await check('one failed source tile is reported while remaining environment and city browsing continue',async()=>{
  intentionalFailures.push('grove-street/roads.glb');
  await page.route('**/environment/grove-street/roads.glb',r=>r.fulfill({status:404,contentType:'text/plain',body:'intentional missing tile test'}));
  await page.locator('#preset').selectOption('grove-street');await page.waitForFunction(()=>window.__NYC_INSPECTION__.snapshot().tileFailures.some(u=>u.includes('grove-street/roads.glb')),null,{timeout:120000});
  assert.ok((await snap()).layerStates.some(l=>l.key!=='roads'&&l.loaded>0));await page.locator('#preset').selectOption('brooklyn-head');await ready('brooklyn-head');await page.unroute('**/environment/grove-street/roads.glb');
 });
 await check('emulated mobile touch zoom and pan,resize and collapse leave a usable viewport',async()=>{
  await page.setViewportSize({width:390,height:844});await page.locator('#collapse').click();await delay(250);let rect=await page.locator('#globe canvas').boundingBox();assert.ok(rect.width>300&&rect.height>600);
  const cdp=await context.newCDPSession(page);await cdp.send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:2});
  const x=rect.x+rect.width*.5,y=rect.y+rect.height*.5,before=(await snap()).cameraHeight;
  await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:x-35,y,id:1},{x:x+35,y,id:2}]});
  for(let i=1;i<=6;i++){await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x-35-i*3,y:y+i*2,id:1},{x:x+35+i*3,y:y+i*2,id:2}]});await delay(35);}
  await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await delay(300);assert.ok(Number.isFinite((await snap()).cameraHeight));
  assert.ok(Math.abs((await snap()).cameraHeight-before)>.1);
  await page.setViewportSize({width:844,height:390});await delay(250);rect=await page.locator('#globe canvas').boundingBox();assert.ok(rect.width>800&&rect.height>250);
  await page.setViewportSize({width:390,height:844});await delay(150);await page.screenshot({path:report+'/mobile.png'});
 });
 assert.deepEqual(errors,[]);assert.deepEqual((await snap()).errors,[]);assert.ok(requests.every(u=>new URL(u).origin===new URL(base).origin));
 await writeFile(report+'/browser.json',JSON.stringify({at_utc:new Date().toISOString(),browser:await browser.version(),checks,errors,requests,observations,downloads,intentionalFailures,real_mobile_hardware:false,global_vertical_physical_acceptance:false,scope:'actual desktop/headless softwareWebGL and emulated touch; physical height/bridge limits retained'},null,2)+'\n');
 console.log(JSON.stringify({checks:checks.length,observations:observations.length,errors}));
}catch(e){if(page){await page.screenshot({path:report+'/browser-failure.png'});await writeFile(report+'/browser-failure.json',JSON.stringify({error:String(e),checks,errors,snapshot:await snap()},null,2));}throw e;}finally{await browser?.close();server.kill();}
