# 纽约真实尺度 3D HTML

当前阶段5检查点新增 [地标检视入口](landmarks.html)：29栋独立档案、4栋部分研究、2个部分表示（One WTC主体与432 Park结构网格片段），**完整精细地标完成数0**。不是29栋精细模型交付；当前阶段仍有未完成项，详见 [地标研究与验证报告](reports/LANDMARK_REVIEW.md)、[接续](docs/NEXT_STEPS.md)。

启动 `npm run dev` → **http://localhost:5180/landmarks.html**。固定中性光，支持四向/高处/街道视角、组件拾取、文献和逐参数证据入口。只作局部零高参考检视，全球地面基准未解决。One WTC可精确隐藏/恢复对应来源轮廓，19个邻楼保留；432因来源包括裙房且塔楼位置未确认而禁用替换。

小型离线包 `reports/nyc-stage5-landmark-studies.zip` 包含两个部分表示、一个来源邻域、源码和研究/验证记录；解压后 `python3 -m http.server 8000 --bind 127.0.0.1 --directory app`，打开 `http://localhost:8000/landmarks.html`。它不含全市数据或原始研究照片/PDF，不是全纽约完成版。包校验与实际运行结果见 `reports/stage5/release.json`、`standalone-browser.json`；源码重建需要下列本地研究与GIS输入。

阶段5命令（顺序有依赖；只下载已发现并记录的真实URL）：

```bash
.venv/bin/python scripts/init_landmark_dossiers.py  # 只补缺失档案
.venv/bin/python scripts/acquire_landmark_sources.py  # 原始缓存校验；--refresh另存变化版本
.venv/bin/python scripts/curate_landmarks.py
.venv/bin/python scripts/build_landmarks.py
npm test
npm run build
node tests/landmarks-browser.mjs
NYC_REPORT_DIR=reports/stage5/foundation node tests/foundation-browser.mjs
.venv/bin/python scripts/report_landmarks.py  # 读取真实通过记录，更新部分验证状态
npm run build
.venv/bin/python scripts/package_landmarks.py
node tests/landmarks-standalone.mjs
```

`landmarks/`保存29栋研究队列；`data/manifests/stage5/`保存实际资源SHA、模型与替换映射。私有/许可未知的原HTML、PDF、照片只留本地 `data/raw/stage5/research/`，Git跟踪receipt和事实参数。未取得的四向资料、机械层标高、真实基底等留空，研究目录数不作为完成数。

以下为阶段4及更早记录；其全市来源覆盖和地面基准缺口仍保留。

当前阶段4已发布五区 **1,082,930 条非占位来源轮廓**（输入1,082,964条，排除34占位）。新增 `buildings.html`，复用已验证坐标模块和同一套样区/全市管线，输出 GLB、3D Tiles、部件关联与处理原因。

**可信建筑主体、可靠屋顶、精细立面目前均为0。** 官方轮廓为俯视外边界，HEIGHT_ROOF 的英尺种类、墙基线、地面基准及屋顶部件尚未解决。默认严格模式只显示真实轮廓；可选的来源高度假设包络明确标记、默认关闭、不封未知屋顶，不计入可信主体。详见 [建筑质量报告](reports/BUILDING_QUALITY.md)。

启动：`npm run dev` → **http://localhost:5180/buildings.html**。选择下城/中城或五区，再选择行政区。现有 `index.html` 测绘档案和 `terrain.html` 正高检视保留。全城俯视主动暂停完整细节瓦片，放大或点击定位后加载；没有用低细节方盒代替真实建筑。

完整本地离线交付为 `reports/nyc-stage4-buildings.zip`，包含运行资源、模块源码、关联SQLite和质量/来源记录；解压后运行 `python3 -m http.server 8000 --bind 127.0.0.1 --directory app`，打开 `/buildings.html`。此包不含全部原始GIS大文件，完整raw审计/重建仍需工作区原资料。大库/全市派生资源与ZIP不进Git，清单和两个真实样区随源码保存。

以下为阶段3已交付基础的历史说明，当前建筑状态以上述阶段4及质量报告为准。

当前交付至**阶段3：坐标、高程与真实地形基础**。沿用第二阶段全市数据；新增六样区2017 DEM、24个局部地形块、真实水系展示与可关闭的检查层。30个来源对应检查点不等于实测控制点（后者0个）。全球垂直配准仍受NAD83实现冲突阻塞，地形目前在独立NAVD88正高检视中使用，不给全城加固定偏移。

启动后，主页面进入ECEF参考视图；点击“打开真实DEM”或访问`http://localhost:5180/terrain.html`查看真实地形。正式入口和数据缺口详见[地理配准报告](reports/GEOGRAPHIC_REGISTRATION.md)、[坐标模块](scripts/nyc/coordinates.py)、[检查点CSV](data/processed/foundation/checkpoints.csv)、[阶段3来源](data/manifests/stage3/sources.json)。

阶段3构建包为`reports/nyc-stage3-foundation.zip`；旧`nyc-stage2-browser.zip`保留作历史检查点，不代表当前地形状态。建筑高度旧米字段保留legacy，新canonical字段因foot种类未解决而为null。不能直接把city SQLite的旧height_m/ground_m用作世界落位。

固定工程 `/workspace/nyc-3d-html`。阶段1、2已实现；**不是全纽约外观复刻完成版**。本地取得五区来源轮廓1,082,964条，含34条占位。浏览器发布六个真实样区3,026条非占位轮廓（来源记录3,027条）；单文件预览只含下城/中城1,110条非占位轮廓。没有生成默认楼高、盒楼、屋顶、立面或室内。

## 启动

本环境依赖已安装：

```bash
cd /workspace/nyc-3d-html
npm run dev
# http://localhost:5180
```

新环境使用Node24、Python3.12，执行 `npm ci`、`python3 -m venv .venv`、`.venv/bin/pip install -r requirements-lock.txt`。GIS处理另需系统GDAL CLI，模型审计使用rhino3dm。构建后的运行不需Python GIS依赖或外网：

```bash
npm run build
python3 -m http.server 8000 --bind 127.0.0.1 --directory dist
# http://localhost:8000
```

`reports/nyc-stage2-browser.zip`为阶段2历史构建包，当前交付见阶段3包。`reports/nyc-real-sample-preview.html`为独立单文件样区预览。当前企业浏览器阻止file://；已在Chromium以完整HTML内容完全离线运行和操作验证，**普通浏览器双击file://仍待验证**。

## 实际保留数据

|输入|路径|状态|
|---|---|---|
|全市证据库|`data/processed/city/buildings.sqlite`|1,082,964行，版本化主键、米制/WGS84几何、RTree；约4.7GiB|
|五区原始轮廓|`data/raw/footprints/2026-10-27-city/`|分批响应和receipt；清单在`data/intermediate/city-*/manifest.json`|
|六个样区|`data/processed/{lower-manhattan,midtown,brooklyn-dumbo,queens-lic,bronx-mott-haven,staten-st-george}/`|3,027条JSONL；assets内GLB轮廓线/3D Tiles|
|边界/道路面/水系|`data/processed/context/context.gpkg`|EPSG:32118米，5/104,961/2,206条；阶段3已接入有限样区参考层，桥面高程未知|
|PLUTO 26v2|`data/raw/supporting/nyc_pluto_26v2_csv.zip`|858,284地块；解压CSV/字典保留；不是楼级高度|
|官方MN01模型|`data/raw/supporting/nyc_3dmodel_mn01.zip`|2014航测；1个3dm已解析，132,223对象不等于建筑数，当前匹配0|
|正射|`data/raw/imagery/2024/18-98565-77178.image`|仅1个真实2024影像瓦片，已补抓；许可待协调，仅参考，未打包|

大体积raw、数据库和缓存本地保留，Git只保存源码、样本与清单；克隆仓库不会自动取得这些大文件。未取得LAS/LAZ、其他区3dm、MapPLUTO地块几何或NYS正射栅格。详见[缺口](docs/KNOWN_GAPS.md)。

## 可重复获取与处理

version是抓取标签，不是发布机构正式版本号。原始资料只追加，改变响应另存，不能用派生结果覆盖raw。

```bash
# 真实小范围；其他样区bbox见各manifest
.venv/bin/python scripts/fetch_footprints.py --bbox -73.989 40.748 -73.977 40.7565 --name midtown --version 2026-10-27-pilot --batch 100 --output data/intermediate/midtown
.venv/bin/python scripts/normalize.py --manifest data/intermediate/midtown/manifest.json --output data/processed/midtown

# 五区分别执行同样流程，示例曼哈顿
.venv/bin/python scripts/fetch_footprints.py --borough manhattan --name city-manhattan --version 2026-10-27-city --batch 500 --interval .5 --max-features 1500000 --output data/intermediate/city-manhattan
.venv/bin/python scripts/index_city.py
.venv/bin/python scripts/spatial_index.py
.venv/bin/python scripts/scan_city_quality.py --version 2026-10-27-city

# 本地库按真实范围精确相交导出；默认数量上限防止加载全市
.venv/bin/python scripts/query_city.py --bbox -74.0165 40.7045 -74.007 40.7115 --borough manhattan --version 2026-10-27-city --output data/processed/query-lower

# 支持资源：实际URL从已保存官方CMS/目录发现
.venv/bin/python scripts/acquire_supporting.py
.venv/bin/python scripts/process_supporting.py all
.venv/bin/python scripts/fetch_support_vectors.py
.venv/bin/python scripts/normalize_context.py
.venv/bin/python scripts/link_evidence.py

# 单瓦片补抓：service URL由官方item读取
.venv/bin/python scripts/fetch_ortho_tile.py --version 2024 --level 18 --row 98565 --column 77178 --refetch
.venv/bin/python scripts/report_sources.py
.venv/bin/python scripts/report_quality.py

# 发布六样区与单文件双样区
.venv/bin/python scripts/publish.py data/processed/lower-manhattan data/processed/midtown data/processed/brooklyn-dumbo data/processed/queens-lic data/processed/bronx-mott-haven data/processed/staten-st-george
.venv/bin/python scripts/single_preview.py data/processed/lower-manhattan data/processed/midtown
```

分页恢复/单批补抓参数见`fetch_footprints.py --help`中的`--stop-after-pages`、`--refetch-page`。真正Range续传仅对ETag/206可核验来源启用。发生动态更新的分区需新版本/目录，不能混用旧快照。

本地GeoJSON导入见`.venv/bin/python scripts/import_local.py --help`：必须明确CRS，无来源资料进入local-pending；填写来源/许可也不会自动获准发布。高度须明确字段、相对/绝对含义与单位。

## 验证与记录

```bash
npm test
npm run build
npm run test:browser
node tests/single-preview.mjs
.venv/bin/python scripts/package_foundation.py
```

实际恢复与幂等证据见`reports/real-resume.json`、`city-idempotence.json`、`context-idempotence.json`、`real-tile-refetch.json`。单元检查含截断HTTP Range恢复、有限重试、内容校验、米制坐标、几何修复、空高度与地块隔离；浏览器检查真实本地GLB加载/源ID拾取、六样区和窄屏，屏蔽所有外网请求。

入口：[资产审计](reports/asset-audit.json)、[来源清单](data/manifests/sources.json)、[逐文件SHA](data/manifests/files.jsonl)、[质量报告](reports/data-quality.json)、[五区CSV](reports/borough-coverage.csv)、[验证记录](reports/VALIDATION.md)、[进度](docs/PROGRESS.md)、[后续接续](docs/NEXT_STEPS.md)、[资源条款](THIRD_PARTY_NOTICES.md)。

## 阶段3可重复处理

```bash
# 复用既有全市库/GeoPackage，补充本阶段必需的真实DEM与GEOID12B
.venv/bin/python scripts/acquire_foundation.py
node scripts/decode_dem.mjs
for name in lower-manhattan midtown brooklyn-dumbo queens-lic bronx-mott-haven staten-st-george; do
  /usr/bin/python3 scripts/gdal_raster.py --file data/raw/stage3/dem/$name.tif --output data/intermediate/stage3/dem/$name
done
.venv/bin/python scripts/build_foundation.py
.venv/bin/python scripts/check_registration.py
.venv/bin/python scripts/check_water_holes.py
.venv/bin/python scripts/audit_coordinates.py
npm test
npm run build
node tests/foundation-browser.mjs
node tests/single-preview.mjs
.venv/bin/python scripts/report_foundation.py
```

NYS TIFF导出缺少有效性掩膜，部分NoData露成0；本管线强制同范围LERC掩膜，不能跳过decode步骤。`/usr/bin/python3`实际可用GDAL绑定，项目venv使用pyproj/Shapely；Esri LERC解码器已由Cesium依赖锁固定，无新增在线运行前提。原始TIFF/LERC/格网与下载receipt分开保留，数据/网页/采集/下载日期不混用。

输出：`assets/foundation`为离线场景；`data/processed/foundation`保存canonical高度注册表、检查点和水系内洞证据；`data/manifests/stage3/file-coordinate-audit.jsonl`按实际内容记录CRS/轴/单位/基准及未知。`reports/stage3`保存实际规则/浏览器、NoData与接缝结果。新单文件仍只是下城/中城轮廓预览，不含全城地形。

## 阶段4：建筑生成与可重复重建

所有命令在工程根目录执行，原始库只读。source version 为保存的抓取标签。output 和 work 是派生目录；不同输入/代码指纹应选新目录，脚本拒绝混用旧缓存。

```bash
# 两个真实样区（已执行）
.venv/bin/python scripts/build_buildings.py --aoi lower-manhattan --work data/processed/building-stage4/lower-manhattan --output assets/buildings-pilot-lower
.venv/bin/python scripts/build_buildings.py --aoi midtown --work data/processed/building-stage4/midtown --output assets/buildings-pilot-midtown

# 五区使用同一管线（已执行）
.venv/bin/python scripts/build_buildings.py --version 2026-10-27-city --work data/processed/building-stage4/city --output assets/buildings-city

# 整个行政区单独重建；支持其他四区名称
.venv/bin/python scripts/build_buildings.py --borough manhattan --work data/processed/building-stage4/rebuild-manhattan --output assets/rebuild-manhattan

# 单一对象（已在隔离输出实际检查），不会覆盖全市发布
.venv/bin/python scripts/build_buildings.py --id nyc:footprints:doitt:105139 --work data/intermediate/stage4-single-work --output data/intermediate/stage4-single-rebuild

# 仅强制重建一个500m owner格，其余文件校验复用
.venv/bin/python scripts/build_buildings.py --work data/processed/building-stage4/city --output assets/buildings-city --force-tile 597 119
# --tile 597 119 可选择这个格输出到新的work/output；--bbox支持经纬度范围。

# 实际审计与检查；完整规则测试含本机HTTP服务，需要环境允许监听本地端口
.venv/bin/python scripts/select_building_review.py
.venv/bin/python scripts/check_missing_heights.py
.venv/bin/python scripts/audit_buildings.py
.venv/bin/python scripts/check_building_rebuild.py
npm test
npm run build
node tests/buildings-browser.mjs
NYC_REPORT_DIR=reports/stage4/foundation node tests/foundation-browser.mjs
```

全市关联表：`data/processed/building-stage4/city/associations.sqlite`。源记录及部件、owner、排除/未知原因在metadata列，原始多边形在geometry列，ID与source_rowid唯一。可见对象与原始记录关联见各瓦片JSON、GLB feature ID；全部生成资源SHA见 `data/manifests/stage4/generated-files.jsonl`。抽查CSV、重叠与缺失高度清单在 `reports/stage4`。

示例只读查询：

```bash
.venv/bin/python - <<'PY'
import sqlite3,json
c=sqlite3.connect('file:data/processed/building-stage4/city/associations.sqlite?mode=ro',uri=True)
row=c.execute('select metadata from objects where id=?',('nyc:footprints:doitt:105139',)).fetchone()
print(json.dumps(json.loads(row[0]),ensure_ascii=False,indent=2))
PY
```

阶段4构建在同一文件系统上对大资源建立普通硬链接以节约第二份磁盘，不支持时复制；ZIP保存独立字节。发布资源原子替换，最终测试后再打包。没有云资源或收费接口启动前提。当前主体验证缺口不因打包或浏览器成功而消失。
