// Extract the actual release and run its own resources, with external requests blocked.
import {chromium} from 'playwright-core';
import {spawn,execFileSync} from 'node:child_process';
import {readFile,writeFile,mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import assert from 'node:assert/strict';
import {setTimeout as delay} from 'node:timers/promises';
const dir=await mkdtemp(join(tmpdir(),'nyc-stage5-'));
const release=JSON.parse(await readFile('reports/stage5/release.json','utf8'));
execFileSync('python3',['-c','import zipfile,sys;zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])',release.path,dir]);
const port=4186,base=`http://127.0.0.1:${port}`;
const server=spawn('python3',['-m','http.server',String(port),'--bind','127.0.0.1','--directory',join(dir,'app')],{stdio:'ignore'});
let browser;const errors=[],requests=[],checks=[];
try {
 for(let i=0;i<50;i++){try{if((await fetch(base)).ok)break;}catch{}await delay(100);}
 browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const context=await browser.newContext({viewport:{width:1440,height:1000}});
 await context.route('**/*',r=>new URL(r.request().url()).origin===base?r.continue():r.abort());
 const page=await context.newPage();
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('request',r=>requests.push(r.url()));
 page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await page.goto(base+'/index.html?diagnostics=1');
 await page.waitForFunction(()=>window.__NYC_LANDMARKS__?.snapshot().modelLoads>0,null,{timeout:120000});
 assert.equal(await page.locator('#directories').innerText(),'29');
 assert.equal(await page.locator('#completed').innerText(),'0');
 checks.push('extracted archive index renders the actual partial One WTC GLB with honest scope');
 await page.locator('#context-visible').check();
 await page.waitForFunction(()=>window.__NYC_LANDMARKS__.snapshot().contextStats.targetHidden===1,null,{timeout:120000});
 let s=await page.evaluate(()=>window.__NYC_LANDMARKS__.snapshot());
 assert.equal(s.contextStats.neighboursVisible,19);assert.equal(s.contextStats.neighboursHidden,0);
 await page.locator('#model-visible').uncheck();
 await page.waitForFunction(()=>window.__NYC_LANDMARKS__.snapshot().contextStats.targetVisible===1);
 checks.push('archive contains the exact original neighbourhood and safely restores only the target');
 await page.locator('#landmark').selectOption('432-park-avenue');
 await page.waitForFunction(()=>{const s=window.__NYC_LANDMARKS__.snapshot();return s.active==='432-park-avenue'&&s.modelLoads>0;},null,{timeout:120000});
 assert.equal(await page.locator('#context-visible').isDisabled(),true);
 s=await page.evaluate(()=>window.__NYC_LANDMARKS__.snapshot());
 assert.equal(s.completeCount,0);assert.equal(s.worldBaseRegistered,false);
 checks.push('archive renders432 grid fragment and refuses unsafe whole-project suppression');
 await page.screenshot({path:'reports/stage5/standalone.png'});
 assert.deepEqual(errors,[]);assert.ok(requests.every(u=>new URL(u).origin===base));
 await writeFile('reports/stage5/standalone-browser.json',JSON.stringify({at_utc:new Date().toISOString(),browser:await browser.version(),archive:release.path,archive_sha256:release.sha256,checks,errors,requests,external_requests:0,scope:'extracted small package over local HTTP; file:// and full-city runtime not tested here'},null,2)+'\n');
 console.log(JSON.stringify({checks:checks.length,errors,external_requests:0}));
} finally {
 await browser?.close();server.kill();await rm(dir,{recursive:true,force:true});
}
