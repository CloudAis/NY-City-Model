# 架构

TypeScript + Vite + CesiumJS；Python/pyproj/Shapely处理GIS；GLB/glTF 2.0 + 3D Tiles 1.1，CPU双精度定位，GPU瓦片ENU局部米坐标。固定版本在package-lock.json及requirements-lock.txt。

raw(只追加原始响应+receipt) → intermediate(下载分片/恢复点) → processed(规范化记录) → assets(发布瓦片/清单)。download、解压、解析、规范化、发布各自缓存与结果，不让失败重跑破坏原始资料。

运行无Cesium ion、云地形、收费底图。椭球作为明确标记的显示参考面，不能解释成真实地面高程。当前轮廓GLB是测绘线，不是补全的立体楼群。真实屋顶/立面/地形须后续取得证据。

Tinnis既有相机/DOM/拾取逻辑属于虚构微缩游戏，与Cesium坐标及分块加载不同；只参考交互概念，不迁移建筑资产或随机世界生成。比较：旧Three框架需自建ECEF/分块/LOD；Cesium原生高精度定位与3D Tiles，代价是运行资源更大。沿用用户默认Cesium路线。

全市采用SQLite（约4.7GiB），buildings以(capture,id)为主键，BIN/BBL非唯一索引；pages与记录在同一事务提交，quarantine独列失败。处理器SHA改变时拒绝复用规范化缓存。RTree为米制float32向外扩包围框粗筛，最终用float64多边形精确相交。该库不直接发送浏览器。

六样区按500m网格发布GLB LINES/3D Tiles 1.1，EXT_mesh_features与EXT_structural_metadata保留源ID，实际Cesium拾取已验证。根节点非零geometricError、叶节点0；启动加载小样区档案，GLB按视野请求。全市LOD/大规模档案服务留第三阶段。不将未核验高度挤出实体。单文件另用内联WebGL2，复用规范化数据和ENU，避免内嵌整套Cesium。

上下文GeoPackage通过逐页投影缓存、临时合并、计数核对后原子发布。PLUTO关联保留parcel scope。历史3dm的曲线/Brep/重复图层未强行合并或套用当前建筑ID。

下载重试有界、指数退避、限速、类型校验与磁盘/单文件预算。仅ETag/Range可验证时续传，否则重新开始该请求。相同raw不改mtime，不同响应另存哈希文件。解压只有完整receipt后复用；未完成文件会安全报错，需保留raw、移走该派生目录再解压，而非把半成品当成功。
