import type {FrameRecord} from '../geo/coordinates';
export interface Facade {
 id:string; building_id:string; outward_azimuth_degrees:number; width_projected_m:number;
 height_m:number|null; endpoints_lon_lat:number[][]; evidence_status:string;
 components:Record<string,{status:string;value:unknown}>; current_complete:boolean;
 historical_evidence?:{date:string;status:string;material:{value:string};components:Record<string,{status:string;value:unknown}>};
}
export interface Building {
 id:string; bin:string|null; base_bbl:string|null; height_m:null; facades:Facade[];
 geometry_wgs84:{type:string;coordinates:unknown}; raw_record:{path:string;sha256:string};
 archival_front?:{date:string;texture:string;width_conflict_m:number;scope:string};
}
export interface AreaSummary {
 id:string;name:string;borough:string;category:string;bbox:number[];building_denominator:number;
 facade_candidate_denominator:number;details:string;tileset:string;
}
export interface CameraStop {id:string;label:string;azimuth_deg:number;pitch_deg:number;range_m:number}
export interface Area {summary:AreaSummary;buildings:Building[];fixed_observation_path:CameraStop[]}
export interface Street {
 frame:FrameRecord;credit:string;rights:Record<string,string>;
 fronts:{building_id:string;address:string;texture:string;unknown_pixel_fraction:number;
 historical_plane_height_m:number;historical_plane_width_m:number;width_conflict_m:number;pick_point_local_enu_m:number[]}[];
 fixed_path:{id:string;label:string;enu_camera:number[];enu_target:number[]}[];
}
export interface Manifest {
 areas:AreaSummary[];area_count:number;unique_source_buildings:number;current_verified_facades:number;
 current_complete_streets:number;procedural_facades:number;history:string;history_tileset:string;
}
