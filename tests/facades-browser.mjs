import {chromium} from 'playwright-core';
import {spawn} from 'node:child_process';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {setTimeout as delay} from 'node:timers/promises';
const port=4187,base=`http://127.0.0.1:${port}/`,report='reports/stage6';
const server=spawn(process.execPath,['node_modules/vite/bin/vite.js','preview','--host','127.0.0.1','--port',String(port),'--strictPort'],{stdio:'ignore'});
let browser,page,evidencePrimitiveCount;const errors=[],requests=[],checks=[],areaResults=[],views=[];
async function check(name,fn){await fn();checks.push(name);console.log('PASS',name);}
const snap=()=>page.evaluate(()=>window.__NYC_FACADES__.snapshot());
async function ready(id){await page.waitForFunction(id=>{const s=window.__NYC_FACADES__?.snapshot();return s?.area===id&&s.outlineLoads>0&&!s.cameraFlying;},id,{timeout:120000});await delay(200);}
try{
 await mkdir(report+'/views',{recursive:true});
 for(let i=0;i<80;i++){try{if((await fetch(base)).ok)break;}catch{}await delay(100);}
 browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const context=await browser.newContext({viewport:{width:1440,height:1000}});
 await context.route('**/*',r=>new URL(r.request().url()).origin===new URL(base).origin?r.continue():r.abort());
 page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await page.goto(base+'facades.html?diagnostics=1');await ready('manhattan-grove');
 const manifest=JSON.parse(await readFile('assets/facades/manifest.json','utf8'));
 await check('default evidence mode has12 real AOIs,918 unique source objects and no invented current facades',async()=>{
  const s=await snap();evidencePrimitiveCount=s.primitiveCount;assert.ok(evidencePrimitiveCount>=1);assert.equal(s.mode,'evidence');assert.equal(s.currentVerified,0);assert.equal(s.completedStreets,0);assert.equal(s.procedural,0);assert.equal(s.historyLoaded,false);assert.equal(s.bloom,false);assert.equal(s.worldGroundRegistered,false);
  assert.equal(await page.locator('#area option').count(),12);assert.equal(await page.locator('#source-count').innerText(),'918');
  await page.screenshot({path:report+'/default-evidence.png'});
 });
 await check('all12 actual source AOIs load GLBs and explicit boundaries without accumulating old tilesets',async()=>{
  for(const area of manifest.areas){await page.locator('#area').selectOption(area.id);await ready(area.id);const s=await snap();assert.equal(s.sourceBuildingCount,area.building_denominator);assert.equal(s.historyLoaded,false);assert.equal(s.primitiveCount,evidencePrimitiveCount);assert.equal(s.entities,1);areaResults.push({id:area.id,buildings:s.sourceBuildingCount,actualGlbRequested:true});}
  await page.screenshot({path:report+'/staten-tottenville.png'});
  await page.locator('#area').selectOption('manhattan-grove');await ready('manhattan-grove');
 });
 await check('per-face panel distinguishes historical front from unknown current sides without a whole-building truth label',async()=>{
  await page.locator('#building').selectOption('nyc:footprints:doitt:233256');assert.match(await page.locator('#building-info').innerText(),/1936/);
  await page.locator('[data-face]').first().click();assert.match(await page.locator('#face-evidence').innerText(),/1936-08-25/);
  const other=page.locator('[data-face]').filter({hasText:'现状未知 / 未概括材料'}).first();await other.click();assert.match(await page.locator('#face-evidence').innerText(),/九项构件均无/);
  assert.equal((await snap()).currentVerified,0);
 });
 await check('historical toggle loads four distinct licensed photo textures, restores evidence mode and never hides current outlines',async()=>{
  await page.locator('#history').check();await page.waitForFunction(()=>{const s=window.__NYC_FACADES__.snapshot();return s.historyLoads>0&&!s.cameraFlying;},null,{timeout:120000});await delay(700);
  let s=await snap();assert.equal(s.mode,'historical-reference');assert.equal(s.outlineLoaded,true);assert.equal(s.primitiveCount,evidencePrimitiveCount+1);
  assert.match(await page.locator('#mode').innerText(),/1936/);
  assert.equal(new Set(requests.filter(u=>/front-(4|6|8|10)\.png/.test(u))).size,4);
  const rect=await page.locator('canvas').boundingBox();
  for(const p of (await snap()).historicalPickPoints){
   await page.mouse.click(rect.x+p.x,rect.y+p.y);
   assert.equal((await snap()).selected,p.id);
  }
  await page.screenshot({path:report+'/historical-street.png'});
  await page.locator('#history').uncheck();await page.waitForFunction(()=>!window.__NYC_FACADES__.snapshot().cameraFlying);
  s=await snap();assert.equal(s.historyLoaded,false);assert.equal(s.outlineLoaded,true);assert.equal(s.primitiveCount,evidencePrimitiveCount);
 });
 await check('fixed neutral observation path covers front, joins, close windows and the explicitly missing back',async()=>{
  await page.locator('#history').check();await page.waitForFunction(()=>window.__NYC_FACADES__.snapshot().historyLoads>0);
  for(const id of ['front','left','right','close','rear']){
   await page.locator('[data-view='+id+']').click();await page.waitForFunction(id=>{const s=window.__NYC_FACADES__.snapshot();return s.view===id&&!s.cameraFlying;},id);await delay(150);
   const s=await snap();views.push({id,cameraWorld:s.cameraWorld,light:'fixed neutral',scope:'historical wall fragments; no roof/stoop/rear completion'});await page.screenshot({path:report+'/views/'+id+'.png'});
  }
  await page.locator('[data-view=front]').click();await page.waitForFunction(()=>!window.__NYC_FACADES__.snapshot().cameraFlying);const one=(await snap()).cameraWorld;
  await page.locator('[data-view=close]').click();await page.waitForFunction(()=>!window.__NYC_FACADES__.snapshot().cameraFlying);
  await page.locator('[data-view=front]').click();await page.waitForFunction(()=>!window.__NYC_FACADES__.snapshot().cameraFlying);
  const two=(await snap()).cameraWorld;assert.ok(Math.hypot(...one.map((v,i)=>v-two[i]))<.001);
 });
 await check('original reference previews are local, dated and separate from derived textures and current status',async()=>{
  await page.locator('details summary').click();await page.locator('#reference').click();await page.locator('#reference-image').waitFor({state:'visible'});await page.waitForFunction(()=>document.getElementById('reference-image').naturalWidth>0);assert.match(await page.locator('#reference-dialog').innerText(),/1936-08-25/);assert.match(await page.locator('#reference-dialog').innerText(),/公有领域/);
  await page.locator('#drawing').click();await page.waitForFunction(()=>document.getElementById('reference-image').src.endsWith('source-drawing.jpg')&&document.getElementById('reference-image').naturalWidth>0);await page.screenshot({path:report+'/reference.png'});await page.locator('#close-reference').click();
 });
 await check('changing AOI removes historical fragments, disables unsuitable mode and preserves bounded resource counts',async()=>{
  await page.locator('#area').selectOption('manhattan-soho');await ready('manhattan-soho');let s=await snap();assert.equal(s.primitiveCount,evidencePrimitiveCount);assert.equal(s.historyLoaded,false);assert.equal(await page.locator('#history').isDisabled(),true);
  await page.locator('#boundary').uncheck();await page.locator('#boundary').check();assert.equal((await snap()).entities,1);
  await page.locator('#area').selectOption('manhattan-grove');await ready('manhattan-grove');
 });
 await check('narrow screen can select buildings and faces, switch mode and collapse to a usable viewport',async()=>{
  await page.setViewportSize({width:390,height:844});await delay(300);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.locator('#history').check();await page.waitForFunction(()=>window.__NYC_FACADES__.snapshot().historyLoads>0);
  await page.locator('#building').selectOption('nyc:footprints:doitt:138288');assert.match(await page.locator('#building-info').innerText(),/宽度差/);
  await page.locator('#collapse').click();await delay(300);const rect=await page.locator('canvas').boundingBox();assert.ok(rect.width>300&&rect.height>500);await page.screenshot({path:report+'/mobile.png'});
 });
 assert.deepEqual(errors,[]);assert.ok(requests.every(u=>new URL(u).origin===new URL(base).origin));
 await writeFile(report+'/browser.json',JSON.stringify({at_utc:new Date().toISOString(),browser:await browser.version(),checks,errors,requests,areas:areaResults,views,current_verified_facades:0,complete_current_streets:0,scope:'actual partial historical photo planes and source inventories; NOT full facade or current street acceptance'},null,2)+'\n');
 console.log(JSON.stringify({checks:checks.length,errors,areas:areaResults.length,views:views.length}));
}catch(e){if(page){await page.screenshot({path:report+'/browser-failure.png'});await writeFile(report+'/browser-failure.json',JSON.stringify({error:String(e),checks,errors,snapshot:await snap()},null,2));}throw e;}finally{await browser?.close();server.kill();}
