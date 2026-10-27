import {defineConfig} from 'vite';
import {cpSync,existsSync,createReadStream,statSync,mkdirSync,readdirSync,linkSync,unlinkSync} from 'node:fs';
import {resolve,extname} from 'node:path';
const cesium='node_modules/cesium/Build/Cesium';
// Multi-GiB city data is published atomically. Ordinary hard links keep the
// standalone build without allocating a second city copy on this volume.
// ZIP/export copies bytes; EXDEV/unsupported filesystems fall back to copying.
function copyLocalAssets(from:string,to:string){
 mkdirSync(to,{recursive:true});
 for(const item of readdirSync(from,{withFileTypes:true})){
  if(item.name.endsWith('.tmp')||item.name.endsWith('.receipt.json'))continue;
  const src=resolve(from,item.name),dst=resolve(to,item.name);
  if(item.isDirectory())copyLocalAssets(src,dst);
  else if(item.isFile()){if(existsSync(dst))unlinkSync(dst);try{linkSync(src,dst);}catch{cpSync(src,dst);}}
 }
}

export default defineConfig({base:'./',build:{target:'es2022',rolldownOptions:{input:{main:resolve('index.html'),terrain:resolve('terrain.html'),buildings:resolve('buildings.html')}}},plugins:[{name:'local-static-assets',configureServer(server){server.middlewares.use((req,res,next)=>{const uri=(req.url??'').split('?')[0];let root='',relative='';if(uri.startsWith('/datasets/')){root=resolve('assets');relative=uri.slice(10);}else if(uri.startsWith('/cesium/')){root=resolve(cesium);relative=uri.slice(8);}else return next();const path=resolve(root,decodeURIComponent(relative));if(!path.startsWith(root+'/')){res.statusCode=403;return res.end();}if(!existsSync(path)||!statSync(path).isFile())return next();res.setHeader('Content-Type',({'.json':'application/json','.js':'text/javascript','.css':'text/css','.wasm':'application/wasm','.glb':'model/gltf-binary','.png':'image/png','.svg':'image/svg+xml'}as Record<string,string>)[extname(path)]??'application/octet-stream');res.setHeader('Content-Length',statSync(path).size);createReadStream(path).pipe(res);});},closeBundle(){mkdirSync('dist/licenses',{recursive:true});for(const [from,to]of [['cesium/LICENSE.md','cesium.md'],['cesium/ThirdParty.json','cesium-third-party.json'],['@cesium/engine/LICENSE.md','cesium-engine.md'],['@cesium/widgets/LICENSE.md','cesium-widgets.md']])if(existsSync('node_modules/'+from))cpSync('node_modules/'+from,'dist/licenses/'+to);cpSync('THIRD_PARTY_NOTICES.md','dist/licenses/PROJECT_NOTICES.md');copyLocalAssets('assets','dist/datasets');for(const name of ['Workers','Assets','Widgets','ThirdParty'])if(existsSync(`${cesium}/${name}`))cpSync(`${cesium}/${name}`,`dist/cesium/${name}`,{recursive:true});}}]});
