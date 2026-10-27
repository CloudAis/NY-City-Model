# 阶段1/2实际验证记录

当前阶段3以[地理配准报告](GEOGRAPHIC_REGISTRATION.md)和`reports/stage3`为准，下文保留阶段1/2历史。阶段3实际23项规则、8组浏览器、构建与单文件内容离线通过；30来源对应点不是实测控制网。LERC掩膜修复真实NoData，全球垂直配准仍阻塞，不能把近景/全城参考线稳定写成真实地形接地验收。

工作日期2026-10-27；时间戳以机器UTC报告为准。工程/workspace/nyc-3d-html，原Tinnis工作区保持干净。此记录不能解释成全纽约完整外观已验收。

|实际命令/动作|观察结果|证据|
|---|---|---|
|`npm run dev`|5180实际启动、HTTP200；本地Cesium/数据资源|dev-server.log|
|`npm run build`|TS检查、Vite构建成功，资源/许可复制到dist；JS约4.18MB，保留大chunk提示|stage2-build.log|
|`npm test`|13项通过，约4.6s；包含真实样本/坐标/修复/幂等、占位排除、证据隔离及HTTP检查|stage2-tests.log|
|`npm run test:browser`|4组通过；六样区实际GLB请求、实际源ID拾取、搜索/相机/档案收起、窄屏；0页面错误、无外部请求|stage2-browser.log、browser-report.json、browser-*.png|
|`node tests/single-preview.mjs`|2真实AOI内容完全离线执行，选择/旋转/缩放/切换/窄屏通过；外部请求0；file://企业策略阻止，记录后以setContent执行|stage2-single-browser.log、single-preview-report.json、single-preview.png|
|中城`--stop-after-pages 1`后相同参数恢复|控制中断exit75；完成812条/812唯一ID；首批原始SHA/mtime不变|stage2-interrupted.log、stage2-resumed.log、real-resume.json|
|下载器本地HTTP实际切断响应/续传|后续Range+If-Range请求，完整字节一致；HTML不能存为ZIP，503有限重试|tests/test_download.py、stage2-tests.log|
|全市index_city重跑|前后1,082,964行，语义SHA完全相同，无重复插入；逐raw页SHA核验|city-idempotence.json、city-idempotent-rerun.log|
|本地query_city下城bbox|299建筑ID集合与原始API样本完全一致，使用RTree粗筛+精确相交|city-idempotence.json、city-query.log|
|normalize_context重跑|已发布GeoPackage SHA和mtime均不变|context-idempotence.json|
|官方2024影像单瓦片实际重取|L18/98565/77178，256²，12,586bytes；相同SHA/原始mtime未改变，命令复跑也成功|real-tile-refetch.json、ortho-command-refetch.log|
|全市覆盖核对|服务总量=五分区总量=规范库1,082,964；未分配0；图形隔离失败0|source-city-inventory.json、city-quality.json、data-quality.json|
|官方3dm/PLUTO实际解析|132,223几何对象、1文件；858,284地块。前者不当建筑数，后者不覆写建筑属性|official-model-audit.json、pluto-audit.json、model-audit-rerun.log|

浏览器：Chromium154.0.8037.57，WebGL2，ANGLE/Vulkan SwiftShader Device(Subzero)，软件渲染；桌面1440×1000、窄屏390×844。浏览器测试只允许本地origin；全程资源来自构建包，禁用ion/在线底图/云地形。已人工查看生成截图，确认轮廓可见；准确性依据原始数据/代码/单位和ID核验，不只凭截图判断。

空间数值测试用真实轮廓顶点，偏离ENU原点215/315米，GLB→ECEF复原<1mm；这只是数值变换误差，不是数据实测精度。全市6项修复最大面积变化约1.46e-11m²，原始记录未覆盖。1异常高度2130353ft保留raw且规范高度null，34占位排除实景，32负地面高程保留。

真实API不是原子快照：建筑抓取两端ID集/编辑标记未变，矢量计数/唯一行ID/结束更新时间一致，但仍保留时间一致性限制。未独立验证任何楼的现场位置/高度，未取得任何LiDAR点云，未验证硬件GPU、多浏览器、真正触屏多指或正常file://双击。没有把这些项目写成通过。

历史失败保留：长GET404已用POST完成等价查询；道路source_id非唯一后改按行ID全量重取；初版根geometricError=0导致空场景已修复并重测。LiDAR权限/预算、规格文档旧链接404等在failure-summary保留状态；下载失败与几何失败分开计数。
