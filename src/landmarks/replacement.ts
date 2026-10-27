export interface Replacement {eligible:boolean;building_id:string;source_part_ids:string[];hide_source_building_ids:string[];physical_world_replacement_allowed:boolean}
export function hiddenSourceIds(mapping:Replacement,modelVisible:boolean):string[]{
 if(!modelVisible||!mapping.eligible)return[];
 if(mapping.source_part_ids.length!==1)throw new Error('来源含多部件，不能按整栋编号掩盖未完成部件');
 if(mapping.hide_source_building_ids.some(id=>id!==mapping.building_id))throw new Error('替换映射不得隐藏邻楼');
 return [...new Set(mapping.hide_source_building_ids)];
}
export function sourceShowExpression(mapping:Replacement,modelVisible:boolean):string{
 const ids=hiddenSourceIds(mapping,modelVisible);return ids.length?ids.map(id=>'${id} !== '+JSON.stringify(id)).join(' && '):'true';
}
