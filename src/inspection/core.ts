/** Pure time, measurement, identity and bookmark rules; no graphics-frame accounting. */
export type Layers=Record<string,boolean>;
export const MIN_WORLD_HEIGHT=800;
export const MAX_WORLD_HEIGHT=250000;
export function speedMetresPerSecond(distance:number):number {
 if(!Number.isFinite(distance))throw new Error('有限距离必需');
 return Math.min(1200,Math.max(2,Math.abs(distance)*.08));
}
export function movement(distance:number,elapsedSeconds:number,axes:number[],slow=false):number[] {
 if(!Number.isFinite(elapsedSeconds)||elapsedSeconds<0||elapsedSeconds>1)throw new Error('运动时间间隔失效，应停止输入');
 const norm=Math.hypot(...axes);if(!norm)return axes.map(()=>0);
 const step=speedMetresPerSecond(distance)*elapsedSeconds*(slow?.1:1);
 return axes.map(x=>x/norm*step);
}
export function stableId(pick:unknown):string|null {
 try{
  if(!pick||typeof pick!=='object')return null;
  const f=pick as {getProperty?:(key:string)=>unknown};
  if(typeof f.getProperty!=='function')return null;
  const id=f.getProperty('id');
  return typeof id==='string'&&/^nyc:footprints:(?:doitt|objectid):[A-Za-z0-9._-]+$/.test(id)?id:null;
 }catch{return null;}
}
export function idBucket(id:string):string{
 const suffix=id.split(':').at(-1)!;
 if(!/^\d+$/.test(suffix))throw new Error('仅支持已保存的数字来源编号');
 return suffix.slice(-3).padStart(3,'0');
}
export function localMeasurement(a:number[],b:number[]){
 if(a.length!==3||b.length!==3||![...a,...b].every(Number.isFinite))throw new Error('同基准三维坐标必需');
 return {horizontal:Math.hypot(b[0]-a[0],b[1]-a[1]),space:Math.hypot(...b.map((v,i)=>v-a[i])),difference:b[2]-a[2]};
}
export interface Bookmark {
 schema:1;name:string;savedAt:string;mode:string;preset:string;quality:string;layers:Layers;
 camera:{position:number[];heading:number;pitch:number;roll:number};
 selectedId:string|null;lighting:{mode:'neutral-fixed';datetime:null;note:string};
 localWalk?:{area:string;position:number[];yaw:number;pitch:number};
}
export function validateBookmark(value:unknown):Bookmark{
 if(!value||typeof value!=='object')throw new Error('书签必须为对象');
 const b=value as Bookmark,p=b.camera?.position;
 if(b.schema!==1||!Array.isArray(p)||p.length!==3||!p.every(Number.isFinite)||
  ![b.camera.heading,b.camera.pitch,b.camera.roll].every(Number.isFinite)||
  !['city','orbit','top','fly','walk'].includes(b.mode)||!['low','medium','high'].includes(b.quality)||
  typeof b.name!=='string'||b.name.length>100||!b.layers||Object.values(b.layers).some(v=>typeof v!=='boolean')||
  b.lighting?.mode!=='neutral-fixed'||b.lighting.datetime!==null)throw new Error('书签字段或版本无效');
 if(Math.hypot(...p)<6300000||Math.hypot(...p)>6650000)throw new Error('相机位置超出支持范围');
 if(b.selectedId&&!/^nyc:footprints:(?:doitt|objectid):\d+$/.test(b.selectedId))throw new Error('建筑ID无效');
 if(b.localWalk&&(!Array.isArray(b.localWalk.position)||b.localWalk.position.length!==3||
  !b.localWalk.position.every(Number.isFinite)||!Number.isFinite(b.localWalk.yaw)||!Number.isFinite(b.localWalk.pitch)))throw new Error('局部漫游状态无效');
 return b;
}
