# 第三阶段接续入口（本轮不自动执行）

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
