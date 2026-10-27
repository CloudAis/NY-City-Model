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
