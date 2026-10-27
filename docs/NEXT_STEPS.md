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
