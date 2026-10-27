# 阶段实况

## 阶段1 · 已完成

2026-10-27（Asia/Singapore）。/workspace没有生效根AGENTS；Tinnis内AGENTS仅约束旧项目，旧工作区干净，保留。新工程固定/workspace/nyc-3d-html。已审计220个既有文件，没有旧曼哈顿/GIS资料；未发现用户上传的其他资料，细目reports/asset-audit.json。

Node24.19/npm11.9、Python3.12.14、系统GDAL与Chromium可用；起始没有Python GIS库，已实际安装固定pyproj3.8.0/Shapely2.2.0，依赖完整锁定。Cesium1.146.0、Vite8.3.5、TS7.0.2已核对注册表及官方文档并安装；尚未把安装当浏览器验证通过。

官方轮廓元数据与FeatureServer已保存；服务CRS3857、HEIGHT_ROOF为相对高度feet/0未知已核对。下城官方原始样本实际取得299条（3批100/100/99），计数、唯一ID集与抓取两端核对一致；规范化299来源实体/299几何部件、297有效高度数值、2未知高度、0独立核验高度、0占位、0解析失败。标准化脚本重跑字节一致，原始SHA不变。

实际验证：`npm test` 5/5通过（真实样本数/地理范围、单位/空值、内洞/自交/多部件、幂等与GLB坐标轴/局部精度），`npm run build`通过；真实Chromium154/SwiftShader 1440×1000和390×844浏览器4组通过，实际GLB请求和来源ID拾取已验证，没有外部网络请求或页面错误。首轮只请求tileset不请求GLB，修复空根geometricError后重测通过，失败截图/日志保留。已实际查看主场景与单文件轮廓截图。

`reports/nyc-real-sample-preview.html`为真实下城单文件WebGL2轮廓预览，无建筑实体补全。企业策略阻止file://导航（ERR_BLOCKED_BY_ADMINISTRATOR），没有绕过；改在同一浏览器以完整HTML内容setContent完全断网执行，交互、元数据、旋转缩放、窄屏通过。不能把此结果写成已通过本机双击file://验收。

开发服务`npm run dev`已实际启动5180，HTTP200；旧Tinnis工作区仍干净。证据：reports/stage1-{fetch,normalize,publish,tests,build,browser,single-browser}.log、browser-report.json、single-preview-report.json及PNG。原始/字段/source清单在data/manifests与data/raw。

阶段2前置发现已缓存官方动态CMS、MN01 .3dm压缩包、PLUTO 26v2 CSV与字典；仅下载不代表解析或核验完成。下一步沿同一工程规范化中城与五区样本，完善恢复/补抓和数据报告，不自动展开阶段3。
