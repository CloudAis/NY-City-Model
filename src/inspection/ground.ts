/** Use the selected ground layer only. Never snap to an unrelated higher bridge deck. */
export interface GroundTerrain {vertices:number[];indices:number[];width:number;height:number}
export interface CollisionSpec {id:string;allowed_triangle_offsets:number[];spawn:number[]|null;layer_id:'ground';eye_height_m:number;speed_m_per_s:number}
export class GroundCollider {
 private cells=new Map<string,number[]>();
 readonly terrain:GroundTerrain;
 readonly spec:CollisionSpec;
 constructor(terrain:GroundTerrain,spec:CollisionSpec){
  this.terrain=terrain;this.spec=spec;
  if(spec.layer_id!=='ground')throw new Error('需要明确的地面碰撞层');
  for(const offset of spec.allowed_triangle_offsets){
   if(offset%3||offset<0||offset+2>=terrain.indices.length)throw new Error('碰撞索引越界');
   const ids=terrain.indices.slice(offset,offset+3);
   const c=Math.min(...ids.map(i=>i%terrain.width)),r=Math.min(...ids.map(i=>Math.floor(i/terrain.width)));
   const key=c+':'+r;this.cells.set(key,[...(this.cells.get(key)??[]),offset]);
  }
 }
 sample(x:number,y:number):number|null {
  const t=this.terrain,v=t.vertices,dx=v[3]-v[0],dy=v[t.width*3+1]-v[1];
  const c=Math.floor((x-v[0])/dx),r=Math.floor((y-v[1])/dy);
  if(c<0||r<0||c>=t.width-1||r>=t.height-1)return null;
  for(const offset of this.cells.get(c+':'+r)??[]){
   const [a,b,d]=t.indices.slice(offset,offset+3).map(i=>v.slice(i*3,i*3+3));
   const den=(b[1]-d[1])*(a[0]-d[0])+(d[0]-b[0])*(a[1]-d[1]);
   const u=((b[1]-d[1])*(x-d[0])+(d[0]-b[0])*(y-d[1]))/den;
   const q=((d[1]-a[1])*(x-d[0])+(a[0]-d[0])*(y-d[1]))/den,w=1-u-q;
   if(u>=-1e-8&&q>=-1e-8&&w>=-1e-8)return u*a[2]+q*b[2]+w*d[2];
  }
  return null;
 }
 move(position:number[],delta:number[]):{position:number[];blocked:boolean}{
  if(![...position,...delta].every(Number.isFinite))throw new Error('有限地面位置必需');
  const steps=Math.max(1,Math.ceil(Math.hypot(delta[0],delta[1])/.2));let p=[...position],blocked=false;
  for(let i=0;i<steps;i++){
   const x=p[0]+delta[0]/steps,y=p[1]+delta[1]/steps,z=this.sample(x,y);
   if(z===null){blocked=true;break;}p=[x,y,z];
  }
  return {position:p,blocked};
 }
}
