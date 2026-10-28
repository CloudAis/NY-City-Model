export interface BuildingRecord {
 id:string;bin:string|null;bbl:string|null;borough:string;name:string|null;address:string|null;aliases:string[];
 bbox:number[];source_version:string;raw_record:{path:string;sha256:string};relative_height_raw_ft:number|null;
 canonical_height_m:null;ground_ellipsoid_m:null;roof_status:string;facade_status:string;observation_date:string|null;
 last_edited_at:string|null;state:string;
}
let worker:Worker|undefined,next=0;const pending=new Map<number,{resolve:(v:any)=>void;reject:(e:Error)=>void;cleanup:()=>void}>();
export const searchMetrics={requested:0,completed:0,cancelled:0,errors:0,pending:0,workerCache:null as unknown};
function ensureWorker(){
 if(worker)return worker;
 worker=new Worker(new URL('./search.worker.ts',import.meta.url),{type:'module'});
 worker.onmessage=e=>{const {id,result,error,metrics}=e.data;searchMetrics.workerCache=metrics;const p=pending.get(id);if(!p)return;pending.delete(id);p.cleanup();searchMetrics.pending=pending.size;
  if(error){searchMetrics.errors++;p.reject(new Error(error));}else{searchMetrics.completed++;p.resolve(result);}
 };
 worker.onerror=e=>{for(const p of pending.values()){p.cleanup();p.reject(new Error('索引Worker失效：'+e.message));}pending.clear();searchMetrics.pending=0;worker?.terminate();worker=undefined;};return worker;
}
function query<T>(method:string,args:string[],signal?:AbortSignal):Promise<T>{
 if(signal?.aborted)return Promise.reject(new DOMException('已取消','AbortError'));
 const w=ensureWorker(),id=++next;searchMetrics.requested++;
 return new Promise((resolve,reject)=>{
  const abort=()=>{w.postMessage({cancel:id});pending.delete(id);searchMetrics.cancelled++;searchMetrics.pending=pending.size;cleanup();reject(new DOMException('已取消','AbortError'));};
  const timer=setTimeout(abort,22000),cleanup=()=>{clearTimeout(timer);signal?.removeEventListener('abort',abort);};
  pending.set(id,{resolve,reject,cleanup});searchMetrics.pending=pending.size;signal?.addEventListener('abort',abort,{once:true});w.postMessage({id,method,args,base:new URL('datasets/inspection/search/',document.baseURI).href});
 });
}
export const byId=(id:string,signal?:AbortSignal)=>query<BuildingRecord|null>('id',[id],signal);
export const search=(q:string,borough:string,signal?:AbortSignal)=>query<BuildingRecord[]>('search',[q,borough],signal);
export function disposeSearch(){for(const p of pending.values()){p.cleanup();p.reject(new DOMException('页面已关闭','AbortError'));}pending.clear();worker?.terminate();worker=undefined;searchMetrics.pending=0;}
