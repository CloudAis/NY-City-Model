import {chromium} from 'playwright-core';
import {spawn} from 'node:child_process';
import {readFile,writeFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
import {setTimeout as delay} from 'node:timers/promises';
import assert from 'node:assert/strict';
const report='reports/stage10',origin='http://127.0.0.1:4201';const server=spawn('python3',['-m','http.server','4201','--bind','127.0.0.1'],{cwd:process.cwd(),stdio:'ignore'});
let browser;const checks=[],errors=[],requests=[];let fileMode,blockedReason=null;
try{
 browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const context=await browser.newContext({viewport:{width:1440,height:1000}});await context.route('**/*',r=>{const u=new URL(r.request().url());return u.origin===origin||['file:','data:','about:'].includes(u.protocol)?r.continue():r.abort();});
 let page=await context.newPage();const listen=p=>{p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>requests.push(r.url()));};listen(page);
 try{await page.goto(pathToFileURL(resolve('preview-single.html')).href);await page.waitForFunction(()=>window.__FINAL_PREVIEW__?.snapshot().ready,null,{timeout:20000});fileMode='file_navigation_succeeded';}
 catch(e){if(!String(e).includes('ERR_BLOCKED_BY_ADMINISTRATOR'))throw e;fileMode='blocked_by_enterprise_policy';blockedReason=String(e);}
 if(fileMode==='blocked_by_enterprise_policy'){
  await page.close();page=await context.newPage();listen(page);await page.setContent(await readFile('preview-single.html','utf8'));await page.waitForFunction(()=>window.__FINAL_PREVIEW__?.snapshot().ready,null,{timeout:20000});
 }
 let s=await page.evaluate(()=>window.__FINAL_PREVIEW__.snapshot());assert.equal(s.complete_fine_buildings,0);assert.equal(s.model_count,2);assert.equal(s.texture_count,4);assert.equal(s.error,'');await page.waitForFunction(()=>window.__FINAL_PREVIEW__.snapshot().draws>0);
 checks.push('actual file navigation attempted; standalone content runs with allGLB and four original textures inline, explicit partial scope');
 await page.screenshot({path:report+'/preview-grove.png'});
 const photoPixels=()=>page.locator('canvas').evaluate(c=>{const gl=c.getContext('webgl2'),p=new Uint8Array(c.width*c.height*4);gl.readPixels(0,0,c.width,c.height,gl.RGBA,gl.UNSIGNED_BYTE,p);let n=0;for(let i=0;i<p.length;i+=16)if(p[i]>25&&p[i]<225&&p[i]===p[i+1]&&p[i+1]===p[i+2])n++;return n;});
 assert.ok(await photoPixels()>1000,'known front displays the original grayscale photo');const rb=await page.locator('canvas').boundingBox();await page.mouse.move(rb.x+50,rb.y+rb.height*.5);await page.mouse.down();await page.mouse.move(rb.x+50+Math.PI/.006,rb.y+rb.height*.5,{steps:12});await page.mouse.up();await delay(100);assert.equal(await photoPixels(),0,'unknown rear stays neutral and never mirrors the front photo');await page.screenshot({path:report+'/preview-unknown-rear.png'});await page.locator('#reset').click();checks.push('actual front photo pixels visible,180degree orbit renders unknown rear neutral rather than mirrored photo');
 const box=await page.locator('canvas').boundingBox();const before=s.camera;await page.mouse.move(box.x+box.width*.5,box.y+box.height*.5);await page.mouse.down();await page.mouse.move(box.x+box.width*.6,box.y+box.height*.56,{steps:8});await page.mouse.up();await page.mouse.wheel(0,120);s=await page.evaluate(()=>window.__FINAL_PREVIEW__.snapshot());assert.notDeepEqual(s.camera,before);
 await page.locator('#sample').selectOption('1');await page.waitForFunction(()=>window.__FINAL_PREVIEW__.snapshot().sample==='one-wtc-partial');await page.screenshot({path:report+'/preview-wtc.png'});await page.locator('#north').click();
 for(let i=0;i<20;i++)await page.locator('#sample').selectOption(String(i%2));s=await page.evaluate(()=>window.__FINAL_PREVIEW__.snapshot());assert.equal(s.model_count,2);assert.equal(s.texture_count,4);assert.equal(s.error,'');checks.push('actual orbit,zoom,top view and20 switches retain bounded model/texture ownership');
 await page.setViewportSize({width:390,height:844});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:report+'/preview-mobile.png'});checks.push('narrow viewport remains usable without page overflow; no real mobile hardware claim');
 for(let i=0;i<100;i++){try{if((await fetch(origin+'/preview-single.html')).ok)break;}catch{}await delay(100);}
 const http=await context.newPage();http.on('pageerror',e=>errors.push(e.message));http.on('request',r=>requests.push(r.url()));await http.goto(origin+'/preview-single.html');await http.waitForFunction(()=>window.__FINAL_PREVIEW__?.snapshot().ready,null,{timeout:20000});assert.equal(await http.locator('#loading').isHidden(),true);checks.push('same physical single file works over localHTTP with outside network blocked');
 const unsupported=await browser.newContext();await unsupported.addInitScript(()=>{HTMLCanvasElement.prototype.getContext=()=>null;});const u=await unsupported.newPage();await u.setContent(await readFile('preview-single.html','utf8'));assert.equal(await u.locator('#error').isVisible(),true);assert.equal(await u.locator('#loading').isHidden(),true);checks.push('unsupportedWebGL2 produces explicit finite error instead of an endless loading page');await unsupported.close();
 assert.deepEqual(errors,[]);assert.ok(requests.every(s=>{const u=new URL(s);return u.origin===origin||['file:','data:','about:'].includes(u.protocol);}));await writeFile(report+'/single-preview.json',JSON.stringify({at_utc:new Date().toISOString(),browser:await browser.version(),checks,errors,requests,fileMode,blockedReason,embedded_mode:'actual offline setContent' ,http_mode:'actual localhostHTTP with outside routes blocked',real_mobile_hardware:false,complete_fine_buildings:0},null,2)+'\n');console.log('PREVIEW_COMPLETE',checks.length,'checks',fileMode);
}finally{await browser?.close();server.kill();}
