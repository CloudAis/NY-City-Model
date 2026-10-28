# 最终验收报告 · 部分完成

当前工程交付全部已发布五区资源及检查工具；**未达到五区全部可信主体、屋顶与逐立面复刻目标**，不能宣布全项目现实真实性验收通过。实体分母、版本、排除与未知见[真实性报告](AUTHENTICITY_FINAL.md)。完整精细当前建筑0，独立实测现实误差未知。

## 实际运行证据

本轮类型检查与Vite构建通过，57项规则测试通过；实际浏览器：坐标/地形8组、地标6组及12生成视角、立面8组/12AOI、检查器12组/25观察点、故障11组、单文件6组。浏览器截图只辅助实际操作与日志，不代替资料/几何/状态检查。首次普通沙箱测试因本地TCP权限失败，保留失败日志，在允许127.0.0.1监听后重跑通过，没有隐藏失败。

真实连续浏览：1805.459秒，完成30分钟条件：True；周期33，请求2759，失败请求40。冻结候选资产指纹见stage10/soak/result.json。测试时HEAD为来源基线，工作区包含本轮代码，实际bundle指纹才是运行候选证据。早期同时运行其他回归/重建，不冒称严格独占性能对照。

连续harness的requestfailed计数包含取消但没有保留errorText，故不称零网络失败；最终包新缓存记录260请求、0失败，HTTP全部成功且无外网请求。 末十分钟主JS堆在显式GC后约54.47—56.96MiB，斜率0.018MiB/分钟，不是GPU显存。已观察根创建/销毁，但叶tileUnload事件为0时不能称该事件压力路径已覆盖。

首轮分包浏览测试把布鲁克林大桥曼哈顿桥头误当成布鲁克林区，最终“实际GLB每区请求”断言拦下，保留package-first-failure记录。改用资料明确的曼哈顿大桥DUMBO桥头后通过。旧phase9v1同机位性能对照保留，但其brooklyn步骤不算该行政区覆盖；新路线见config/final-review-route.json。

环境为Debian13/Linux x86_64，Node24.19、Python3.12.14、Chromium154.0.8037.57/ANGLE SwiftShader软件渲染，1440×1000、DPR1、均衡0.9x；390×844/844×390触控为模拟环境。真实GPU显存未测、移动真机/其他浏览器未测。阶段9同条件对照首场景4.156→3.378秒、JS峰值约94.6→50.3MiB，同时rAFP99由216.8恶化到283.4ms；保留该取舍，不能承诺60FPS。当前30分钟主JS堆尾部数据见acceptance.json，不与显存混称。

全资源审计：25888文件、15071GLB头、22789本地引用，错误0。完整包的实际大小/逐文件SHA/各分包SHA以包外delivery-manifest.json、SHA256SUMS、stage10/package.json为准，避免文档内自校验循环。新目录完整解压及禁外网新缓存浏览已实测，五区原始叶实际请求、稳定ID拾取、地面和预览通过。

## 逐项状态

|用户项目|状态|证据（主要在reports/stage10，文档另列）|范围和限制|
|---|---|---|---|
|1|passed_source_census|census.json,input-lock.json,borough-coverage.csv|all source records reread; real physical building universe not independently counted|
|2|passed_distinctions|census.json,package-browser.json|download/processed/published/actual visible/independently verified separate|
|3|passed_with_scope_limit|AUTHENTICITY_FINAL.md|source denominator and34original exclusions, not reality coverage|
|4|partial|lifecycle-all-source.csv.gz,lifecycle-candidates.json|target epoch not unified; all current physical statuses unknown; DOB work candidates not completion proof|
|5|passed_disclosure|release.html,KNOWN_GAPS.md|unknown layers/fields and non-completed body/roof/facade clearly flagged|
|6|partial|independent-evidence.json,evidence-lock.json|227objects have independent DOB administration; independently surveyed position/outline/height0|
|7|partial|review-summary.json,object-review.json|334source objects/309nonplaceholder across five boroughs rechecked against raw/GLB, not200independent real surveys|
|8|partial|landmark-checklist.json,landmarks/browser.json|29dossier8aspect audit; only2partial representations, no missing-view fabricated completion|
|9|passed_disclosure|review-summary.json,AUTHENTICITY_FINAL.md|position/outline/height/roof/facade/reality errors separate; reality max error null|
|10|passed_no_unsupported_precision|AUTHENTICITY_FINAL.md|numerical fidelity does not imply source or real-world accuracy|
|11|passed|tests-final.log,typecheck.log,build-final.log,final-build-match.json,core.json|57rule tests; GIS/polygons/null/pagination/ID/streaming/replacement + actual browser suites|
|12|passed_source_scene|inspection/browser.json,observations.json,soak/result.json|25actual source observations; global physical height remains blocked|
|13|passed|resource-audit.json,package-browser.json|all GLB headers/references and fresh cache local requests; no old cache substitute|
|14|passed_declared_rights_audit|resource-audit.json,runtime-files.json,delivery-manifest.json|per-file rights basis, individual third-party notices, unknown-rights originals excluded|
|15|passed|nyc-developer-source.zip,source-package.json,REBUILD.md|source/locks/scripts/docs/samples; all raw originals retained locally, not all in source ZIP|
|16|passed_current_published_runtime|six actual ZIPs,package.json|all current published assets; complete real-city exterior models NOT achieved|
|17|passed|delivery-manifest.json,assemble.py|five borough ZIPs + common; no old base, no download-only placeholder|
|18|passed|start-local.py,package-server.log|actual127.0.0.1 starter in independently extracted new directory|
|19|passed_disclosure|DELIVERY.md,single-preview.json|offline localHTTP vsfile double-click explicitly separated|
|20|passed|package-browser.json|no CDN,online font,unconfigured cloud or paid API runtime requirement|
|21|passed|package-browser.json|fresh Chromium context,cache disabled,outside blocked,localhost preserved,all five actual leaf loads|
|22|partial|preview-single.html,single-preview-build.json|real original evidence embedded,4historical fronts+partialWTC, complete current fine sample0|
|23|partial_environment_limit|single-preview.json|defaultfile blocked by enterprise policy; actual offline embedding and localHTTP pass; unsupportedWebGL finite error|
|24|passed|preview-single.html|explicit local partial research title, not full New York model|
|25|passed_documentation|DELIVERY.md,REBUILD.md,AUTHENTICITY_FINAL.md,KNOWN_GAPS.md|sources,rights,coverage and limitations persist with project|
|26|passed_disclosure|environment.json,QUALITY.md,PERFORMANCE_REVIEW.md,package.json|softwareChromium154,viewport/DPR,actual sizes/years/quality; other browsers/mobile hardware not tested|
|27|passed|assembly.log,package-browser.json,delivery-manifest.json,SHA256SUMS|real new-directory extraction/start; per-file and per-archive checksums|
|28|passed_conservative_update_tool|incremental-rebuild.json,update-tests.log,UPDATE.md|actualsingleID/full20objecttile/boroughindex;3scopepatch+rollback,owner-loss rejected; no real newepoch matching claim|
|29|passed_honest_partial_status|acceptance.json,AUTHENTICITY_FINAL.md|unmet exterior/roof/facade/independentreality goals remain partial|
|30|passed_handoff_scope|DELIVERY.md,package.json,FINAL_ACCEPTANCE.md|launch/currentcoverage/fine0/numericalvsrealprecision/performance/remaininginputs|

## 交付与后续

按docs/DELIVERY.md组装六个实物分包，执行`python3 nyc-local/start-local.py --port 8080`，访问`http://127.0.0.1:8080/index.html`。本地HTTP不需外网；file://默认被本机企业策略拦截。preview-single.html只为4块1936正面和部分WTC的单文件，局部完整现状建筑仍0。

开发源码、固定依赖、真实小样本、来源清单、完整运行载荷分别交付；多GiB原始主库/历史3dm/研究原件保留工作区，未知权利原件不进入分发包，完整原始离线重建仍需这些输入。没有因性能/体积改变楼高、删除楼、缩小城市或损坏Tinnis。

本轮修复更新邻楼丢失保护、回退历史状态、单文件企业策略失败后的导航竞态、历史照片正面默认朝向和未知背面镜像问题。原精细模型未改；新预览经实际正面照片/180度背面中性像素检查。未来最小输入：统一目标历元、单位与地面框架确认、可分发现状尺度/四向参考、独立分层测量、屋顶点云和真实墙基线。见KNOWN_GAPS与NEXT_STEPS；不自动开始新的建模阶段。
