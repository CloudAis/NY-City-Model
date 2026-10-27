# 当前阶段5接续（仍未完成精细地标目标）

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
