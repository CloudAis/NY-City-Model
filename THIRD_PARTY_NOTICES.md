# 第三方资源与许可记录

浏览器库CesiumJS 1.146.0为Apache-2.0；自身与第三方资源许可随构建放在`dist/licenses`，详细名单来自已安装官方包的ThirdParty.json。Vite、TypeScript、Playwright是构建/验证工具，版本在package-lock；Python处理依赖由requirements-lock锁定，未把安装环境打进浏览器包。

NYC轮廓、边界、道路、水系适用NYC Open Data条款；DCP的PLUTO和历史模型适用发布页BYTES说明与免责。捕获的条款、URL、实际版本、下载时间和SHA保留在data/manifests及data/raw/catalog。这不是将“公开可访问”解释为公共领域或添加新许可；后续分发须保留来源及相应条款。

影像item列NYC.gov Terms，元数据另列CC BY4.0，尚需协调；单瓦片只本地参考，未进assets/dist。LiDAR只有元数据，点云包许可/基准待核。OSM仅版权页，未用几何；未来使用须处理ODbL归属与派生数据库义务。

未抓取或打包商业街景、实景瓦片、未知照片或室内。来源明确与独立验证分别记录；年代和精度限制见docs/ACCURACY.md。

阶段3新增数据来自NYS官方公开高程服务的NYC 2017裸地/水底产品，服务署名NYS ITS Geospatial Services；官方NYC元数据列Public及Use Limitations NA。未将其推定为公共领域；实际URL、原始说明和下载/SHA在data/manifests/stage3。GEOID12B由PROJ登记链接取得，open_license标志及参考框架保留。Esri LERC解码器2.0.0为已有锁定依赖、Apache-2.0，使用它保留NoData掩膜；构建继续携带Cesium第三方许可。地形和水系年代、抽稀及配准限制随交付保留。
