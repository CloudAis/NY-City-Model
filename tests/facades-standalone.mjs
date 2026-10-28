import {chromium} from 'playwright-core';
import {spawn,execFileSync} from 'node:child_process';
import {readFile,writeFile,mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import assert from 'node:assert/strict';
import {setTimeout as delay} from 'node:timers/promises';
const release=JSON.parse(await readFile('reports/stage6/release.json','utf8'));
const directory=await mkdtemp(join(tmpdir(),'nyc-facade-release-'));
execFileSync('python3',['-c','import zipfile,sys;zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])',release.path,directory]);
const port=4188,base=`http://127.0.0.1:${port}`;
const server=spawn('python3',['-m','http.server',String(port),'--bind','127.0.0.1','--directory',join(directory,'app')],{stdio:'ignore'});
let browser;const requests=[],errors=[],checks=[];
try{
 for(let i=0;i<60;i++){try{if((await fetch(base)).ok)break;}catch{}await delay(100);}
 browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const context=await browser.newContext({viewport:{width:1440,height:1000}});
 await context.route('**/*',r=>new URL(r.request().url()).origin===base?r.continue():r.abort());
 const page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));page.on('request',r=>requests.push(r.url()));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await page.goto(base+'/index.html?diagnostics=1');await page.waitForFunction(()=>window.__NYC_FACADES__?.snapshot().outlineLoads>0,null,{timeout:120000});
 assert.equal(await page.locator('#area option').count(),12);assert.equal(await page.locator('#source-count').innerText(),'918');assert.equal(await page.locator('#history').isChecked(),false);
 checks.push('extracted package opens default evidence mode with12 actual source AOIs');
 await page.locator('#history').check();await page.waitForFunction(()=>{const s=window.__NYC_FACADES__.snapshot();return s.historyLoads>0&&!s.cameraFlying;},null,{timeout:120000});
 assert.equal(new Set(requests.filter(u=>/front-(4|6|8|10)\.png/.test(u))).size,4);
 await page.screenshot({path:'reports/stage6/standalone.png'});
 await page.locator('#history').uncheck();await page.locator('#area').selectOption('queens-jackson-heights');await page.waitForFunction(()=>{const s=window.__NYC_FACADES__.snapshot();return s.area==='queens-jackson-heights'&&s.outlineLoads>0;},null,{timeout:120000});
 assert.equal((await page.evaluate(()=>window.__NYC_FACADES__.snapshot())).historyLoaded,false);
 checks.push('archive contains four different historical textures and removes them before another real AOI');
 await page.goto(base+'/landmarks.html?diagnostics=1');await page.waitForFunction(()=>window.__NYC_LANDMARKS__?.snapshot().modelLoads>0,null,{timeout:120000});
 assert.equal(await page.locator('#completed').innerText(),'0');
 checks.push('existing landmark entry remains operable with its incomplete status retained');
 assert.deepEqual(errors,[]);assert.ok(requests.every(u=>new URL(u).origin===base));
 await writeFile('reports/stage6/standalone-browser.json',JSON.stringify({at_utc:new Date().toISOString(),browser:await browser.version(),archive:release.path,archive_sha256:release.sha256,checks,errors,requests,external_requests:0,scope:'actual extracted package over local HTTP, no full street or file:// acceptance'},null,2)+'\n');
 console.log(JSON.stringify({checks:checks.length,errors,external_requests:0}));
}finally{await browser?.close();server.kill();await rm(directory,{recursive:true,force:true});}
