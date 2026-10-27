import {chromium} from 'playwright-core';
import {spawn} from 'node:child_process';
import {mkdir,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {setTimeout as delay} from 'node:timers/promises';
import {hiddenSourceIds,sourceShowExpression} from '../src/landmarks/replacement.ts';
const port=4185,base=`http://127.0.0.1:${port}/`,checks=[],errors=[],requests=[],views=[];
const server=spawn(process.execPath,['node_modules/vite/bin/vite.js','preview','--host','127.0.0.1','--port',String(port),'--strictPort'],{stdio:'ignore'});let browser,page;
async function check(name,fn){await fn();checks.push(name);console.log('PASS',name);}
const snapshot=()=>page.evaluate(()=>window.__NYC_LANDMARKS__.snapshot());
async function ready(slug){await page.waitForFunction(slug=>{const s=window.__NYC_LANDMARKS__?.snapshot();return s?.active===slug&&s.modelLoads>0;},slug,{timeout:120000});await delay(600);}
try{
 await mkdir('reports/stage5/views',{recursive:true});for(let i=0;i<70;i++){try{if((await fetch(base)).ok)break;}catch{}await delay(150);}
 browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const context=await browser.newContext({viewport:{width:1440,height:1000}});await context.route('**/*',r=>new URL(r.request().url()).origin===new URL(base).origin?r.continue():r.abort());page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('request',r=>requests.push(r.url()));
 await page.goto(base+'landmarks.html?diagnostics=1');await ready('one-world-trade-center');
 await check('research, representations and completed fine models remain separate with fixed neutral lighting',async()=>{const s=await snapshot();assert.equal(await page.locator('#directories').innerText(),'29');assert.equal(await page.locator('#representations').innerText(),'2');assert.equal(s.completeCount,0);assert.equal(s.bloom,false);assert.equal(s.globeVisible,false);assert.equal(s.worldBaseRegistered,false);assert.deepEqual(s.errors,[]);});
 await check('One WTC and432 real evidence representations render six explicitly oriented views',async()=>{
  for(const slug of ['one-world-trade-center','432-park-avenue']){
   await page.locator('#landmark').selectOption(slug);await ready(slug);
   for(const key of ['north','east','south','west','high','street']){
    await page.locator('[data-view='+key+']').click();await page.waitForFunction(key=>{const s=window.__NYC_LANDMARKS__.snapshot();return s.view===key&&!s.cameraFlying;},key);await delay(120);const s=await snapshot(),p=s.cameraLocalEnu;
    if(key==='north')assert.ok(p[1]>500);if(key==='south')assert.ok(p[1]<-500);if(key==='east')assert.ok(p[0]>500);if(key==='west')assert.ok(p[0]<-500);if(key==='high')assert.ok(p[2]>s.heightM+100);if(key==='street')assert.ok(Math.abs(p[2]-1.7)<.01);
    assert.equal(s.primitives,1);assert.equal(s.view,key);views.push({slug,view:key,cameraLocalEnu:p,referenceCalibration:'not calibrated, generated view is NOT an acquired reference photo'});await page.screenshot({path:`reports/stage5/views/${slug}-${key}.png`});
   }
  }
 });
 await check('actual merged model component picking keeps original building stable ID',async()=>{
  await page.locator('#landmark').selectOption('one-world-trade-center');await ready('one-world-trade-center');await page.locator('[data-view=south]').click();await delay(700);const rect=await page.locator('canvas').boundingBox();let found=false;
  for(const p of(await snapshot()).pickPoints){if(p.x<10||p.x>rect.width-10||p.y<10||p.y>rect.height-10)continue;await page.mouse.click(rect.x+p.x,rect.y+p.y);if((await snapshot()).selected==='nyc:footprints:doitt:1114961'){found=true;break;}}
  assert.ok(found);assert.match(await page.locator('#selection').innerText(),/nyc:footprints:doitt:1114961/);
 });
 await check('source replacement hides exactly one source building and preserves every loaded neighbour, then restores it',async()=>{
  await page.locator('#context-visible').check();await page.waitForFunction(()=>{const s=window.__NYC_LANDMARKS__.snapshot();return s.contextLoads>0&&s.contextStats.targetHidden===1&&s.contextStats.neighboursVisible>0;},null,{timeout:120000});const a=await snapshot();assert.equal(a.contextStats.neighboursHidden,0);assert.equal(a.contextStats.targetVisible,0);const neighbours=a.contextStats.neighboursVisible;
  await page.locator('#model-visible').uncheck();await page.waitForFunction(()=>window.__NYC_LANDMARKS__.snapshot().contextStats.targetVisible===1);const b=await snapshot();assert.equal(b.contextStats.neighboursVisible,neighbours);assert.equal(b.contextStats.neighboursHidden,0);
  await page.locator('#model-visible').check();await page.waitForFunction(()=>window.__NYC_LANDMARKS__.snapshot().contextStats.targetHidden===1);await page.screenshot({path:'reports/stage5/replacement-neighbours.png'});
 });
 await check('partial podium/tower source cannot be erased by432 grid fragment; invalid mapping cannot hide neighbours',async()=>{
  await page.locator('#landmark').selectOption('432-park-avenue');await ready('432-park-avenue');assert.equal(await page.locator('#context-visible').isDisabled(),true);assert.match(await page.locator('#replacement-note').innerText(),/podium|来源|塔楼|erase/i);assert.equal((await snapshot()).primitives,1);
  const map={eligible:true,building_id:'a',source_part_ids:['a:part:0'],hide_source_building_ids:['a'],physical_world_replacement_allowed:false};assert.deepEqual(hiddenSourceIds(map,true),['a']);assert.deepEqual(hiddenSourceIds(map,false),[]);assert.equal(sourceShowExpression(map,false),'true');assert.throws(()=>hiddenSourceIds({...map,hide_source_building_ids:['neighbour']},true),/邻楼/);assert.throws(()=>hiddenSourceIds({...map,source_part_ids:['p0','p1']},true),/多部件/);
 });
 await check('narrow layout, panel collapse and model switching preserve a usable nonzero viewport',async()=>{
  await page.setViewportSize({width:390,height:844});await delay(350);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.locator('#collapse').click();await delay(350);let rect=await page.locator('canvas').boundingBox();assert.ok(rect.width>300&&rect.height>500);await page.screenshot({path:'reports/stage5/mobile.png'});await page.locator('#collapse').click();await page.locator('#landmark').selectOption('one-world-trade-center');await ready('one-world-trade-center');assert.equal((await snapshot()).primitives,1);assert.equal((await snapshot()).completeCount,0);
 });
 assert.deepEqual(errors,[]);assert.ok(requests.every(u=>new URL(u).origin===new URL(base).origin));await writeFile('reports/stage5/browser.json',JSON.stringify({at:new Date().toISOString(),browser:await browser.version(),checks,errors,requests,generatedViews:views,referenceImagesCalibrated:0,fullyDetailedModelsValidated:0,scope:'runtime and dimension/source checks of partial representations, NOT full current landmark or real-world geometric verification'},null,2));console.log(JSON.stringify({checks:checks.length,errors,views:views.length}));
}catch(e){if(page){await page.screenshot({path:'reports/stage5/browser-failure.png'});await writeFile('reports/stage5/browser-failure.json',JSON.stringify({error:String(e),errors,checks,snapshot:await page.evaluate(()=>window.__NYC_LANDMARKS__?.snapshot())},null,2));}throw e;}finally{await browser?.close();server.kill();}
