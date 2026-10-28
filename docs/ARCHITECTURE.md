# 架构

阶段6同工程facades.html：只读RTree→12完整来源AOI→逐边候选面/未知构件→历史图像校正/遮罩→独立UV/feature ID照片面→默认严格/可移除历史参考→运行验证/覆盖报告。图像facade_math不依赖GIS，可用系统Pillow/numpy；GIS仍用原虚拟环境。4历史面不是完整普通建筑，不改既有地标资产与全市高度门控。

阶段5沿用同一工程，新增landmarks.html与src/landmarks。独立档案→逐参数引用校验→局部组件GLB→3D Tiles→来源/模型/替换清单→实际浏览器证据→质量报告。研究/体量/立面/完整验证独立状态。One WTC部分主体与432线网格不计为完整精细模型。精确原ID筛选仅在参考检视器隐藏One WTC单对象；432项目含裙房故拒绝替换。全局替换权限保持false。照片/PDF原件不分发。

TypeScript + Vite + CesiumJS；Python/pyproj/Shapely处理GIS；GLB/glTF 2.0 + 3D Tiles 1.1，CPU双精度定位，GPU瓦片ENU局部米坐标。固定版本在package-lock.json及requirements-lock.txt。

raw(只追加原始响应+receipt) → intermediate(下载分片/恢复点) → processed(规范化记录) → assets(发布瓦片/清单)。download、解压、解析、规范化、发布各自缓存与结果，不让失败重跑破坏原始资料。

运行无Cesium ion、云地形、收费底图。椭球作为明确标记的显示参考面，不能解释成真实地面高程。当前轮廓GLB是测绘线，不是补全的立体楼群。真实屋顶/立面/地形须后续取得证据。

Tinnis既有相机/DOM/拾取逻辑属于虚构微缩游戏，与Cesium坐标及分块加载不同；只参考交互概念，不迁移建筑资产或随机世界生成。比较：旧Three框架需自建ECEF/分块/LOD；Cesium原生高精度定位与3D Tiles，代价是运行资源更大。沿用用户默认Cesium路线。

全市采用SQLite（约4.7GiB），buildings以(capture,id)为主键，BIN/BBL非唯一索引；pages与记录在同一事务提交，quarantine独列失败。处理器SHA改变时拒绝复用规范化缓存。RTree为米制float32向外扩包围框粗筛，最终用float64多边形精确相交。该库不直接发送浏览器。

六样区按500m网格发布GLB LINES/3D Tiles 1.1，EXT_mesh_features与EXT_structural_metadata保留源ID，实际Cesium拾取已验证。根节点非零geometricError、叶节点0；启动加载小样区档案，GLB按视野请求。全市LOD/大规模档案服务留第三阶段。不将未核验高度挤出实体。单文件另用内联WebGL2，复用规范化数据和ENU，避免内嵌整套Cesium。

上下文GeoPackage通过逐页投影缓存、临时合并、计数核对后原子发布。PLUTO关联保留parcel scope。历史3dm的曲线/Brep/重复图层未强行合并或套用当前建筑ID。

下载重试有界、指数退避、限速、类型校验与磁盘/单文件预算。仅ETag/Range可验证时续传，否则重新开始该请求。相同raw不改mtime，不同响应另存哈希文件。解压只有完整receipt后复用；未完成文件会安全报错，需保留raw、移走该派生目录再解压，而非把半成品当成功。

阶段3共用Python `nyc/coordinates.py`与TS `geo/coordinates.ts`，世界采用WGS84/ECEF和每块ENU；glTF写(E,Up,-N)，引擎Y-up到Z-up只做一次。原点、轴、完整列主序矩阵与参考面明确保存。建筑、道路、水系及未来地标必须遵守同一契约；旧3dm的Feet冲突未解决，不放进世界。

`elevations.py`将地面、相对楼高、绝对屋顶、尖顶、天线分开；未明确foot种类或垂直参考时不产生canonical米值。旧阶段2暂算值保留为legacy。`GeoidConversion`只接受明确NAD83(2011)+NAVD88，产物仍为NAD83(2011)椭球高，需要另选框架转换才可进入WGS84世界。

真实裸地处理使用实际GDAL地理参考与官方Esri LERC有效性掩膜。NYS TIFF导出会把NoData露成0，已发现并以同范围LERC修复；不能只按像元有限或为0判定地面。每源网格分四个独立局部原点块，边界共享真实采样；遇缺失不造三角形/裙边。水面按原水系多边形及内洞三角化，水底DEM与展示水位分开；无桥面资料不生成贴地桥。

两个入口共用工程/资源：`index.html`为ECEF地理参考与检查层，`terrain.html`为局部EPSG:32118+NAVD88正高检视。当前源服务generic NAD83与索引NAD83(2011)冲突，地形全球叠加保持阻塞，正高检视不冒称ECEF配准。它使用小型WebGL2渲染器和共享矩阵库，没有新建无关联项目或依赖云服务。GPU缓冲每次换样区释放，静止不持续重绘。

## 阶段4建筑表示

同一工程新增buildings.html，不重建演示。Python的nyc/buildings.py管理证据门控、完整多边形、部件和中性GLB；build_buildings.py管理只读源库→可恢复派生SQLite→双表示瓦片→原子清单。source/processor SHA变化时拒绝旧work复用。原始数据只读。

严格模式只有来源俯视轮廓。显式hypothesis是原HEIGHT_ROOF与未确认international-foot假设的开口垂直包络，canonical高度仍null；不封顶，不作为墙基线或真实主体。停车/棚/罐/占位/悬挑/连廊/施工记录有专门原因，后几类不盲目拉到地面。可靠屋顶、立面、当前旧模型关联和LiDAR提取仍缺证据。

完整对象以来源包围框中心归属唯一500m格；保留原几何跨格，不裁断、不按BIN/共墙合并。每块最多200来源对象，UINT32索引/feature ID和结构化元数据保持可拾取。每块独立ENU和外部ECEF矩阵，根/叶几何误差和实际包围体齐全。语义证据与渲染LOD独立。

全市完整细节采用近区viewerRequestVolume与显式7000m俯视暂停；没有未披露的盒楼LOD。运行时仅本地GLB/JSON。构建同卷普通硬链接大资源、跨卷回退复制，ZIP独立读回SHA/CRC；工作库/原始大数据不依赖Git传输。
