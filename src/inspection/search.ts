import {idBucket} from './core';
export interface BuildingRecord {
 id:string;bin:string|null;bbl:string|null;borough:string;name:string|null;address:string|null;aliases:string[];
 bbox:number[];source_version:string;raw_record:{path:string;sha256:string};relative_height_raw_ft:number|null;
 canonical_height_m:null;ground_ellipsoid_m:null;roof_status:string;facade_status:string;observation_date:string|null;
 last_edited_at:string|null;state:string;
}
const cache=new Map<string,unknown>();
async function json<T>(path:string,signal?:AbortSignal):Promise<T>{
 if(cache.has(path))return cache.get(path) as T;
 const r=await fetch(new URL('datasets/inspection/search/'+path,document.baseURI),{signal});
 if(r.status===404)return []as T;if(!r.ok)throw new Error('查询索引HTTP '+r.status);
 const value=await r.json();cache.set(path,value);if(cache.size>14)cache.delete(cache.keys().next().value!);return value;
}
export async function byId(id:string,signal?:AbortSignal):Promise<BuildingRecord|null>{
 const rows=await json<BuildingRecord[]>('ids/'+idBucket(id)+'.json',signal);
 return rows.find(r=>r.id===id)??null;
}
export async function search(query:string,borough:string,signal?:AbortSignal):Promise<BuildingRecord[]>{
 const q=query.normalize('NFKC').trim().toLowerCase();if(!q)return [];
 if(q.startsWith('nyc:')||q.startsWith('id:')){
  const id=q.startsWith('id:')?'nyc:footprints:doitt:'+q.slice(3).trim():q;
  if(!/^nyc:footprints:(doitt|objectid):\d+$/.test(id))return [];
  const r=await byId(id,signal);return r&&(!borough||r.borough===borough)?[r]:[];
 }
 if(/^\d{4,}$/.test(q)){
  const index=await json<{bin_buckets:string[]}>('manifest.json',signal);
  const bins=index.bin_buckets.includes(q.slice(0,4))?await json<string[][]>('bins/'+q.slice(0,4)+'.json',signal):[];
  const matches=bins.filter(r=>r[0].startsWith(q)&&(!borough||r[2]===borough)).slice(0,60);
  const result=await Promise.all(matches.map(r=>byId(r[1],signal)));
  if(result.some(Boolean))return result.filter((r):r is BuildingRecord=>!!r);
  const r=await byId('nyc:footprints:doitt:'+q,signal);return r&&(!borough||r.borough===borough)?[r]:[];
 }
 const boroughs=borough?[borough]:['manhattan','brooklyn','queens','bronx','staten-island'];
 const rows=(await Promise.all(boroughs.map(b=>json<BuildingRecord[]>('names/'+b+'.json',signal)))).flat();
 return rows.filter(r=>[r.name,r.address,...r.aliases].some(v=>v?.normalize('NFKC').toLowerCase().includes(q))).slice(0,100);
}
