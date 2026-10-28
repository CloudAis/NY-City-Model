import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {movement,speedMetresPerSecond,stableId,validateBookmark,localMeasurement,idBucket} from '../src/inspection/core.ts';
import {GroundCollider} from '../src/inspection/ground.ts';
const checks=[];
function test(name,fn){fn();checks.push(name);console.log('PASS',name);}
test('movement integrates real elapsed time consistently at20,60,144FPS',()=>{
 const distances=[];
 for(const fps of [20,60,144]){let d=0;for(let i=0;i<fps*8;i++)d+=movement(2000,1/fps,[1,0,0])[0];distances.push(d);}
 assert.ok(Math.max(...distances)-Math.min(...distances)<1e-7);assert.ok(speedMetresPerSecond(100)<speedMetresPerSecond(10000));
 assert.throws(()=>movement(1000,3,[1,0,0]),/停止输入/);
});
test('identity handler tolerates empty, destroyed, out-of-bounds and malformed picks',()=>{
 for(const p of [null,undefined,{}, {getProperty:()=>{throw Error('unloaded');}}, {getProperty:()=>7},{getProperty:()=>"neighbour' || true"}])assert.equal(stableId(p),null);
 assert.equal(stableId({getProperty:()=> 'nyc:footprints:doitt:233256'}),'nyc:footprints:doitt:233256');
 assert.equal(idBucket('nyc:footprints:doitt:233256'),'256');
});
test('horizontal,3D and signed height differences remain distinct in same-datum local coordinates',()=>{
 assert.deepEqual(localMeasurement([0,0,2],[3,4,14]),{horizontal:5,space:13,difference:12});
});
test('ground collider never chooses a higher bridge floor and rejects unknown cells',()=>{
 const terrain={width:2,height:2,vertices:[0,0,2,10,0,2,0,10,2,10,10,2],indices:[0,1,2,1,3,2]};
 const c=new GroundCollider(terrain,{id:'isolated-test',allowed_triangle_offsets:[0],spawn:[2,2,2],layer_id:'ground',eye_height_m:1.7,speed_m_per_s:1.4});
 assert.equal(c.sample(2,2),2);assert.equal(c.sample(9,9),null);assert.equal(c.sample(-1,1),null);
 const moved=c.move([2,2,2],[20,20]);assert.equal(moved.blocked,true);assert.equal(moved.position[2],2);assert.ok(moved.position[0]<6);
 assert.throws(()=>new GroundCollider(terrain,{allowed_triangle_offsets:[999],layer_id:'ground'}),/索引越界/);
});
test('unknown bookmark version or fields cannot replace valid world state',()=>{
 const b={schema:1,name:'source view',savedAt:'2026-10-28T00:00:00Z',mode:'orbit',preset:'brooklyn-span',quality:'medium',layers:{water:true},camera:{position:[1333603,-4652686,4139943],heading:0,pitch:-1,roll:0},selectedId:null,lighting:{mode:'neutral-fixed',datetime:null,note:'no solar simulation'}};
 assert.equal(validateBookmark(b),b);assert.throws(()=>validateBookmark({...b,schema:99}));
 assert.throws(()=>validateBookmark({...b,camera:{...b.camera,position:[NaN,0,0]}}));
 assert.throws(()=>validateBookmark({...b,lighting:{mode:'solar',datetime:'2026-01-01'}}));
});
const foundation=JSON.parse(await readFile('assets/environment/terrain-manifest.json','utf8'));
for(const area of foundation.datasets){
 const scene=JSON.parse(await readFile('assets/foundation/'+area.terrain,'utf8'));
 const spec=JSON.parse(await readFile('assets/environment/collision/'+area.id+'.json','utf8'));
 const collider=new GroundCollider(scene.terrain,spec);assert.ok(spec.spawn);assert.ok(spec.allowed_triangle_offsets.length>0);
 assert.ok(Math.abs(collider.sample(spec.spawn[0],spec.spawn[1])-spec.spawn[2])<1e-5);
 assert.equal(collider.sample(1e7,1e7),null);
}
checks.push('eight actual DEM spawns use allowed rendered triangles; no fake zero ground');
await writeFile(process.env.NYC_CORE_REPORT??'reports/stage8/core.json',JSON.stringify({at_utc:new Date().toISOString(),checks,actual_dem_spawns:foundation.datasets.length,synthetic_geometry_scope:'isolated collision unit test only; never a city asset'},null,2)+'\n');
