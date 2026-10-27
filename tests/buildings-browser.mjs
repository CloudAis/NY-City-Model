import {chromium} from 'playwright-core';
import {spawn} from 'node:child_process';
import {mkdir,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {setTimeout as delay} from 'node:timers/promises';
const port=4184,base=`http://127.0.0.1:${port}/`,checks=[],errors=[],requests=[],observations=[];
const pilot=process.argv.includes('--pilot');let browser,page;
const server=spawn(process.execPath,['node_modules/vite/bin/vite.js','preview','--host','127.0.0.1','--port',String(port),'--strictPort'],{stdio:'ignore'});
async function check(name,fn){await fn();checks.push(name);console.log('PASS',name);}
async function ready(collection,borough,mode){await page.waitForFunction(({collection,borough,mode})=>{const s=window.__NYC_BUILDINGS__?.snapshot();return s&&s.collection===collection&&(!borough||s.borough===borough)&&s.mode===mode&&s.loadedContent>0&&s.pending===0&&s.cameraHeight<6000&&s.pickPoints.length>0;},{collection,borough,mode},{timeout:120000});await delay(700);}
const snapshot=()=>page.evaluate(()=>window.__NYC_BUILDINGS__.snapshot());
try{
 await mkdir('reports/stage4',{recursive:true});for(let i=0;i<100;i++){try{if((await fetch(base)).ok)break;}catch{}await delay(150);}
 browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const context=await browser.newContext({viewport:{width:1440,height:1000}});await context.route('**/*',r=>new URL(r.request().url()).origin===new URL(base).origin?r.continue():r.abort());
 page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('request',r=>requests.push(r.url()));
 await page.goto(base+'buildings.html?diagnostics=1');await ready('pilot-lower',null,'strict');
 await check('real lower Manhattan strict outlines load with canonical heights still unknown',async()=>{const s=await snapshot();assert.equal(s.records,299);assert.equal(s.canonicalSolids,0);assert.equal(await page.locator('#hypothesis').isChecked(),false);assert.deepEqual(s.errors,[]);await page.screenshot({path:'reports/stage4/pilot-strict.png'});});
 await check('merged GLB exact feature id resolves its source metadata after an actual click',async()=>{
  const rect=await page.locator('canvas').first().boundingBox();let found=false;
  for(const p of (await snapshot()).pickPoints){if(p.x<20||p.x>rect.width-20||p.y<20||p.y>rect.height-20)continue;await page.mouse.click(rect.x+p.x,rect.y+p.y);await delay(60);const s=await snapshot();if(s.selected===p.id){found=true;observations.push({picked:p.id,detail:await page.locator('#details').innerText()});break;}}
  assert.ok(found,'at least one unambiguous exact source ID must match');assert.match(await page.locator('#details').innerText(),/可信米制高度/);
 });
 await check('explicit neutral open envelopes load only after opt-in, preserving source counts',async()=>{await page.locator('#hypothesis').check();await ready('pilot-lower',null,'hypothesis');const s=await snapshot();assert.equal(s.records,299);assert.equal(s.canonicalSolids,0);assert.match(await page.locator('#banner').innerText(),/假设包络/);await page.screenshot({path:'reports/stage4/pilot-hypothesis.png'});});
 await check('midtown uses the same pipeline and placeholder remains excluded',async()=>{await page.locator('#collection').selectOption('pilot-midtown');await ready('pilot-midtown',null,'hypothesis');const s=await snapshot();assert.equal(s.records,812);assert.equal(s.outlines,811);assert.equal(s.primitives,1);await page.screenshot({path:'reports/stage4/midtown-hypothesis.png'});});
 if(!pilot){
  await check('five borough source tiles load locally without accumulating tilesets',async()=>{
   await page.locator('#collection').selectOption('city');
   for(const [borough,count]of Object.entries({manhattan:45172,bronx:104268,brooklyn:330113,queens:460950,'staten-island':142461})){
    if((await snapshot()).borough!==borough)await page.locator('#borough').selectOption(borough);
    await ready('city',borough,'hypothesis');const s=await snapshot();assert.equal(s.records,count);assert.equal(s.primitives,1);assert.equal(s.canonicalSolids,0);assert.deepEqual(s.errors,[]);observations.push({borough,records:s.records,loadedContent:s.loadedContent});await page.screenshot({path:`reports/stage4/city-${borough}.png`});
   }
  });
  await check('city overview explicitly hides full detail and can return to a loaded source neighbourhood',async()=>{await page.evaluate(()=>window.__NYC_BUILDINGS__.overview());await page.waitForFunction(()=>window.__NYC_BUILDINGS__.snapshot().cameraHeight>30000);await delay(500);assert.equal((await snapshot()).show,false);assert.equal(await page.locator('#zoom-note').isVisible(),true);await page.locator('#fit').click();await ready('city','staten-island','hypothesis');assert.equal((await snapshot()).show,true);});
 }
 await check('bounds, strict mode return, camera gestures and narrow panel controls work',async()=>{
  await page.locator('#bounds').check();await page.locator('#hypothesis').uncheck();await ready(pilot?'pilot-midtown':'city',pilot?null:'staten-island','strict');const before=(await snapshot()).cameraHeight;await page.locator('#collapse').click();await delay(350);const rect=await page.locator('canvas').first().boundingBox();await page.mouse.move(rect.x+rect.width/2,rect.y+rect.height/2);await page.mouse.wheel(0,500);await delay(700);assert.notEqual((await snapshot()).cameraHeight,before);await page.locator('#collapse').click();await page.setViewportSize({width:390,height:844});await delay(400);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:'reports/stage4/buildings-mobile.png'});await page.locator('#collapse').click();assert.equal(await page.locator('#collapse').getAttribute('aria-expanded'),'false');await page.locator('#collapse').click();
 });
 assert.deepEqual(errors,[]);assert.ok(requests.some(u=>u.endsWith('-hypothesis.glb')));assert.ok(requests.some(u=>u.endsWith('-strict.glb')));assert.ok(requests.every(u=>new URL(u).origin===new URL(base).origin));
 await writeFile(`reports/stage4/browser${pilot?'-pilot':''}.json`,JSON.stringify({at:new Date().toISOString(),browser:await browser.version(),checks,errors,requests,observations,scope:'Chromium154 SwiftShader; source correspondence and envelope inspection only, not field reality or globally registered building bases'},null,2));console.log(JSON.stringify({checks:checks.length,errors}));
}catch(e){if(page){await page.screenshot({path:'reports/stage4/browser-failure.png'});await writeFile('reports/stage4/browser-failure.json',JSON.stringify({error:String(e),errors,checks,observations,snapshot:await page.evaluate(()=>window.__NYC_BUILDINGS__?.snapshot())},null,2));}throw e;}
finally{await browser?.close();server.kill();}
