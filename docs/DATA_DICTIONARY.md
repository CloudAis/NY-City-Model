# 字段字典

阶段5landmarks/<slug>：dossier保存稳定原ID/BIN、身份范围、坐标或null、目标日期和四项statuses；dimensions.parameters保存source_value/unit、value_m、原文证据URL/路径/SHA/quote、换算/推导、uncertainty_m（未知null）和project_review_tolerance_m（项目阈值，非来源精度）。conflicts保留竞争数值/年代/选择依据。components区分已输出与缺失；materials类别证据与检查色度/粗糙度分开；references.views明确拍摄日/方位/校准状态；validation保存实际生成相机和数值残差、现实误差null。source-building.json为阶段2完整payload审计快照，其中height_m/ground_elevation_m只是legacy，不是阶段5canonical参数。manifest中的published_representations不等于fine_model_complete。

原始字段和domains以保存的footprints-layer.json为准。

|规范字段|官方字段/口径|处理|
|---|---|---|
|id / source_id|DOITT_ID|稳定内部ID含来源命名空间；缺失时带版本标记的OBJECTID回退，不用BIN作主键|
|source_object_id|OBJECTID|服务抓取分页键，不能承诺跨版本稳定|
|bin|BIN|字符串保留；百万整值为占位，重复允许，建立关系而非去重删楼|
|base_bbl / mappluto_bbl|BASE_BBL / MAPPLUTO_BBL|物理地块与billing地块区分；地块属性不直接当建筑属性|
|part_id|规范MultiPolygon部件|来源ID下的部件映射，记录修复后排序依据|
|name|NAME|缺失保留null，字段不活跃维护，不视为现名已核实|
|address / floors|无对应可信建筑字段|保留null；PLUTO只能作为关联地块证据|
|height_m|HEIGHT_ROOF|相对地面屋顶高度；0/null未知，负数异常，不默认楼高|
|ground_elevation_m|GROUND_ELEVATION|英尺换米，负值允许；基准证据另列|
|construction_year|CONSTRUCTION_YEAR|0/null未知，不是观测日期|
|feature_code|FEATURE_CODE|1003占位三角形不进入实景主场景；保留原记录|
|geometry_source|GEOM_SOURCE|摄影测量与手工来源区分|
|last_edited_at|LAST_EDITED_DATE|记录编辑日期，不是采集或观测日期|
|geometry|rings + spatialReference|修复前后面积、内洞、多部件及原始记录引用|

每个建筑position/footprint/height/roof/facade/age分别保存source_id、原字段、status（source_explicit / derived / estimated / unknown）、independently_verified布尔、年代和说明。明确来源不等于独立验证。屋顶相对高度不能证明屋顶形状；立面无资料即unknown。

source_version为抓取标签；raw_record保留页路径、SHA、OBJECTID。修复保留area_before_m2/area_after_m2/area_change_m2/area_change_fraction、原始有效性、重复点处理和方法，不覆盖rings。part编号按修复后bounds/area排序，几何跨版本改变时另保留关系，不能声称序号永久不变。

PLUTO 26v2：NumFloors为地块上最高建筑层数，可有2.5等部分楼层，不是每栋楼的层数。YearBuilt按字典通常只有年代级可靠性，0/空未知。BBL是地块键，CSV可能带.000；保留原值和规范键。pluto-pilot-links保留整行地块属性与building_ids，不复制为楼高/楼层/年龄/地址。265项scope问题（221个非空值差异、44个缺失楼级年份）不可直接比较，不自动判定任何一方错误。

道路/水系source_id有真实重复和零占位，不能作分页唯一键；socrata_row_id是版本内唯一行ID，逻辑source_id仍保留。边界用borocode。原始GeoJSON为EPSG:4326角度，GeoPackage为EPSG:32118米。编辑/行更新时间不是航摄采集日。

3dm GUID是历史对象ID，不是当前DOITT_ID/BIN；对象含曲线、Brep、重复表示和地形道路，数量不能当建筑数。Feet与US survey foot差异作为单位冲突保留。

SQLite capture=抓取标签:行政区，payload为完整规范JSON，payload_sha用于语义校验；height_m/ground_m为查询列，前者null不补值，后者负值合法。processor_meta记录处理器SHA；跨capture查询须显式选版本。

阶段3 `foundation/building-elevations.json`覆盖六样区3,027来源记录。`ground`、`building_relative`、`roof_absolute`、`spire_height`、`antenna_height`各含value/unit/quantity/datum/horizontal_frame/ground_reference_id/source；已知原值保存raw_values。`legacy_stage2_*_m`只是旧假设审计值，新canonical米值因foot种类未核为null。地面负数和真实零值可有效，相对楼高不能为负；绝对屋顶禁止再次加地面。

DEM样本采用metre/NAVD88，2017采集；`masked_raster`为真实LERC，`lerc_export_metadata`保留范围/CRS，`raster`TIFF只提供实际地理参考与原始证据。`valid_cells/missing_cells/real_zero_valid_cells/tiff_zero_but_lerc_missing`区分有效、缺失、真实零、错误露零，`maximum_valid_tiff_lerc_difference_m`为编码/处理差，不是测绘精度。缺失写null/NaN，不进入显示三角形。

水系代码2600湖库、2610塘、2620河、2630溪、2640湿地、2650海滩岸线、2660海湾海洋，依据保存的官方Capture Rules。当前只给2620/2660展示水面；其`display_water_level_m=0`有明确场景基准和非潮位标识。未知湖塘不填、湿地沙滩不当水面。道路`elevation/deck_height=null`，不生成贴地桥面。地形上的建筑轮廓是投影检视线，不是已确认基础；`dem_ground_reference`只记录已知2017采样范围。

检查点role固定source-correspondence，现实测量误差为null；geographic字段显式longitude/latitude degrees，source_xy有实际原始CRS。方向箭头的diagnostic_only=true且默认关闭，不计入建筑/地标数量。

新发布GLB属性不再用无标识的height_m暴露旧暂算值，改为relative_height_raw_ft与legacy_stage2_height_m；canonical高度来自严格注册表。GLB和瓦片索引同时保存实际局部原点及完整ENU→ECEF矩阵，外部矩阵只由tileset施加一次，不再作为glTF节点矩阵重复应用。

## 阶段4建筑关联

派生associations.sqlite：objects.id为来源实体唯一键，source_rowid为只读第二阶段库行引用，borough为来源BASE_BBL分区；gx/gy为500m完整对象owner。metadata含source_id/OBJECTID/BIN/BBL/raw路径SHA、原部件ID、版本/日期、state/reasons、geometry_sha256、轮廓面积/范围、内洞/顶点数。geometry是原规范化多边形，不是包围盒。部分来源实体可能不是独立物理建筑。

canonical_height_m和ground_ellipsoid_m保持null。relative_height_raw_ft是来源数值；height_evidence_status区分有效数值但单位未知与缺失/异常。height_hypothesis_m及interval只为明确的international/US-survey-foot比较假设；不提升证据等级，不落到真实地面。semantic_level为outline_only；render_lod明确full_source_outline_no_simplification，两者独立。roof_status/facade_status、observation_date未知继续保留。

state=source_outline_only或excluded_placeholder；reasons包含单位、地面基准、墙线、屋顶部件、观测日、缺失/异常楼高及非普通主体类型原因。历史/拆除状态不能仅由旧模型或编辑日判断；本阶段未确认。GLB严格/假设有相同源ID与parts表，模型表现不是新建筑实体。

工业抽查的parcel_context保留PLUTO LandUse06、主建筑分类和numbldgs；它不等于被抽查单栋的用途。complex_outline标签不等于复杂屋顶证据。原始来源、管线数值误差与现实实测误差分开记录。
