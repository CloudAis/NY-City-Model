import {chromium} from 'playwright-core';
import {spawn} from 'node:child_process';
import {mkdir,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {setTimeout as delay} from 'node:timers/promises';

const reportDir=process.env.NYC_REPORT_DIR||'reports/stage3',reportPath=name=>reportDir+'/'+name;
const port=4183,base=`http://127.0.0.1:${port}/`,checks=[],errors=[],requests=[],observations={};let browser,page;
const server=spawn(process.execPath,['node_modules/vite/bin/vite.js','preview','--host','127.0.0.1','--port',String(port),'--strictPort'],{stdio:'ignore'});
async function stableCamera(){let previous='';let equal=0;for(let i=0;i<80;i++){const camera=await page.evaluate(()=>window.__NYC__.snapshot().camera);const key=JSON.stringify(camera);equal=key===previous?equal+1:0;if(equal>=4)return;previous=key;await delay(250);}throw new Error('camera did not settle');}
async function check(name,fn){await fn();checks.push(name);console.log('PASS',name);}
try{
 await mkdir(reportDir,{recursive:true});for(let i=0;i<60;i++){try{if((await fetch(base)).ok)break;}catch{}await delay(150);}
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const context=await browser.newContext({viewport:{width:1440,height:1000}});await context.route('**/*',r=>new URL(r.request().url()).origin===new URL(base).origin?r.continue():r.abort());
 await context.addInitScript(()=>{const live=new Set(),create=WebGL2RenderingContext.prototype.createBuffer,remove=WebGL2RenderingContext.prototype.deleteBuffer;WebGL2RenderingContext.prototype.createBuffer=function(...args){const b=create.apply(this,args);if(b)live.add(b);return b;};WebGL2RenderingContext.prototype.deleteBuffer=function(b){live.delete(b);return remove.call(this,b);};Object.defineProperty(window,'__LIVE_GL_BUFFERS__',{get:()=>live.size});});
 page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('request',r=>requests.push(r.url()));
 await page.goto(base+'?diagnostics=1');await page.waitForFunction(()=>window.__NYC__?.snapshot().loaded===6&&window.__NYC__.snapshot().foundation?.active==='lower-manhattan'&&window.__NYC__.snapshot().camera.height<5000,null,{timeout:120000});await delay(1600);
 const main=()=>page.evaluate(()=>window.__NYC__.snapshot());
 await check('existing real footprint picking survives explicit unresolved elevation fields',async()=>{
  const s=await main(),rect=await page.locator('canvas').first().boundingBox();let found=false;
  for(const p of s.pickPoints){if(p.x<50||p.x>rect.width-50||p.y<70||p.y>rect.height-70)continue;await page.mouse.click(rect.x+p.x,rect.y+p.y);if((await main()).selected){found=true;break;}}
  assert.ok(found);assert.match(await page.locator('#details').innerText(),/英尺种类未解决|单位待核|未知/);assert.equal(s.recordCount,3027);assert.equal(s.foundation.globalTerrainRegistered,false);
 });
 await check('real water, roads, metric grid, ground reference points and tile bounds toggle independently',async()=>{
  await page.locator('#layer-controls>summary').click();for(const key of ['water','roads','grid','samples','bounds']){await page.locator('#layer-'+key).check();const s=await main();assert.equal(s.foundation.layers[key].show,true);assert.ok(s.foundation.layers[key].entities>0);}
  await delay(1400);await page.screenshot({path:reportPath('globe-layers.png')});observations.mainLayers=(await main()).foundation.layers;
  await page.locator('#layer-north').uncheck();assert.equal(await page.locator('#north-indicator').isVisible(),false);await page.locator('#layer-north').check();await page.locator('#layer-footprints').uncheck();assert.ok((await main()).tiles.every(t=>!t.show));await page.locator('#layer-footprints').check();
 });
 await check('actual glTF feature picking verifies East West North South Up Down with one engine rotation',async()=>{
  for(const key of ['water','roads','grid','samples','bounds'])await page.locator('#layer-'+key).uncheck();
  await page.locator('#fit-axes').click();await page.waitForFunction(()=>window.__NYC__.snapshot().foundation.axisGlbLoaded&&window.__NYC__.snapshot().camera.height<1200,null,{timeout:120000});await delay(1200);const s=await main();observations.axes=s.foundation.axesPoints;
  for(const p of s.foundation.axesPoints)assert.equal(p.pickedAxis,'diagnostic:'+p.axis,`real GLB pick at expected ${p.axis} ENU midpoint`);
  assert.equal(s.foundation.axesPoints.length,6);assert.ok(requests.some(url=>url.endsWith('/axes-diagnostic.glb')));await page.screenshot({path:reportPath('axes-six-directions.png')});await page.locator('#layer-axes').uncheck();
 });
 await check('whole-city ECEF view stays numerically stable and keeps unresolved global terrain blocked',async()=>{
  const selected=(await main()).selected;if(selected){await page.locator('#buildings').selectOption(selected);await delay(1100);await stableCamera();const nearA=await main();await delay(700);const nearB=await main();assert.deepEqual(nearA.camera,nearB.camera);observations.nearBuilding={camera:nearA.camera,stable:true};await page.screenshot({path:reportPath('building-near-view.png')});}
  await page.locator('#city-overview').click();await page.waitForFunction(()=>window.__NYC__.snapshot().camera.height>25000);await delay(1200);await stableCamera();const a=await main();const shot1=await page.locator('#globe').screenshot();await delay(1100);const b=await main();const shot2=await page.locator('#globe').screenshot();assert.deepEqual(a.camera,b.camera);assert.equal(a.foundation.globalTerrainRegistered,false);observations.city={camera:a.camera,pixelHashFirst:createHash('sha256').update(shot1).digest('hex'),pixelHashSecond:createHash('sha256').update(shot2).digest('hex'),samePixelBuffer:shot1.equals(shot2),globalRegisteredTerrainTest:'blocked by source-frame conflict; no terrain floating/sinking success claim'};await page.screenshot({path:reportPath('city-overview.png')});
 });
 await check('switching all six source areas releases old diagnostic data sources',async()=>{
  for(const key of ['water','roads','grid','samples','bounds'])await page.locator('#layer-'+key).uncheck();for(const d of(await main()).catalog.datasets){await page.locator(`[data-area="${d.id}"]`).click();await page.waitForFunction(id=>window.__NYC__.snapshot().foundation.active===id,d.id,{timeout:120000});}
  const s=await main();assert.equal(s.recordCount,3027);assert.equal(Object.keys(s.foundation.layers).length,5);assert.equal(s.foundation.dataSourceCount,5);observations.finalGlobe=s.foundation;
 });
 await page.goto(base+'terrain.html?diagnostics=1');await page.waitForFunction(()=>window.__NYC_TERRAIN__?.snapshot().draws>0,null,{timeout:120000});const terrain=()=>page.evaluate(()=>window.__NYC_TERRAIN__.snapshot());
 await check('actual bare-earth orthometric mesh renders source-derived terrain pixels without global-datum substitution',async()=>{
  const s=await terrain();assert.equal(s.datum,'NAVD88');assert.equal(s.worldPlacementAllowed,false);assert.equal(s.exaggeration,1);assert.equal(s.tiles,4);assert.ok(s.triangles>1000&&s.triangles<8192);assert.equal(s.webglError,0);
  const pixels=await page.locator('canvas').evaluate(c=>{const gl=c.getContext('webgl2'),p=new Uint8Array(c.width*c.height*4);gl.readPixels(0,0,c.width,c.height,gl.RGBA,gl.UNSIGNED_BYTE,p);let terrain=0,water=0;for(let i=0;i<p.length;i+=16){if(p[i+1]>75&&p[i]>40)terrain++;if(p[i+2]>80&&p[i+1]>70&&p[i]<80)water++;}return{terrain,water};});assert.ok(pixels.terrain>2000);observations.terrainPixels=pixels;await page.screenshot({path:reportPath('terrain-lower-manhattan.png')});
 });
 await check('six real terrain crops retain varying source elevations and release GPU buffers between loads',async()=>{
  observations.terrainAreas=[];for(const id of ['lower-manhattan','midtown','brooklyn-dumbo','queens-lic','bronx-mott-haven','staten-st-george']){await page.locator('#terrain-area').selectOption(id);await page.waitForFunction(id=>window.__NYC_TERRAIN__.snapshot().id===id&&document.getElementById('terrain-loading').hidden,id,{timeout:120000});await delay(100);const s=await terrain();assert.equal(s.webglError,0);assert.equal(await page.evaluate(()=>window.__LIVE_GL_BUFFERS__),s.buffers);observations.terrainAreas.push({id,source:s.sourceRaster,range:s.heightRange,buffers:s.buffers});}
  assert.ok((await terrain()).heightRange[1]>60);await page.screenshot({path:reportPath('terrain-staten-island.png')});
 });
 await check('orthometric camera, raycast sampling, all diagnostic layers and narrow layout work without height mutation',async()=>{
  const before=await terrain(),rect=await page.locator('canvas').boundingBox();for(const key of ['grid','samples','bounds'])await page.locator('#terrain-'+key).check();await page.mouse.move(rect.x+rect.width*.5,rect.y+rect.height*.5);await page.mouse.down();await page.mouse.move(rect.x+rect.width*.58,rect.y+rect.height*.55,{steps:8});await page.mouse.up();await page.mouse.wheel(0,-100);await delay(250);assert.notDeepEqual((await terrain()).camera,before.camera);await page.mouse.click(rect.x+rect.width*.5,rect.y+rect.height*.5);assert.ok((await terrain()).lastPick);assert.equal((await terrain()).lastPick.datum,'NAVD88');assert.equal((await terrain()).worldPlacementAllowed,false);assert.deepEqual((await terrain()).heightRange,before.heightRange);await page.screenshot({path:reportPath('terrain-diagnostics.png')});
  await page.setViewportSize({width:390,height:844});await page.locator('#terrain-panel').click();await delay(200);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:reportPath('terrain-mobile.png')});await page.locator('#terrain-panel').click();assert.equal((await terrain()).exaggeration,1);
 });
 assert.deepEqual(errors,[]);assert.ok(requests.every(url=>new URL(url).origin===new URL(base).origin));await writeFile(reportPath('browser.json'),JSON.stringify({at:new Date().toISOString(),browser:await browser.version(),checks,errors,requests,observations,scope:'Chromium software WebGL; 30 source correspondences are not field-survey control points; global registered terrain remains blocked'},null,2));console.log(JSON.stringify({checks:checks.length,errors}));
}catch(e){if(page){await page.screenshot({path:reportPath('browser-failure.png')});await writeFile(reportPath('browser-failure.json'),JSON.stringify({error:String(e),errors,requests,checks,observations,main:await page.evaluate(()=>window.__NYC__?.snapshot()),terrain:await page.evaluate(()=>window.__NYC_TERRAIN__?.snapshot())},null,2));}console.error(e);throw e;}finally{await browser?.close();server.kill();}
