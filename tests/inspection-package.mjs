import {chromium} from 'playwright-core';
import {spawn,execFileSync} from 'node:child_process';
import {readFile,writeFile,mkdir,mkdtemp,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {setTimeout as delay} from 'node:timers/promises';
import assert from 'node:assert/strict';
const report='reports/stage8',temp=await mkdtemp(join(process.cwd(),'data/intermediate/stage7/package-'));
const spec=JSON.parse(await readFile(report+'/package.json','utf8'));
const zip=join(process.cwd(),spec.path),baseCity=join(process.cwd(),'dist/datasets/buildings-city');
const setup=JSON.parse(execFileSync('.venv/bin/python',['-c',`import zipfile,pathlib,os,json,hashlib,sys
z=zipfile.ZipFile(sys.argv[1]);root=pathlib.Path(sys.argv[2]);base=pathlib.Path(sys.argv[3]);manifest=json.loads(z.read('OVERLAY_MANIFEST.json'))
assert hashlib.sha256((base/'manifest.json').read_bytes()).hexdigest()==manifest['required_base']['manifest_sha256']
for f in z.infolist():
 assert not pathlib.PurePosixPath(f.filename).is_absolute() and '..'not in pathlib.PurePosixPath(f.filename).parts
z.extractall(root)
for f in manifest['files']:assert hashlib.sha256((root/f['path']).read_bytes()).hexdigest()==f['sha256']
target=root/'app/datasets/buildings-city';count=0
for p in base.rglob('*'):
 if p.is_file():
  q=target/p.relative_to(base);q.parent.mkdir(parents=True,exist_ok=True);os.link(p,q);count+=1
print(json.dumps({'extracted_payload_sha_verified':True,'unchanged_base_files_hardlinked':count,'assembly_note':'overlay plus explicitly required existing stage4 city; not a self-contained full-city ZIP'}))`,zip,temp,baseCity],{encoding:'utf8'}));
let server,browser,page;const checks=[],errors=[],requests=[];
const origin='http://127.0.0.1:4192';
try{
 server=spawn('python3',['-m','http.server','4192','--bind','127.0.0.1'],{cwd:join(temp,'app'),stdio:'ignore'});
 for(let i=0;i<100;i++){try{if((await fetch(origin+'/inspection.html')).ok)break;}catch{}await delay(100);}
 browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const context=await browser.newContext({viewport:{width:1440,height:1000}});
 await context.route('**/*',r=>new URL(r.request().url()).origin===origin?r.continue():r.abort());
 page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('request',r=>requests.push(r.url()));
 await page.goto(origin+'/inspection.html?diagnostics=1');
 await page.waitForFunction(()=>{const s=window.__NYC_INSPECTION__?.snapshot();return s&&!s.flying&&s.layerStates.some(l=>l.key==='roads'&&l.loaded>0)&&s.layerStates.some(l=>l.key.startsWith('city:')&&l.loaded>0);},null,{timeout:120000});
 checks.push('actual extracted overlay loads local environment and required unchanged city GLBs without external access');
 await page.locator('#query').fill('id:233256');await page.locator('#search-form button').click();await page.locator('#results [data-id]').first().click();
 await page.waitForFunction(()=>document.getElementById('details').textContent.includes('规范楼高'));assert.match(await page.locator('#details').innerText(),/233256/);
 checks.push('static offline source-ID query and evidence panel use packaged shards');
 await page.locator('#mode').selectOption('walk');await page.locator('#walk-area').selectOption('central-park');
 const child=page.frameLocator('#local-view');
 await page.waitForFunction(()=>{const s=document.getElementById('local-view').contentWindow?.__NYC_TERRAIN__?.snapshot();return s?.id==='central-park'&&s.walk.ready;},null,{timeout:120000});
 const ground=()=>child.locator('body').evaluate(()=>window.__NYC_TERRAIN__.snapshot());const saved=(await ground()).walk.position;
 await page.getByText('相机书签',{exact:true}).click();await page.locator('#bookmark-name').fill('packaged ground');await page.locator('#save-bookmark').click();await page.waitForFunction(()=>window.__NYC_INSPECTION__.snapshot().bookmarks.length===1);
 await child.locator('#terrain-canvas').focus();await page.keyboard.down('w');await delay(450);await page.keyboard.up('w');
 await page.locator('[data-bookmark="0"]').click();
 await page.waitForFunction(saved=>{const s=document.getElementById('local-view').contentWindow?.__NYC_TERRAIN__?.snapshot();return s?.walk.ready&&Math.hypot(...s.walk.position.map((v,i)=>v-saved[i]))<.01;},saved,{timeout:120000});
 checks.push('actual packaged park DEM and collision load; ground bookmark restores through validated ready handshake');
 await page.getByText('读取与量测',{exact:true}).click();await page.locator('#measure-tool').click();
 const box=await child.locator('#terrain-canvas').boundingBox();
 await page.mouse.click(box.x+box.width*.4,box.y+box.height*.85);await page.mouse.click(box.x+box.width*.6,box.y+box.height*.85);
 assert.match(await page.locator('#measurement').innerText(),/局部水平≈.*空间≈.*高差≈/);
 checks.push('actual two terrain picks report same-datum local horizontal,space andheight difference');
 await page.screenshot({path:report+'/package-ground.png'});
 assert.deepEqual(errors,[]);assert.ok(requests.every(u=>new URL(u).origin===origin));
 await writeFile(report+'/package-browser.json',JSON.stringify({at_utc:new Date().toISOString(),zip_sha256:spec.sha256,setup,checks,errors,requests,external_requests:0,real_mobile_hardware:false},null,2)+'\n');
 console.log(JSON.stringify({checks:checks.length,errors,setup}));
}catch(e){if(page)await page.screenshot({path:report+'/package-failure.png'});throw e;}finally{await browser?.close();server?.kill();await rm(temp,{recursive:true,force:true});}
