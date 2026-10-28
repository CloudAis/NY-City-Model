# 第三方资源与许可记录

阶段6使用Library of Congress / Prints & Photographs Division的HABS NY-449（ny0381）原创政府摄影和测绘图。街段照片119530p、入口细节119531p/119532p由Arnold Moses于1936-08-25拍摄；Four Grove Street测绘图署Harry Davis Riley/WPA/HABS，具体绘制日未独立确认。LOC实际权利表说明原创政府摄影/测绘图为公有领域，外部转载材料另查；本次未使用第三方转载图。原件/receipt、实际权利CSV、逐文件SHA与加工记录在data/raw/stage6和data/manifests/stage6，运行时四张灰度历史片段保留年代、遮罩和来源，不能当2026现状或PBR反照率。

阶段6调查的两张Sylvan Terrace照片来自Carol M.Highsmith Archive，LOC条款明确其照片为公有领域；署名Library of Congress, Prints & Photographs Division, photograph by Carol M.Highsmith，原图编号highsm.14220和highsm.14082，日期范围1980–2006，未作为当前街段纹理。旧权利页跳转到通用指南，实际从指南所链CSV核实对应条款，不能仅以“可浏览”推定许可。Pillow11.1.0/numpy2.2.4只作本地处理工具，未把其安装环境分发为浏览器资源。

浏览器库CesiumJS 1.146.0为Apache-2.0；自身与第三方资源许可随构建放在`dist/licenses`，详细名单来自已安装官方包的ThirdParty.json。Vite、TypeScript、Playwright是构建/验证工具，版本在package-lock；Python处理依赖由requirements-lock锁定，未把安装环境打进浏览器包。

NYC轮廓、边界、道路、水系适用NYC Open Data条款；DCP的PLUTO和历史模型适用发布页BYTES说明与免责。捕获的条款、URL、实际版本、下载时间和SHA保留在data/manifests及data/raw/catalog。这不是将“公开可访问”解释为公共领域或添加新许可；后续分发须保留来源及相应条款。

影像item列NYC.gov Terms，元数据另列CC BY4.0，尚需协调；单瓦片只本地参考，未进assets/dist。LiDAR只有元数据，点云包许可/基准待核。OSM仅版权页，未用几何；未来使用须处理ODbL归属与派生数据库义务。

未抓取或打包商业街景、实景瓦片、未知照片或室内。来源明确与独立验证分别记录；年代和精度限制见docs/ACCURACY.md。

阶段3新增数据来自NYS官方公开高程服务的NYC 2017裸地/水底产品，服务署名NYS ITS Geospatial Services；官方NYC元数据列Public及Use Limitations NA。未将其推定为公共领域；实际URL、原始说明和下载/SHA在data/manifests/stage3。GEOID12B由PROJ登记链接取得，open_license标志及参考框架保留。Esri LERC解码器2.0.0为已有锁定依赖、Apache-2.0，使用它保留NoData掩膜；构建继续携带Cesium第三方许可。地形和水系年代、抽稀及配准限制随交付保留。
