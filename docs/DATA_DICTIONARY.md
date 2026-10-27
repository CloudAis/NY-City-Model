# 字段字典

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
