import {chromium} from 'playwright-core';
import {spawn,execFileSync} from 'node:child_process';
import {readFile,writeFile} from 'node:fs/promises';
import {setTimeout as delay} from 'node:timers/promises';
import assert from 'node:assert/strict';
const baseline=JSON.parse(await readFile('reports/stage9/baseline.json','utf8'));
const fixtures=[['midtown','central-south'],['brooklyn','brooklyn-head'],['queens','queensboro-head']].map(([id,preset])=>({id,preset,pose:baseline.steps.find(s=>s.id===id).viewer}));
const records=[],errors=[];let browser,server;
try{
 browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 for(const [label,root,port]of [['baseline','data/intermediate/stage9/baseline',4197],['optimized','dist',4198]]){
  const origin=`http://127.0.0.1:${port}`;server=spawn('python3',['-m','http.server',String(port),'--bind','127.0.0.1'],{cwd:root,stdio:'ignore'});
  for(let i=0;i<100;i++){try{if((await fetch(origin)).ok)break;}catch{}await delay(100);}
  for(const f of fixtures){
   const context=await browser.newContext({viewport:{width:1440,height:1000},deviceScaleFactor:1});await context.route('**/*',r=>new URL(r.request().url()).origin===origin?r.continue():r.abort());const page=await context.newPage();page.on('pageerror',e=>errors.push({label,fixture:f.id,error:e.message}));
   await page.goto(origin+'/inspection.html?diagnostics=1');await page.waitForFunction(()=>window.__NYC_INSPECTION__?.snapshot().preset);
   const b={schema:1,name:'fixed visual reference',savedAt:'2026-10-28T00:00:00Z',mode:'orbit',preset:f.preset,quality:'high',layers:{...f.pose.layers},camera:{position:f.pose.cameraWorld,heading:f.pose.heading,pitch:f.pose.pitch,roll:0},selectedId:null,lighting:{mode:'neutral-fixed',datetime:null,note:'fixed evidence comparison'}};
   await page.getByText('相机书签',{exact:true}).click();await page.locator('#import-bookmarks').setInputFiles({name:'fixed-camera.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify({schema:1,bookmarks:[b]}))});await page.locator('[data-bookmark="0"]').click();
   await page.waitForFunction(p=>{const s=window.__NYC_INSPECTION__.snapshot();return !s.flying&&Math.hypot(...s.cameraWorld.map((v,i)=>v-p[i]))<.01&&s.layerStates.some(l=>l.key==='roads'&&l.loaded>0);},f.pose.cameraWorld,{timeout:120000});
   await page.waitForFunction(()=>{const s=window.__NYC_INSPECTION__.snapshot();return s.layerStates.every(l=>l.pending===0&&l.processing===0)&&(!s.runtime||s.runtime.queue.active===0);},null,{timeout:120000});await delay(1500);
   const s=await page.evaluate(()=>window.__NYC_INSPECTION__.snapshot());assert.ok(Math.hypot(...s.cameraWorld.map((v,i)=>v-f.pose.cameraWorld[i]))<.01);assert.equal(s.quality,'high');
   await page.locator('#globe canvas').screenshot({path:'reports/stage9/visual-'+label+'-'+f.id+'.png'});records.push({label,fixture:f.id,preset:f.preset,camera:s.cameraWorld,heading:s.heading,pitch:s.pitch,quality:s.quality,loadedTotal:s.loadedTotal,layerStates:s.layerStates});await context.close();
  }server.kill();await delay(200);server=undefined;
 }
 const numeric=JSON.parse(execFileSync('/usr/bin/python3',['-c',`from PIL import Image
import numpy as np,json
rows=[]
for name in ['midtown','brooklyn','queens']:
 a=np.array(Image.open('reports/stage9/visual-baseline-'+name+'.png').convert('RGB'),dtype=np.int16);b=np.array(Image.open('reports/stage9/visual-optimized-'+name+'.png').convert('RGB'),dtype=np.int16)
 assert a.shape==b.shape
 d=np.abs(a-b);rows.append({'fixture':name,'shape':list(a.shape),'mean_absolute_rgb_difference_0_255':float(d.mean()),'fraction_pixels_any_channel_difference_above20':float((d.max(axis=2)>20).mean()),'note':'same real camera,neutral light,original-precision mode; pixels are render comparison,not measured building accuracy'})
Image.fromarray(np.minimum(np.abs(np.array(Image.open('reports/stage9/visual-baseline-midtown.png').convert('RGB'),dtype=np.int16)-np.array(Image.open('reports/stage9/visual-optimized-midtown.png').convert('RGB'),dtype=np.int16))*4,255).astype('uint8')).save('reports/stage9/visual-midtown-diff4x.png')
print(json.dumps(rows))`],{encoding:'utf8'}));
 await writeFile('reports/stage9/visual.json',JSON.stringify({at_utc:new Date().toISOString(),records,numeric,errors,geometry_change_m:0,geometry_basis:'all original GLB bytes and every leaf transform/feature mapping retained; this is not a claim of real-world0m accuracy',lossy_compression:'none',fixed_camera_numeric_tolerance_m:.01},null,2)+'\n');assert.deepEqual(errors,[]);console.log('COMPLETE',numeric);
}finally{server?.kill();await browser?.close();}
