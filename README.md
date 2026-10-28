# 纽约真实尺度 3D HTML

## GitHub下载与运行

**部分完成版：完整现状精细建筑0；已发布五区来源轮廓与检查工具。**

- [下载全部运行分包、单文件预览与源码](https://github.com/CloudAis/NY-City-Model/releases/tag/v0.1.0-evidence-20261028)（六个运行ZIP约1.45GB，解压约6.2GiB）。
- [逐文件下载和SHA256清单](reports/final-delivery/FILES.md)。
- [最终验收](reports/FINAL_ACCEPTANCE.md)、[真实性与覆盖](reports/AUTHENTICITY_FINAL.md)、[已知缺口](docs/KNOWN_GAPS.md)。

直接运行不需要Node、GIS库、云服务或外网；需要Python3标准库与支持WebGL2的浏览器。从Release把六个运行ZIP、delivery-manifest.json、assemble.py、start-local.py、update-local.py下载到同一目录，然后：

```bash
python3 assemble.py --parts-dir . --output nyc-local
python3 nyc-local/start-local.py
# http://127.0.0.1:8080/
```

也可用GitHub CLI下载至一个新目录：

```bash
gh release download v0.1.0-evidence-20261028 --repo CloudAis/NY-City-Model --dir nyc-release
python3 nyc-release/assemble.py --parts-dir nyc-release --output nyc-local
python3 nyc-local/start-local.py
```

Git仓库保存源码、锁文件、配置、样本、来源清单及验证记录；全市大资源随Release实际提供。**仅克隆仓库不包含被Git忽略的全量数据。** 要重新构建当前完整页面，组装Release后把`nyc-local/app/datasets/`的内容复制到源码`assets/`，再按[重建说明](docs/REBUILD.md)安装开发依赖和构建。多GiB原始GIS/主库/历史研究原件没有全部上传，来源再处理需要相应原始输入。

单文件preview-single.html仅四块1936历史正面及部分WTC体量；HTTP/离线嵌入通过，默认file导航受测试环境企业策略限制。它不是全纽约完整版。独立实测现实精度未知；源转换忠实度检查不代替现实测绘。

---

**当前为第十阶段部分完成交付，以下旧阶段说明作为历史保留。** 全部已发布五区轮廓、检查工具及局部证据可本地离线运行；完整现状精细建筑0，不是完整纽约外观复刻。

交付目录为`reports/final-delivery/`，包含**六个实际运行分包**、`delivery-manifest.json`、`SHA256SUMS`、Python组装/启动/更新脚本、单文件局部预览和开发源码ZIP。无需任何旧基础包。具体清单、限制与操作见[交付说明](docs/DELIVERY.md)，真实性见[最终真实性报告](reports/AUTHENTICITY_FINAL.md)，实际验收见[最终验收报告](reports/FINAL_ACCEPTANCE.md)。

```bash
cd reports/final-delivery
python3 assemble.py --parts-dir . --output ./nyc-local
python3 nyc-local/start-local.py --port 8080
# http://127.0.0.1:8080/index.html
```

源码已具备依赖时：`npm run dev` → **http://127.0.0.1:5180/release.html**。构建：`npm run build`，随后`python3 -m http.server 8080 --bind 127.0.0.1 --directory dist`，打开`/release.html`。开发dist保留原index为来源档案；最终运行包的index为覆盖说明入口，原档案另存source-audit.html。

新单文件为根目录`preview-single.html`：Grove四块1936历史正面片段和OneWTC部分文献体量，无外部依赖，不是完整现状街段。HTTP与内容嵌入实测可用，默认file://被本机企业策略拦截，普通浏览器双击待测。运行包离线HTTP不等于支持多文件file://。源数据/年代、重建输入与更新回退见[重建](docs/REBUILD.md)、[更新](docs/UPDATE.md)。

---

阶段6新增 [普通建筑逐面检视](facades.html)：五区12个明确边界、918个来源对象、10,667条立面候选边；实际处理Grove四栋各自的1936年正面照片，独立校正、遮罩和UV。**完整现状街段与已核验现状立面仍为0**，门廊、栏杆和屋顶实体未完成。见 [普通建筑报告](reports/FACADE_REVIEW.md) 和 [接续](docs/NEXT_STEPS.md)。

启动 `npm run dev` → **http://localhost:5180/facades.html**。默认严格证据只显示已知轮廓；明确打开“1936年历史立面片段”才加载四个照片面，可完全移除。当前来源轮廓不隐藏，不以历史资料替代2026现状。其他范围没有铺随机或重复纹理。固定路径、逐面状态和原图预览均可查看。

局部离线包 `reports/nyc-stage6-facade-studies.zip` 解压后执行 `python3 -m http.server 8000 --bind 127.0.0.1 --directory app`，打开 `http://localhost:8000/facades.html`；不是全市外观完成版。校验和实际解压运行结果在 `reports/stage6/release.json`、`standalone-browser.json`；普通file://未测。原始TIFF留本地并附来源/SHA，许可明确的政府原图可随研究包保留。

阶段6重建顺序：

```bash
.venv/bin/python scripts/acquire_facade_sources.py
.venv/bin/python scripts/build_facade_areas.py
/usr/bin/python3 scripts/process_facade_images.py
.venv/bin/python scripts/build_facade_street.py
.venv/bin/python scripts/link_facade_parcels.py  # 只核对地块语境，不覆盖逐楼外观
npm test
npm run build
node tests/facades-browser.mjs
NYC_REPORT_DIR=reports/stage6/foundation node tests/foundation-browser.mjs
.venv/bin/python scripts/report_facades.py
npm run build
.venv/bin/python scripts/package_facades.py
node tests/facades-standalone.mjs
# 单范围重建；重建Grove后再运行build_facade_street恢复历史关联
.venv/bin/python scripts/build_facade_areas.py --area manhattan-soho
```

当前图像步骤使用系统Pillow11.1.0/numpy2.2.4，GIS沿用.venv。新环境可在独立环境安装这两个固定版本并用该Python运行图像脚本；没有声称GIS虚拟环境已有Pillow。配置、原始图路径/URL/许可/日期/SHA、各面状态和补齐队列在 `config/`、`data/manifests/stage6/`、`reports/stage6/`。

以下为阶段5及更早检查点，未完成项继续保留。

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

## 当前入口：第7/8部分环境与模型检查

工程固定在/workspace/nyc-3d-html。运行 `npm run dev` 后打开 `http://localhost:5180/inspection.html`；已有index/terrain/buildings/landmarks/facades入口保留。`npm run build` 生成dist；离线以本机HTTP服务启动（不是file://），无需ion/云地形/底图凭据。

25预设覆盖五区；查询支持来源名称/别名/明确地址、BIN（至少4位）、`id:233256`。点击/悬停原轮廓可查稳定ID，返回选中、Esc取消飞行、俯视/环绕/自由飞行、八区受限NAVD88检查。WASD/QE移动，Shift慢速；鼠标拖动旋转/右键平移/滚轮缩放，触点双指缩放与平移。地面只允许已知DEM三角形，桥面/道路/水面/地下/室内禁止。

量测区分全球水平测地距离与局部NAVD88空间/高差；缺高程不报零。书签保存在本地浏览器，可导入导出；截图带来源署名。光照固定中性，不支持太阳日期/夜景。所有道路/桥梁全球图层是明确标记的参考投影，不能当物理接地表面。

重建（先保留原数据，网络仅下载步骤使用）：

```bash
.venv/bin/python scripts/acquire_environment.py
.venv/bin/python scripts/research_bridges.py
.venv/bin/python scripts/build_environment.py --vectors-only
.venv/bin/python scripts/acquire_park_terrain.py
.venv/bin/python scripts/build_environment.py
.venv/bin/python scripts/build_city_search.py
.venv/bin/python scripts/report_environment.py
npm test
node tests/inspection-core.mjs
npm run build
node tests/inspection-browser.mjs
NYC_REPORT_DIR=reports/stage8/foundation node tests/foundation-browser.mjs
NYC_REPORT_DIR=reports/stage8/landmarks node tests/landmarks-browser.mjs
NYC_REPORT_DIR=reports/stage8/facades node tests/facades-browser.mjs
```

先用--vectors-only发布公园边界，获取两个公园DEM后完整构建纳入八区；还需要现有六区foundation。若只有源码克隆，必须按旧阶段说明恢复city库/context/全市瓦片，不能以空数据冒充全市。来源清单data/manifests/stage7/sources.json，环境/交互报告reports/ENVIRONMENT_REVIEW.md与INTERACTION_REVIEW.md，未解决物理高程/桥梁项详见docs/KNOWN_GAPS.md。

离线增量打包：`.venv/bin/python scripts/package_inspection.py`。`reports/nyc-stage78-inspection-overlay.zip`不含旧5.3GiB全市瓦片；覆盖旧stage4包的app，保留`app/datasets/buildings-city`，或从当前dist复制该目录。进入app用`python3 -m http.server 8080 --bind 127.0.0.1`，打开`http://127.0.0.1:8080/inspection.html`。包内START_HERE与OVERLAY_MANIFEST明确基底SHA和范围。

对实际增量包复验：`node tests/inspection-package.mjs`（需本机HTTP监听和Chromium）。结果在reports/stage8/package-browser.json；它使用同卷临时解压并接回既有全市数据，清楚记录基底依赖。最终ZIP校验和在同名.sha256，包外复验记录不参与ZIP自包含。

## 性能与稳定性检查点

当前同一入口inspection.html；运行`npm run dev`，浏览http://localhost:5180/inspection.html。三档画质与缓存/自动策略见docs/QUALITY.md。主数据和原GLB/精细表示完整保留，assets/performance只增加引用目录。

```bash
.venv/bin/python scripts/build_streaming_catalog.py
npm test
node tests/performance/rules.mjs
npm run build
node tests/performance/faults.mjs
NYC_REPORT_DIR=reports/stage9/inspection NYC_OBSERVATION_REPORT=reports/stage9/observations.json node tests/inspection-browser.mjs
NYC_PERF_LABEL=optimized-final NYC_PERF_ROOT=dist node tests/performance/benchmark.mjs
node tests/performance/soak.mjs
node tests/performance/visual.mjs
.venv/bin/python scripts/check_performance_integrity.py
.venv/bin/python scripts/report_performance.py
.venv/bin/python scripts/package_performance.py
NYC_REPORT_DIR=reports/stage9 node tests/inspection-package.mjs
```

benchmark基线需保留data/intermediate/stage9/baseline（本轮af311b2编译快照，静态数据指向未改assets）；配对测试按顺序、同视口/条件执行，不与其他浏览器测试并行。soak默认1800现实秒，禁止用加速模拟替代；短NYC_SOAK_SECONDS只作预检，不记30分钟通过。每轮GC前后均记，GC和后台测试负载如实列出。

源码Git不带多GiB主库/原五区瓦片，恢复方式仍按前期说明。性能增量包reports/nyc-stage9-performance-overlay.zip需保留既有app/datasets/buildings-city；它包含新代码、完整查询/环境/原精细检查资源和来源/验证记录，没有删改原基底。ZIP校验与解压运行结果在包外stage9/package*.json。

性能对照和仍有回退的路线见reports/PERFORMANCE_REVIEW.md，真实时长/内存/故障见STABILITY_REVIEW.md。软件WebGL结果不能外推硬件GPU/真机；本轮未解决的全城高程、完整可信建筑主体等前期缺口继续保留。
