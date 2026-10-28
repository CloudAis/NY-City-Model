# 性能与稳定性接续入口

固定/workspace/nyc-3d-html。先读AGENTS、PROJECT_BRIEF、ARCHITECTURE、PROGRESS、QUALITY和reports/PERFORMANCE_REVIEW.md、STABILITY_REVIEW.md；实际源/运行检查点ebc86ce，最终文档/交付记录见本次Git提交。不另起演示、不变真实尺寸或丢原模型。

直接使用：

1. assets/performance/manifest及五区root/pages，完整引用7,383原严格叶；旧assets/buildings-city/主库/原精细资产完整，input-integrity保存原22178发布文件与其余来源SHA。不要因克隆缺大数据而补随机模型。
2. src/inspection/runtime、search.worker、main及受限terrain入口。Cesium1.146两个private预算适配器升级需源码复核；公开loadJson用于可取消根JSON，Resource会克隆实例。
3. config/performance-route、tests/performance的同探针基准/故障/固定机位/真实时长soak、scripts/report_performance与package_performance；短soak不能写30分通过。
4. reports/stage9/comparison含逐段/整体受控数据，优化峰值主堆降低但部分P99回退；初方案结果也保留。soak/result实际1822.909秒、37轮、0错误且不重载，memory-trend明确GC与主isolate/估算范围。
5. 性能ZIP是显式有完整旧五区基底依赖的overlay，包外SHA/实际解压检查不参与ZIP自校验循环。新静态目录/模型来源仍为原工程，不宣称当前全城精细复刻完成。

后续优先：真实GPU/移动硬件上重复相同路线，多次配对测量与CPU/GPU分析，定位首景/跨区长帧，不以删楼、缩城或隐式换低模优化成绩。按真实设备重新选请求/创建预算；如派生几何LOD/压缩必须保留原件并加固定机位/数值误差。当前仅元数据与调度变化，不在此轮继续大规模重建。

全局高程/桥面及可信建筑主体/屋顶/现状立面的前期任务仍独立待补，不把性能通过当真实性通过。当前授权范围已结束，下一阶段待用户明确指定。

---

# 第7/8部分接续入口

固定/workspace/nyc-3d-html。先读AGENTS、全部docs、reports/ENVIRONMENT_REVIEW.md、INTERACTION_REVIEW.md、stage7/quality.json和stage8/browser.json。保持原坐标/轮廓与数据原件；不要另起演示或推定已完成全部物理环境。

可直接输入：

1. assets/environment/manifest、25区域3D Tiles/context、parks-source、桥梁dossiers与data/manifests/stage7，219原始载荷本地保留。用acquire_environment复核更新，变化另存版本。
2. scripts/build_environment.py --vectors-only生成真实边界输入，acquire_park_terrain取两公园，再完整build_environment产生八区碰撞。新terrain-manifest不修改旧foundation六区资产。
3. src/inspection的core/search/ground/main与inspection.html；搜索静态分片775MB、大环境145MB本地缓存，源码Git只留清单/脚本和小碰撞。没有数据恢复时明确失败，不生成替代楼群。
4. reports/stage7的121道路候选、1633树投影候选、14几何修复、25真实观察截图/记录、input-integrity；它们不是独立测量或已确认建筑侵路。
5. 第8部分完整验证记录、三入口回归与offline overlay；真实手机/硬件GPU/多浏览器未测。

优先继续解决DEM实际参考框架/格网、桥面绝对高程/宽度/引桥纵断/塔截面、同年代道路/基础关系，逐桥真实模型与桥下碰撞后才解除地面限制。再补有日期许可的路灯/设施/公园路径资料。既有建筑canonical高度仍空、当前完整立面/可信主体未完成；不把交互或来源数量当作几何完成。

当前范围止于用户授权第7/8部分；后续工作待用户明确指定，不自动引入交通、动态人车或艺术夜景。

---

# 当前阶段6接续：完整街段外观尚未完成

固定/workspace/nyc-3d-html，先读AGENTS、全部docs、reports/FACADE_REVIEW.md与stage6/quality.json。用户已授权普通建筑阶段，保留地标未完成项，不重建独立演示。

直接输入：

1. config/facade-areas.json和assets/facades/<area>：12明确范围、918对象、10,667候选边，原ID/部件/原页/真实完整轮廓/逐面未知。不是已测物理立面数。
2. scripts/nyc/facades.py、build_facade_areas.py：只读原库和共享坐标，按area重建，不补高度或套地块用途。
3. data/manifests/stage6/sources.json及23原载荷/receipt；acquire_facade_sources使用原请求URL、保留跳转最终URL，raw不可覆盖。
4. config/grove-facade-controls.json、process_facade_images.py（系统Pillow11.1.0/numpy2.2.4）、build_facade_street.py：4独立1936面、遮罩/控制点/UV。照片顺序10、8、6、4，图纸仅4号，不复制给邻楼。
5. reports/stage6的逐面CSV、补齐队列、冲突、44规则、8新浏览器、8基础回归与5机位；当前外观核验0，完整街段0。历史照片面不是已校准PBR或完整建筑。

先补Grove当前可定年四向资料、墙线/地基/屋顶/入口台阶/门廊/栏杆/檐口尺度，解决约0.8–1.2m共同平面宽度偏差，必要时逐栋相机标定；不能拉伸或生成补图掩盖。默认证据模式只显示已知；历史参考可完全移除且不隐藏原轮廓。先验收一个完整街段，再扩至其余11范围，不能用4张照片面称整街完成。

README有重建/验证/打包命令；重建Grove AOI后再执行街段关联步骤。每个新增素材分别核实下载/改造/离线分发权利，HABS条款不自动覆盖图录外部转载。继续当前阶段6，不自动进入下一阶段。

## 历史：阶段5接续

固定/workspace/nyc-3d-html；先读AGENTS、全部docs、reports/LANDMARK_REVIEW.md和reports/stage5/quality.json。当前基于68adbd4继续；Tinnis独立且未改动。云环境可访问，不需重启。

直接输入：

1. landmarks/queue.json及29栋档案。4栋部分研究，2个部分表示；完整研究/体量/立面/精细验证均0，不从目录数量推断模型完成数。
2. assets/landmarks/manifest.json、逐栋GLB/tileset、data/manifests/stage5/models.json和replacement-map.json。One WTC仅局部主体，432仅结构网格线段，physical_world_replacement_allowed=false。
3. scripts/curate_landmarks.py逐参数来源，nyc/landmark_mesh.py组件/法线/feature ID，build_landmarks.py发布，共享coordinates模块不改。来源不确定度未知，project_review_tolerance_m不是现实精度。
4. data/raw/stage5/research/45份实际原文/照片/PDF本地保留、receipt与sources清单有SHA。原件许可未知者不进Git/运行包；有需要用acquire_landmark_sources.py按已记录真实URL恢复，变化另存版本。
5. reports/stage5的36规则、6新浏览器组、8基础回归、12生成视角、定性资料覆盖及质量报告。截图不是已校准真实照片；校准图和独立实测均0。

优先继续：

- One WTC：解决基座205/200ft、屋顶150/145ft冲突；分清SOM441ft与屋顶以上408ft语义。取得实际基座切角、冠部设备、尖顶直径/环/缆索、入口及可定年四向资料。不能用工程预算阈值冒充来源精度。
- 432 Park：取得机械层准确标高、梁柱截面、塔楼中心/方向独立证据及裙房边界。当前来源实体包括裙房，旁边BIN1035787不是可删除替身；拒绝官网错误地图点。
- ESB已有业主原文，先分清1250ft最高使用层/屋顶语义与1454ft天线最高点；111W57已有SHoP原文但无分段尺寸。随后逐栋推进其余队列，不生成通用楼体贴名称。
- 当前全球地面/垂直参考问题继续独立追踪。局部零高检视不是接地验收，原source-building.json含旧legacy高度不能拿来落位。

重建/验证/打包见README阶段5命令。report_landmarks在真实检查通过后更新验证状态；再次curate/build会回到待检查状态，应重新运行相关验证。小包只含两个部分表示与一个来源邻域，不替代阶段4全市包。继续当前阶段，不自动进入下一阶段。

## 历史：阶段4接续

固定/workspace/nyc-3d-html，先读AGENTS和全套docs、reports/BUILDING_QUALITY.md、GEOGRAPHIC_REGISTRATION.md。检查点基于7464214，当前五区来源轮廓发布完成，可信建筑主体因证据缺口仍未完成。

直接输入：

1. scripts/nyc/coordinates.py（含正式GIS批量顶点转换）和src/geo/coordinates.ts：米/ECEF/分瓦片ENU、显式椭球高。不可用未知正高直接落位。
2. data/processed/building-stage4/city/associations.sqlite：1,082,964来源实体、raw引用、部件ID、500m完整对象owner、证据/排除原因、原几何。只读消费，不修改第二阶段库。
3. assets/buildings-city/manifest.json及五区strict/hypothesis.json、GLB、瓦片关联JSON：1,082,930非占位轮廓；默认严格，hypothesis只是明示单位/基底假设且无封盖，不是可信主体。
4. 两个同管线真实样区assets/buildings-pilot-lower、buildings-pilot-midtown，可直接用作快速验证。buildings.html为同工程检视页，index/terrain原入口保留。
5. data/manifests/stage4的来源/表示政策/生成文件SHA，reports/stage4的219对象审计、height-gaps、overlaps、重建与浏览器证据。

优先补足：HEIGHT_ROOF的foot种类；俯视轮廓与墙基线/悬挑关系；单楼基底及垂直基准；原DEM generic NAD83与NAD83(2011)冲突；按年代核对的旧模型GUID↔当前实体关系；真正取得并过滤的屋顶点云与部件高度。未有证据不生成默认高度、统一平屋顶或虚构细节。PLUTO工业地块/最高楼层不传播给每栋楼。未知区域不随机补齐。

抽查有真实内洞与高低源数值，复杂屋顶可靠证据0、真实工业用途独立确认0、现实实测控制0。纯计算误差不能替代现实准确度。所有当前可信主体/屋顶/立面比例0的缺口继续保留。

重建与验收命令见README。大库/全市瓦片/ZIP本地保留，Git只跟踪源码、样本和清单；克隆不等于已取得所有大文件。当前不自动进入下一阶段。

## 历史：阶段3接续

# 下一阶段接续入口（阶段3结束，阶段4未自动启动）

继续固定工程/workspace/nyc-3d-html。首先读取AGENTS、PROJECT_BRIEF、ARCHITECTURE、COORDINATES、DATA_DICTIONARY、ACCURACY、PROGRESS、KNOWN_GAPS和reports/GEOGRAPHIC_REGISTRATION.md；不要重建无关联演示。

当前直接输入：

1. `scripts/nyc/coordinates.py`、`src/geo/coordinates.ts`：共用米制/ECEF/ENU、轴约定和严格WGS84椭球高入口。新建筑/道路/地标一律使用，不手写经纬度乘常数。
2. `scripts/nyc/elevations.py`与`data/processed/foundation/{height-policy,building-elevations}.json`：全市旧高度列仅legacy，新的canonical值因foot/基准未解为空。不要直接拿city SQLite height_m/ground_m落位。
3. `data/manifests/stage3/dem-samples.json`、原始TIFF/LERC及`data/intermediate/stage3/dem`：257²真实裁剪的LERC掩膜与实际地理参考。不能跳过掩膜，原TIFF零值会把NoData伪装为地面。
4. `assets/foundation/*.json`：6样区24个局部正高地形块、完整局部矩阵、真实水系、采样和诊断层；地形world_placement_allowed=false，NAVD88不能直接当椭球高。
5. `data/raw/stage3/geoid/us_noaa_g2012bu0.tif`与geoid.json：匹配NAD83(2011)的GEOID12B，严格转换模块已验证；源服务/索引参考框架冲突仍须解决。
6. `data/processed/foundation/checkpoints.csv`及reports/stage3/registration.json：五区30个来源对应点，实测控制点0。源ID/页/顶点可回查，不当作现场控制网。
7. 第二阶段全市SQLite、GeoPackage、PLUTO、历史3dm保持原样；旧接续详情在本文件历史段。水系内洞证据在shoreline-hole-proof.json。

后续优先：取得/核实原生DEM的实际参考框架、观测历元和提供方说明，解决service2263与index6539冲突；找到独立控制证据后再审核世界垂直操作。未解决时继续正高检视，不以固定偏移、移模型或补零地面掩盖。桥面高程不足保留空，坡地基础应独立处理，不拉主体。模型复用先解决Feet/US survey foot和历史GUID身份映射。

持续验证：npm test、npm run build、node tests/foundation-browser.mjs；新高程/模型数据必须补独立来源/现实误差和真实配准后的近景/全城检查。当前23规则、8阶段3浏览器组、单文件内容离线检查均有记录，但不等于全球真实地形已验收。每阶段继续更新同一套文档。

## 阶段2留下的历史接续说明

固定工程`/workspace/nyc-3d-html`。首先读AGENTS、PROJECT_BRIEF、ARCHITECTURE、COORDINATES、DATA_DICTIONARY、ACCURACY、PROGRESS、KNOWN_GAPS和`reports/VALIDATION.md`，保留现有修改，不另起演示。

可直接消费：

1. `data/processed/city/buildings.sqlite`：五区1,082,964条规范记录、版本化ID/证据/原始引用、米制与WGS84几何、RTree。用README的query_city命令输出有限AOI；不把4.7GiB库整体发给浏览器。
2. `data/processed/lower-manhattan`与`midtown`：真实试验区299/812条；其他四样区合计1,916条。`assets`含局部GLB/3D Tiles与可拾取源ID，它们是轮廓线，不是墙体/屋顶。
3. `data/processed/context/context.gpkg`：边界/道路面/水系米制数据，可裁剪到样区；尚未渲染。
4. `data/intermediate/extracted/nyc_pluto_26v2_csv/pluto_26v2.csv`及原ZIP/字典：全市地块属性；`pluto-pilot-links.json`、`field-conflicts.json`为关系/冲突输入，不默认传播给每栋楼。
5. `data/intermediate/extracted/nyc_3dmodel_mn01/`：历史3dm。先读`reports/official-model-audit.json`核对单位/图层/Brep/曲线与重复表示，解决foot/垂直基准，建立历史GUID→当前建筑的带日期匹配证据，再决定可复用部分；当前匹配0。
6. `data/manifests/{sources.json,files.jsonl,coverage.json,field-priorities.json}`、各city manifest和receipt：抓取证据。扩区/补抓使用原下载器，不覆盖raw。

建议先做两个AOI的控制点、投影/垂直基准和历史建筑匹配，再做有证据的体量/LOD。屋顶/立面无资料继续标未知；如采用推导体量，独立标derived，不能说完整复刻。优先解决LiDAR可取得瓦片入口、影像许可、模型单位差异。

接续验证保持Python规则和六样区真实浏览器检查；新增体量再验证米制尺寸、朝向、局部精度、年代和瓦片边界。真实GPU、多浏览器和普通file://双击尚未验证。每次数据变更更新质量、冲突/失败清单及本文件。
