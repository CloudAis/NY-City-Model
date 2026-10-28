import type {BuildingRecord} from './search';
import {idBucket} from './core';
const cache=new Map<string,{value:unknown;bytes:number}>(),inflight=new Map<string,{users:Set<number>;controller:AbortController;promise:Promise<unknown>}>(),jobs=new Map<number,AbortController>();
let activeFetch=0;const permits:(()=>void)[]=[];
async function acquire(signal:AbortSignal){if(activeFetch<4)activeFetch++;else await new Promise<void>(resolve=>permits.push(resolve));if(signal.aborted){release();throw new DOMException('已取消','AbortError');}}
function release(){const next=permits.shift();if(next)next();else activeFetch--;}
let base='',bytes=0,hits=0,fetches=0;const failed=new Map<string,number>();
async function json<T>(path:string,id:number):Promise<T>{
 if(jobs.get(id)?.signal.aborted)throw new DOMException('已取消','AbortError');
 const cached=cache.get(path);if(cached){hits++;cache.delete(path);cache.set(path,cached);return cached.value as T;}
 if((failed.get(path)??0)>Date.now())throw Error('索引请求冷却中：'+path);
 let task=inflight.get(path);
 if(!task){
  const controller=new AbortController(),users=new Set<number>();
  const promise=(async()=>{
   let last:unknown;
   for(let attempt=0;attempt<2;attempt++){
    await acquire(controller.signal);const timer=setTimeout(()=>controller.abort('索引超时'),8000);
    try{
     fetches++;const r=await fetch(new URL(path,base),{signal:controller.signal});if(!r.ok)throw Error('索引HTTP'+r.status);
     const text=await r.text(),value=JSON.parse(text);if(!Array.isArray(value)&&path!=='manifest.json')throw Error('索引格式无效');
     const size=text.length*2;cache.set(path,{value,bytes:size});bytes+=size;
     while(cache.size>14||bytes>8*1024*1024){const key=cache.keys().next().value!;bytes-=cache.get(key)!.bytes;cache.delete(key);}return value;
    }catch(e){last=e;if(controller.signal.aborted||String(e).includes('404'))break;await new Promise(r=>setTimeout(r,500));}finally{clearTimeout(timer);release();}
   }
   if(!controller.signal.aborted){failed.set(path,Date.now()+30000);if(failed.size>128)failed.delete(failed.keys().next().value!);}throw last;
  })();task={users,controller,promise};inflight.set(path,task);void promise.finally(()=>inflight.delete(path)).catch(()=>{});
 }
 task.users.add(id);return await task.promise as T;
}
async function byId(id:string,job:number){const rows=await json<BuildingRecord[]>('ids/'+idBucket(id)+'.json',job);return rows.find(r=>r.id===id)??null;}
async function search(query:string,borough:string,job:number){
 const q=query.normalize('NFKC').trim().toLowerCase();if(!q)return [];
 if(q.startsWith('nyc:')||q.startsWith('id:')){const id=q.startsWith('id:')?'nyc:footprints:doitt:'+q.slice(3).trim():q;if(!/^nyc:footprints:(doitt|objectid):\d+$/.test(id))return [];const r=await byId(id,job);return r&&(!borough||r.borough===borough)?[r]:[];}
 if(/^\d{4,}$/.test(q)){
  const index=await json<{bin_buckets:string[]}>('manifest.json',job),bins=index.bin_buckets.includes(q.slice(0,4))?await json<string[][]>('bins/'+q.slice(0,4)+'.json',job):[];
  const matches=bins.filter(r=>r[0].startsWith(q)&&(!borough||r[2]===borough)).slice(0,60),records=await Promise.all(matches.map(r=>byId(r[1],job)));
  if(records.some(Boolean))return records.filter((r):r is BuildingRecord=>!!r);
  const r=await byId('nyc:footprints:doitt:'+q,job);return r&&(!borough||r.borough===borough)?[r]:[];
 }
 const boroughs=borough?[borough]:['manhattan','brooklyn','queens','bronx','staten-island'];
 const rows=(await Promise.all(boroughs.map(b=>json<BuildingRecord[]>('names/'+b+'.json',job)))).flat();
 return rows.filter(r=>[r.name,r.address,...r.aliases].some(v=>v?.normalize('NFKC').toLowerCase().includes(q))).slice(0,100);
}
self.onmessage=async(e:MessageEvent)=>{
 if(e.data.cancel){jobs.get(e.data.cancel)?.abort();for(const t of inflight.values()){t.users.delete(e.data.cancel);if(!t.users.size)t.controller.abort();}return;}
 const {id,method,args}=e.data;base=e.data.base;const c=new AbortController();jobs.set(id,c);
 try{const result=method==='id'?await byId(args[0],id):await search(args[0],args[1],id);if(!c.signal.aborted)self.postMessage({id,result,metrics:{entries:cache.size,estimatedBytes:bytes,hits,fetches,activeFetch,queuedFetch:permits.length}});}
 catch(error){if(!c.signal.aborted)self.postMessage({id,error:String(error)});}
 finally{jobs.delete(id);for(const t of inflight.values()){t.users.delete(id);if(!t.users.size)t.controller.abort();}}
};
