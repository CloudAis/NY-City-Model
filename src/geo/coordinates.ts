import {Cartesian3,Cartographic,EllipsoidGeodesic,Matrix4} from 'cesium';

export const US_SURVEY_FOOT_METRES=1200/3937;
export const INTERNATIONAL_FOOT_METRES=.3048;
export type GeographicDegrees=Readonly<{longitudeDeg:number;latitudeDeg:number}>;
export type Wgs84EllipsoidHeight=Readonly<{metres:number;datum:'WGS84_ELLIPSOID'}>;
export interface FrameRecord {origin_ecef_m:number[];enu_to_ecef_column_major:number[];origin_longitude_latitude_degrees:number[];origin_ellipsoid_height_m:number}

export function degrees(longitudeDeg:number,latitudeDeg:number):GeographicDegrees {
 if(!Number.isFinite(longitudeDeg)||!Number.isFinite(latitudeDeg)||Math.abs(longitudeDeg)>180||Math.abs(latitudeDeg)>90)throw new Error('明确的经度、纬度（度）必需');
 return {longitudeDeg,latitudeDeg};
}
export function worldPosition(p:GeographicDegrees,height:Wgs84EllipsoidHeight):Cartesian3 {
 if(height.datum!=='WGS84_ELLIPSOID'||!Number.isFinite(height.metres))throw new Error('WGS84椭球高未解决，不能放置到ECEF世界');
 return Cartesian3.fromDegrees(p.longitudeDeg,p.latitudeDeg,height.metres);
}
export function referencePosition(lonLat:number[],displayLiftM=0):Cartesian3 {
 return worldPosition(degrees(lonLat[0],lonLat[1]),{metres:displayLiftM,datum:'WGS84_ELLIPSOID'}); // Display reference only; never a ground datum conversion.
}
export function localEnuToWorld(frame:FrameRecord,enu:number[]):Cartesian3 {
 return Matrix4.multiplyByPoint(Matrix4.fromArray(frame.enu_to_ecef_column_major),new Cartesian3(enu[0],enu[1],enu[2]),new Cartesian3());
}
export function geodesicMetres(a:GeographicDegrees,b:GeographicDegrees):number {
 return new EllipsoidGeodesic(Cartographic.fromDegrees(a.longitudeDeg,a.latitudeDeg),Cartographic.fromDegrees(b.longitudeDeg,b.latitudeDeg)).surfaceDistance;
}
export const gltfToEnu=(p:readonly number[])=>[p[0],-p[2],p[1]];
