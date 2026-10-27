# 架构

TypeScript + Vite + CesiumJS；Python/pyproj/Shapely处理GIS；GLB/glTF 2.0 + 3D Tiles 1.1，CPU双精度定位，GPU瓦片ENU局部米坐标。固定版本在package-lock.json及requirements-lock.txt。

raw(只追加原始响应+receipt) → intermediate(下载分片/恢复点) → processed(规范化记录) → assets(发布瓦片/清单)。download、解压、解析、规范化、发布各自缓存与结果，不让失败重跑破坏原始资料。

运行无Cesium ion、云地形、收费底图。椭球作为明确标记的显示参考面，不能解释成真实地面高程。当前轮廓GLB是测绘线，不是补全的立体楼群。真实屋顶/立面/地形须后续取得证据。

Tinnis既有相机/DOM/拾取逻辑属于虚构微缩游戏，与Cesium坐标及分块加载不同；只参考交互概念，不迁移建筑资产或随机世界生成。比较：旧Three框架需自建ECEF/分块/LOD；Cesium原生高精度定位与3D Tiles，代价是运行资源更大。沿用用户默认Cesium路线。
