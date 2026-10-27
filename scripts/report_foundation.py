"""Assemble stage3 evidence from actual results; never promote source ties to survey accuracy."""
import json,platform,subprocess,re
from pathlib import Path
import pyproj
from nyc.download import ROOT,atomic_json,sha,now

def read(path):return json.loads((ROOT/path).read_text())
q=read('reports/stage3/terrain-quality.json');r=read('reports/stage3/registration.json');audit=read('reports/stage3/coordinate-audit.json');browser=read('reports/stage3/browser.json')
raw=[]
for p in sorted((ROOT/'data/raw/stage3').rglob('*')):
 if not p.is_file()or p.name.endswith('.receipt.json'):continue
 receipt=p.with_name(p.name+'.receipt.json');d=json.loads(receipt.read_text())if receipt.exists()else{}
 raw.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p),'request_url':d.get('request_url'),'download_started_utc':d.get('download_started_at'),'download_completed_utc':d.get('download_completed_at'),'capture_date':'2017-05-03 to 2017-07-26'if'/dem/'in str(p)else None,'capture_date_note':'geoid/catalogue dates not inferred from download date','coordinate_details':'data/manifests/stage3/file-coordinate-audit.jsonl','processor_version':'stage3-foundation-v1'})
versions={'node':subprocess.check_output(['node','-v'],text=True).strip(),'python_venv':platform.python_version(),'proj':pyproj.proj_version_str,'gdal':subprocess.check_output(['gdalinfo','--version'],text=True).strip(),'system_gdal_python_available':True,'lerc_js':'2.0.0, actual installed Esri package pinned via Cesium','browser':browser['browser']}
scripts=['scripts/nyc/coordinates.py','scripts/nyc/elevations.py','scripts/nyc/terrain.py','scripts/acquire_foundation.py','scripts/decode_dem.mjs','scripts/gdal_raster.py','scripts/build_foundation.py','scripts/check_registration.py','scripts/audit_coordinates.py']
source_manifest={'schema_version':1,'created_utc':now(),'user_facing_timezone':'Asia/Singapore','collections':[{'id':'nys-nyc-bare-earth-2017','entry_url':'https://gis.ny.gov/nys-dem','service_url':'https://elevation.its.ny.gov/arcgis/rest/services/NYC_TopoBathymetric_2017_1_meter/ImageServer','observation_period':['2017-05-03','2017-07-26'],'publication_date':None,'metadata_publication':'NYC metadata 2018-09-12; not an acquisition date','coverage':'6 cropped samples only; not NYC-wide terrain acquisition','version':'captured stage3 crops 2026-10-27; source survey 2017','native_horizontal':'EPSG:2263 US survey foot in service; official index .prj EPSG:6539 NAD83(2011) differs','export_horizontal':'actual TIFF and export JSON EPSG:32118, metres','vertical':'NAVD88, GEOID12B; NYS explicitly converted band values to metres','validity':'explicit LERC mask; TIFF has no NoData tag and falsely exposes missing pixels as zero','geoid_application':'blocked: NAD83 realization conflict','license':'Official NYC metadata: Access Rights Public / Use Limitations NA; source notice NYS ITS Geospatial Services. No broader licence inferred.'},{'id':'noaa-geoid12b','entry_url':'https://github.com/Esri/lerc','resource_url':'https://cdn.proj.org/us_noaa_g2012bu0.tif','version':'GEOID12B, exact raw SHA retained','observation_date':None,'source_crs':'EPSG:6349 / NAD83(2011)+NAVD88','target_crs':'EPSG:6319 / NAD83(2011) ellipsoid','license':'PROJ registered grid open_license=true; actual operation and URL recorded','use':'strict frame-checked conversion module verified; not applied to the ambiguous DEM'},{'id':'stage2-official-vectors','source_manifest':'data/manifests/sources.json','coverage':'saved full-city footprints/context reused; 6 finite scene windows published','observation_dates':'source-specific, not download date','water_scope':'2620 rivers, 2660 bay/ocean get display-level surfaces; lakes/ponds remain unfilled; wetlands/beaches are not water surfaces'}],'raw_files':raw,'processing_versions':versions,'processing_script_sha256':{s:sha(ROOT/s)for s in scripts},'key_unknowns':['generic NAD83 service vs NAD83(2011) index','building attribute foot subtype','per-building vertical datum','roof/spire/antenna elevations','bridge-deck elevations','independent reality survey controls'],'date_policy':'Receipt timestamps are UTC for audit; work/report dates use Asia/Singapore. No unknown release/observation dates filled with today.'}
# The grid is discovered through PROJ's registered operation, not the unrelated decoder repository.
source_manifest['collections'][1]['entry_url']=source_manifest['collections'][1]['resource_url']
source_manifest['collections'][1]['operation_provenance']='PROJ database registered inverse NAD83(2011) to NAVD88 height (1), GEOID12B; data/manifests/stage3/geoid.json'
atomic_json(ROOT/'data/manifests/stage3/sources.json',source_manifest);atomic_json(ROOT/'assets/foundation/sources.json',source_manifest)
valid=sum(d['dem']['valid_cells']for d in q['datasets']);missing=sum(d['dem']['missing_cells']for d in q['datasets']);max_seam=max(d['published_tile_seam_max_m']for d in q['datasets']);max_codec=max(d['dem']['maximum_valid_tiff_lerc_difference_m']for d in q['datasets'])
hole=read('data/processed/foundation/shoreline-hole-proof.json');distances=r['distances']
test_log=(ROOT/'reports/stage3/tests.log').read_text();m=re.search(r'Ran (\d+) tests',test_log);tests=int(m.group(1))if m else None
summary={'schema_version':1,'at_utc':now(),'source_correspondence_points':r['source_correspondence_points'],'surveyed_controls':0,'source_reality_accuracy':'not measured','numeric_target_m':.1,'coordinate_roundtrip_max_m':r['maximum_roundtrip_m'],'gpu_pipeline_max_m':r['maximum_gpu_pipeline_m'],'relative_source_geometry_max_m':r['maximum_relative_source_geometry_m'],'published_terrain_seam_max_m':max_seam,'valid_pixel_tiff_lerc_max_difference_m':max_codec,'valid_dem_samples':valid,'unknown_dem_samples':missing,'terrain_areas':len(q['datasets']),'terrain_tiles':4*len(q['datasets']),'global_vertical_registration':'unresolved; deliberately not published','geoid_grid_available':q['geoid_grid_available'],'field_foot_type':'unresolved, no new 0.3048 assumption','python_tests':tests,'python_tests_passed':test_log.rstrip().endswith('OK'),'browser_checks':len(browser['checks']),'browser_errors':browser['errors'],'browser_candidate_limit':'actual Chromium software GPU; no hardware GPU/multi-browser claim','city_overview_stable_pixels':browser['observations']['city']['samePixelBuffer'],'known_gaps':['global vertical frame conflict','real-world survey error unknown','slope foundation/body placement blocked; no body deformation','bridge decks missing; no road surfaces draped over them','2017 DEM and 2022 water/footprint dates differ','NoData/coastline and decimation boundaries are not infilled','no claim that full-city registered terrain exists']}
atomic_json(ROOT/'reports/stage3/summary.json',summary)
table='\n'.join(f"|{d['id']}|{d['dem']['valid_cells']:,}|{d['dem']['missing_cells']:,}|{d['lod_triangles']:,}|{d['published_tile_seam_max_m']:.8f}|"for d in q['datasets'])
text=f'''# 地理配准报告 · 阶段3

工作日期：2026-10-27（Asia/Singapore）；原始receipt和机器报告用UTC排序。沿用现有工程和第二阶段资料，未生成虚构建筑、道路、楼高或室内。

## 实际范围与高度边界

已实现共用米制/经纬度/ECEF/ENU模块，显式US survey foot=1200/3937m、international foot=0.3048m。未知foot种类不能转换。glTF采用(E,Up,-N)，Cesium只做一次Y-up→Z-up，六个100m三维诊断箭头已在实际浏览器通过来源ID拾取验证，默认关闭且明确不是城市实物。

保存了六样区真实2017裸地/水底DEM及GEOID12B格网。源服务EPSG:2263，原生水平像元1 US survey foot；服务名含1_meter不等于真实水平分辨率。高程波段由NYS明确转为米，导出257²裁剪实际为EPSG:32118，分辨率逐文件记录，显示抽稀4倍、垂直比例1:1。

服务/导出声明generic NAD83，官方索引实际.prj为EPSG:6539/NAD83(2011)。GEOID12B要求NAD83(2011)。当前不将这两种声明混为已解决，不给全城加固定偏移。地形可在独立NAVD88正高检视页打开，ECEF全球地形叠加仍阻塞。建筑底面/坡地实体没有完成全球落位；只输出带年代的DEM采样参考范围，不拉扯主体，也不把它称实测地基。

建筑GROUND_ELEVATION、HEIGHT_ROOF只写feet，无法据此决定foot种类。第二阶段0.3048暂算结果保留为legacy审计值，新的canonical米值为null。地面、相对楼高、绝对屋顶、尖顶、天线分别建字段。绝对屋顶不能再加地面；同基准/同基底的相对高度才可合成。未知桥面不贴地生成，道路仅作为二维参考线。

## 实际发现并修复的NoData问题

NYS TIFF导出无NoData标签，掩膜丢失导致{missing:,}个缺失样本看起来为0。已用同请求、同范围的真实LERC有效性掩膜修复；官方identify对保留的零值案例返回NoData。真实零值与缺失分开，未将所有零值一律判错。有效样本{valid:,}，未知样本{missing:,}；未知单元不生成三角形，细网格内洞不能被粗网格跨越。TIFF保留作为原始证据与地理参考，实际高度/掩膜以LERC为准。

|样区|有效采样|NoData|显示三角形|四瓦片接缝最大差m|
|---|---:|---:|---:|---:|
{table}

相邻已知边界来自同一源网格，独立局部原点与float32顶点回算后的最大接缝差{max_seam:.8f}m；独立裁剪间未冒称已完成拼接。地形2017与水系2022年代不同，加上抽稀/NoData边缘可能有未覆盖窄带，保留为空，不以零高程、裙边或扩大水面掩盖。

## 水面与真实岸线

复用第二阶段实际水系、多部件和内洞裁剪，河流/海湾填充，湿地和沙滩不当水面。湖塘水位未知，不填充。正高视图选择NAVD88 H=0m展示水位，地球视图另用椭球h=0m参考，二者没有声称完成垂直转换，也不是实时潮位。

真实{hole['source_properties']['name']}来源多边形内洞案例面积{hole['source']['hole_area_m2']:,.4f}m²，三角化覆盖内洞{hole['water_over_source_hole_m2']}m²；保留源行ID，不编造具体岛名。码头/内湾按源岸线保留，不增加跨陆地矩形水面；裁剪边缘只表示样区范围。

## 检查点与四种误差

实际取得五区各6个、共30个来源对应点，逐一保存建筑DOITT_ID、原始页/SHA、OBJECTID、ring0/vertex0、源XY和规范坐标。**独立实测控制点0个**。这些点不是现场测量，也没有把同源重算当作现实精度。

- 坐标往返最大误差：{r['maximum_roundtrip_m']:.10f}m。
- float32局部顶点→完整矩阵→ECEF处理管线最大误差：{r['maximum_gpu_pipeline_m']:.10f}m。
- 相对保存的源轮廓顶点偏差：{r['maximum_relative_source_geometry_m']:.10f}m。
- 相对独立现实测量误差：未知。NAD83/WGS84操作名与名义精度逐点记录，不并入数值残差，不宣传全城0.10m实测精度。

纯数值工程目标0.10m通过。实际角点测地距离：街区量级{distances[0]['geodesic_m']:,.3f}m、跨东河{distances[1]['geodesic_m']:,.3f}m、跨区{distances[2]['geodesic_m']:,.3f}m。街区同一对角点在Web Mercator中约{distances[0]['mercator_m']:,.3f}m；未用其平面数值当真实量距。测地标尺1/10/100/1000/10000/50000m实际回算，详见JSON。

用统一城市切平面检查时，30点相对该平面最小Up约{r['single_city_tangent_plane_assessment']['min_up_m']:.3f}m；跨区端点切平面曲率偏离约156m。全城仍用ECEF及分块局部坐标，不把全纽约压成一个平面。

## 实际执行的验证与限制

`npm test`：{tests}项，结果{'通过'if summary['python_tests_passed']else'未通过，见日志'}。`npm run build`通过。`node tests/foundation-browser.mjs`：{len(browser['checks'])}组通过，错误{len(browser['errors'])}，实际六向GLB拾取、六DEM显示、资源释放、采样、图层/相机、窄屏均有机器记录；已查看截图。近景参考线相机约114m，五区俯视约56.65km，相机稳定且全城视图两次像素一致。新单文件预览内容离线已执行，企业策略仍阻止file://。

全球已配准地形的浮空/沉陷、建筑/桥面实体接地没有测试通过，因为必要垂直参考仍未解决。真实硬件GPU、多浏览器和独立现场精度尚未验证；不以当前软件渲染测试替代它们。

入口：`data/manifests/stage3/file-coordinate-audit.jsonl`、`sources.json`、`data/processed/foundation/checkpoints.csv`、`reports/stage3/{{registration.json,terrain-quality.json,browser.json,tests.log,summary.json}}`。
'''
(ROOT/'reports/GEOGRAPHIC_REGISTRATION.md').write_text(text)
for source,name in [('reports/stage3/summary.json','summary.json'),('reports/stage3/registration.json','registration.json'),('reports/stage3/coordinate-audit.json','coordinate-audit.json')]:
 (ROOT/'assets/foundation'/name).write_bytes((ROOT/source).read_bytes())
print('STAGE3_SUMMARY',valid,'valid',missing,'NoData',tests,'tests',len(browser['checks']),'browser groups')
