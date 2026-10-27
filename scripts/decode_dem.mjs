// Official Esri LERC 2.0.0 decoder already pinned through Cesium's package lock.
import Lerc from 'lerc';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {dirname} from 'node:path';
const manifest=JSON.parse(await readFile('data/manifests/stage3/dem-samples.json','utf8'));
for(const spec of manifest){
 if(!spec.masked_raster)throw new Error('Explicit LERC mask source is required');
 const b=await readFile(spec.masked_raster),d=Lerc.decode(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength));
 if(d.pixels.length!==1||d.dimCount!==1||d.width!==257||d.height!==257)throw new Error('Unexpected DEM dimensionality');
 const values=new Float32Array(d.pixels[0]),mask=d.mask??new Uint8Array(d.width*d.height).fill(1);
 if(values.length!==mask.length)throw new Error('Mask and height shapes differ');
 const prefix=`data/intermediate/stage3/dem/${spec.id}`;await mkdir(dirname(prefix),{recursive:true});
 // DataView explicitly writes little-endian; the mask is authoritative, never a zero-value test.
 const binary=Buffer.alloc(values.length*4);for(let i=0;i<values.length;i++)binary.writeFloatLE(values[i],i*4);
 await writeFile(prefix+'.f32',binary);await writeFile(prefix+'.mask',Buffer.from(mask));
 const info={source:spec.masked_raster,width:d.width,height:d.height,pixelType:d.pixelType,statistics:d.statistics,maskProvided:d.mask!==null,validPixels:mask.reduce((n,v)=>n+(v?1:0),0),missingPixels:mask.reduce((n,v)=>n+(v?0:1),0),validRealZeroPixels:values.reduce((n,v,i)=>n+(mask[i]&&v===0?1:0),0),decoder:'Esri lerc@2.0.0 (installed and pinned through Cesium)',valuesFile:prefix+'.f32',maskFile:prefix+'.mask',byteOrder:'little-endian',exportMetadata:spec.lerc_export_metadata};
 await writeFile(prefix+'-lerc.json',JSON.stringify(info,null,2));console.log('DECODED',spec.id,'valid',info.validPixels,'missing',info.missingPixels,'real zero',info.validRealZeroPixels);
}
