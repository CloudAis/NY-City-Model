# 阶段实况

## 阶段1 · 已完成

2026-10-27（Asia/Singapore）。/workspace没有生效根AGENTS；Tinnis内AGENTS仅约束旧项目，旧工作区干净，保留。新工程固定/workspace/nyc-3d-html。已审计220个既有文件，没有旧曼哈顿/GIS资料；未发现用户上传的其他资料，细目reports/asset-audit.json。

Node24.19/npm11.9、Python3.12.14、系统GDAL与Chromium可用；起始没有Python GIS库，已实际安装固定pyproj3.8.0/Shapely2.2.0，依赖完整锁定。Cesium1.146.0、Vite8.3.5、TS7.0.2已核对注册表及官方文档并安装；尚未把安装当浏览器验证通过。

官方轮廓元数据与FeatureServer已保存；服务CRS3857、HEIGHT_ROOF为相对高度feet/0未知已核对。下城官方原始样本实际取得299条（3批100/100/99），计数、唯一ID集与抓取两端核对一致；规范化299来源实体/299几何部件、297有效高度数值、2未知高度、0独立核验高度、0占位、0解析失败。标准化脚本重跑字节一致，原始SHA不变。

实际验证：`npm test` 5/5通过（真实样本数/地理范围、单位/空值、内洞/自交/多部件、幂等与GLB坐标轴/局部精度），`npm run build`通过；真实Chromium154/SwiftShader 1440×1000和390×844浏览器4组通过，实际GLB请求和来源ID拾取已验证，没有外部网络请求或页面错误。首轮只请求tileset不请求GLB，修复空根geometricError后重测通过，失败截图/日志保留。已实际查看主场景与单文件轮廓截图。

`reports/nyc-real-sample-preview.html`为真实下城单文件WebGL2轮廓预览，无建筑实体补全。企业策略阻止file://导航（ERR_BLOCKED_BY_ADMINISTRATOR），没有绕过；改在同一浏览器以完整HTML内容setContent完全断网执行，交互、元数据、旋转缩放、窄屏通过。不能把此结果写成已通过本机双击file://验收。

开发服务`npm run dev`已实际启动5180，HTTP200；旧Tinnis工作区仍干净。证据：reports/stage1-{fetch,normalize,publish,tests,build,browser,single-browser}.log、browser-report.json、single-preview-report.json及PNG。原始/字段/source清单在data/manifests与data/raw。

阶段2前置发现已缓存官方动态CMS、MN01 .3dm压缩包、PLUTO 26v2 CSV与字典；仅下载不代表解析或核验完成。下一步沿同一工程规范化中城与五区样本，完善恢复/补抓和数据报告，不自动展开阶段3。

## 阶段2 · 数据底座与样区交付

2026-10-27，实际抓取/验证时间使用UTC写入各receipt/report。沿用阶段1检查点cd95d28，同一工程继续；未修改Tinnis。没有自动展开阶段3。时间依据机器记录，不虚报人工工时。

实际取得并规范化来源建筑记录1,082,964条，与服务全市计数、五个BASE_BBL分区及本地库总数一致，未分配源记录0。这里的实体为DOITT来源实体，未独立确认物理建筑一对一关系，分区也未逐楼做边界复核。

|分区|来源记录/规范记录|有效来源相对高度|未知高度|占位|修复|已匹配当前3D模型|
|---|---:|---:|---:|---:|---:|---:|
|曼哈顿|45,172|45,097|75|5|4|0|
|布朗克斯|104,268|104,082|186|4|0|0|
|布鲁克林|330,113|329,899|214|4|0|0|
|皇后区|460,950|460,793|157|14|1|0|
|史泰登岛|142,461|142,372|89|7|1|0|

全量解析隔离失败0，保留32条负地面高程。721未知高度中含1个源异常值2130353ft，未生成默认值；34占位不作为实景。6项几何修复记录原始引用与面积变化（最大约1.46e-11m²，仍不代表现场精度）。位置/高度独立核验0，屋顶/立面未知。库data/processed/city/buildings.sqlite约4.7GiB，事务分页恢复、版本主键、非唯一BIN/BBL索引与米制RTree可用。

六样区来源记录3,027，发布非占位轮廓3,026；下城299、中城812来源/811发布。单文件只含下城/中城1,110条。GLB保持真实位置、轮廓、朝向/平面尺寸，在明确参考面上显示线，不补墙/屋顶。来源档案支持六维证据、原始路径/SHA、来源与下载年代入口。

补充输入：PLUTO 26v2全市858,284地块解析，匹配2,651样区地块，0楼级字段覆盖；265项scope问题分221个非空年份差异、44个缺失楼级年份不能由地块填充，脚本可重建。MN01官方ZIP/3dm实际解析132,223几何对象（59,996 Brep等）；2014航测、DCP2018包，0当前建筑匹配。Feet/US survey foot冲突、重复图层/表示未擅自消除。不能以对象数报告建筑数。

边界5、道路面104,961、水系2,206已全量获取并投影为32118米GeoPackage。旧道路source_id出现重复/零，原唯一性结论被校验拦下；改用Socrata行ID重取，旧raw保留。抓取结束fresh计数与rowsUpdatedAt一致，仍不是事务快照。初始长ArcGIS GET返回404，改POST等价参数查询后完成全量，历史失败保留。

2024正射真实1瓦片已获取并补抓，原SHA/mtime不变，仅参考不进构建。NYS LiDAR目录和NYC地图应用403，批量包超过64MiB探测预算、HEAD超时；0点云文件。NYS正射只调查门户、MapPLUTO只元数据、其他3dm包未取得。详见KNOWN_GAPS，不将目录读取写成下载成功。

实际验证：13项Python检查通过；最终TypeScript/Vite构建通过（Cesium大chunk提示保留）；Chromium154、实际WebGL2/SwiftShader、1440×1000/390×844，4组操作通过，六样区逐个实际请求GLB，来源ID拾取、档案、搜索/镜头/收起、窄屏通过，无外部请求/页面错误。已查看下城/中城/拾取及单文件截图。主视口选中后档案自动滚入可见区域。

实际恢复/幂等：中城第1批后控制退出75再恢复，812唯一ID且首批raw SHA/mtime保持；HTTP本地服务实际截断后Range恢复；全市重跑记录数/语义SHA不变；本地bbox精确查询299 ID与原API一致；上下文重跑SHA/mtime不变；实际影像单瓦片补抓。单文件两个AOI完全离线内容执行/交互通过，file://仍被企业策略阻止，正常浏览器双击待测。

证据：reports/VALIDATION.md、data-quality.json、borough-coverage.csv、city-record-issues.json、real-resume.json、city-idempotence.json、context-idempotence.json、real-tile-refetch.json、stage2-*.log、browser-report.json、single-preview-report.json。逐raw SHA/时间/版本/许可/坐标/处理器清单在data/manifests；大数据本地保留、Git忽略策略明确，浏览器包只携带有限真实样区。第三阶段输入和未完成项已写NEXT_STEPS。
