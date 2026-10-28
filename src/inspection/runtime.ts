/** Bounded root loading and pinned-engine budget policy. No geometry modification. */
export class LoadQueue {
 private tasks:{run:()=>Promise<void>;signal:AbortSignal;priority:number;resolve:()=>void;reject:(e:unknown)=>void}[]=[];
 active=0;completed=0;cancelled=0;
 readonly limit:number;constructor(limit=2){this.limit=limit;}
 add(run:()=>Promise<void>,signal:AbortSignal,priority=0){
  return new Promise<void>((resolve,reject)=>{this.tasks.push({run,signal,priority,resolve,reject});this.tasks.sort((a,b)=>a.priority-b.priority);this.pump();});
 }
 get pending(){return this.tasks.length;}
 cancelPending(){for(const t of this.tasks){this.cancelled++;t.resolve();}this.tasks=[];}
 private pump(){while(this.active<this.limit&&this.tasks.length){const t=this.tasks.shift()!;if(t.signal.aborted){this.cancelled++;t.resolve();continue;}this.active++;void t.run().then(t.resolve,t.reject).finally(()=>{this.active--;this.completed++;this.pump();});}}
}
export const PROFILES={
 high:{name:'原始精度',resolution:1,sse:6,cacheMiB:96,overflowMiB:48},
 medium:{name:'均衡',resolution:.9,sse:12,cacheMiB:48,overflowMiB:24},
 low:{name:'移动',resolution:.65,sse:24,cacheMiB:24,overflowMiB:12}
}as const;
export type Quality=keyof typeof PROFILES;
/** Hysteresis changes raster resolution only; manual selection disables automatic changes. */
export class AdaptiveQuality {
 enabled=false;index=1;lastChange=-Infinity;slow=0;fast=0;
 sample(frameMs:number,now:number):Quality|null{
  if(!this.enabled||!Number.isFinite(frameMs)||frameMs<=0)return null;
  this.slow=frameMs>42?this.slow+1:0;this.fast=frameMs<22?this.fast+1:0;
  if(now-this.lastChange<30000)return null;
  let next=this.index;
  if(this.slow>=120)next=Math.max(0,this.index-1);
  if(this.fast>=900)next=Math.min(2,this.index+1);
  if(next===this.index)return null;this.index=next;this.lastChange=now;this.fast=this.slow=0;
  return (['low','medium','high']as Quality[])[next];
 }
}
/** Cesium1.146 JobScheduler is private; inspect shape, isolate and fail visibly on upgrade. */
export function configureJobBudget(scene:unknown){
 const s=(scene as {_jobScheduler?:{_totalBudget:number;_budgets:{_total:number}[]}})._jobScheduler;
 if(!s||s._budgets?.length!==3||typeof s._totalBudget!=='number')return {applied:false,targetMs:null,note:'engine adapter incompatible; default budget retained'};
 [2,2,4].forEach((ms,i)=>s._budgets[i]._total=ms);s._totalBudget=8;
 return {applied:true,targetMs:8,note:'soft creation budget: texture2/program2/buffer4ms; one indivisible job per type may exceed it'};
}
/** Pinned1.146 XHR adapter. Fetch roots/Worker have their own AbortController deadlines. */
export function configureResourceTimeout(resourceClass:unknown){
 const api=resourceClass as {_Implementations?:{loadWithXhr:(...args:any[])=>XMLHttpRequest|undefined}};
 const impl=api._Implementations;if(!impl||typeof impl.loadWithXhr!=='function')return {applied:false,timeoutMs:null,restore:()=>{}};
 const original=impl.loadWithXhr;
 impl.loadWithXhr=function(...args:any[]){const xhr=original.apply(this,args);if(xhr&&'timeout'in xhr){xhr.timeout=15000;xhr.ontimeout=()=>args[5]?.reject(new Error('城市资源请求超时：'+args[0]));}return xhr;};
 return {applied:true,timeoutMs:15000,restore:()=>{impl.loadWithXhr=original;}};
}
