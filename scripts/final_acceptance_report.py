"""Read actual receipts; absent evidence remains pending, incomplete reality goals stay partial."""
import json,subprocess
from nyc.download import ROOT,atomic_json,now


def main():
    out=ROOT/'reports/stage10'
    def read(name):
        p=out/name;return json.loads(p.read_text())if p.is_file()else None
    census=read('census.json');review=read('review-summary.json');soak=read('soak/result.json');package=read('package.json');browser=read('package-browser.json');source=read('source-package.json');resource=read('resource-audit.json');preview=read('single-preview.json')
    testlog=(out/'tests-final.log').read_text();buildlog=(out/'build-final.log').read_text()if(out/'build-final.log').is_file()else(out/'build.log').read_text();tests='Ran 57 tests'in testlog and'\nOK'in testlog;built='✓ built'in buildlog
    results=[]
    def item(n,status,evidence,note):results.append({'requirement':n,'status':status,'evidence':evidence,'note':note})
    item(1,'passed_source_census','census.json,input-lock.json,borough-coverage.csv','all source records reread; real physical building universe not independently counted')
    item(2,'passed_distinctions','census.json,package-browser.json','download/processed/published/actual visible/independently verified separate')
    item(3,'passed_with_scope_limit','AUTHENTICITY_FINAL.md','source denominator and34original exclusions, not reality coverage')
    item(4,'partial','lifecycle-all-source.csv.gz,lifecycle-candidates.json','target epoch not unified; all current physical statuses unknown; DOB work candidates not completion proof')
    item(5,'passed_disclosure','release.html,KNOWN_GAPS.md','unknown layers/fields and non-completed body/roof/facade clearly flagged')
    item(6,'partial','independent-evidence.json,evidence-lock.json','227objects have independent DOB administration; independently surveyed position/outline/height0')
    item(7,'partial','review-summary.json,object-review.json','334source objects/309nonplaceholder across five boroughs rechecked against raw/GLB, not200independent real surveys')
    item(8,'partial','landmark-checklist.json,landmarks/browser.json','29dossier8aspect audit; only2partial representations, no missing-view fabricated completion')
    item(9,'passed_disclosure','review-summary.json,AUTHENTICITY_FINAL.md','position/outline/height/roof/facade/reality errors separate; reality max error null')
    item(10,'passed_no_unsupported_precision','AUTHENTICITY_FINAL.md','numerical fidelity does not imply source or real-world accuracy')
    item(11,'passed'if tests and built else'pending','tests-final.log,typecheck.log,build-final.log,final-build-match.json,core.json','57rule tests; GIS/polygons/null/pagination/ID/streaming/replacement + actual browser suites')
    item(12,'passed_source_scene'if read('inspection/browser.json')else'pending','inspection/browser.json,observations.json,soak/result.json','25actual source observations; global physical height remains blocked')
    item(13,'passed'if resource and not resource['errors']and browser and not browser['errors']else'pending','resource-audit.json,package-browser.json','all GLB headers/references and fresh cache local requests; no old cache substitute')
    item(14,'passed_declared_rights_audit'if resource and resource['all_files_have_declared_rights_basis']else'pending','resource-audit.json,runtime-files.json,delivery-manifest.json','per-file rights basis, individual third-party notices, unknown-rights originals excluded')
    item(15,'passed'if source else'pending','nyc-developer-source.zip,source-package.json,REBUILD.md','source/locks/scripts/docs/samples; all raw originals retained locally, not all in source ZIP')
    item(16,'passed_current_published_runtime'if package else'pending','six actual ZIPs,package.json','all current published assets; complete real-city exterior models NOT achieved')
    item(17,'passed'if package and len(package['runtime_parts'])==6 else'pending','delivery-manifest.json,assemble.py','five borough ZIPs + common; no old base, no download-only placeholder')
    item(18,'passed'if browser else'pending','start-local.py,package-server.log','actual127.0.0.1 starter in independently extracted new directory')
    item(19,'passed_disclosure','DELIVERY.md,single-preview.json','offline localHTTP vsfile double-click explicitly separated')
    item(20,'passed'if browser and not browser['external_requests']else'pending','package-browser.json','no CDN,online font,unconfigured cloud or paid API runtime requirement')
    item(21,'passed'if browser else'pending','package-browser.json','fresh Chromium context,cache disabled,outside blocked,localhost preserved,all five actual leaf loads')
    item(22,'partial','preview-single.html,single-preview-build.json','real original evidence embedded,4historical fronts+partialWTC, complete current fine sample0')
    item(23,'partial_environment_limit'if preview else'pending','single-preview.json','defaultfile blocked by enterprise policy; actual offline embedding and localHTTP pass; unsupportedWebGL finite error')
    item(24,'passed','preview-single.html','explicit local partial research title, not full New York model')
    item(25,'passed_documentation','DELIVERY.md,REBUILD.md,AUTHENTICITY_FINAL.md,KNOWN_GAPS.md','sources,rights,coverage and limitations persist with project')
    item(26,'passed_disclosure','environment.json,QUALITY.md,PERFORMANCE_REVIEW.md,package.json','softwareChromium154,viewport/DPR,actual sizes/years/quality; other browsers/mobile hardware not tested')
    item(27,'passed'if browser else'pending','assembly.log,package-browser.json,delivery-manifest.json,SHA256SUMS','real new-directory extraction/start; per-file and per-archive checksums')
    item(28,'passed_conservative_update_tool','incremental-rebuild.json,update-tests.log,UPDATE.md','actualsingleID/full20objecttile/boroughindex;3scopepatch+rollback,owner-loss rejected; no real newepoch matching claim')
    item(29,'passed_honest_partial_status','acceptance.json,AUTHENTICITY_FINAL.md','unmet exterior/roof/facade/independentreality goals remain partial')
    item(30,'passed_handoff_scope'if package and browser else'pending','DELIVERY.md,package.json,FINAL_ACCEPTANCE.md','launch/currentcoverage/fine0/numericalvsrealprecision/performance/remaininginputs')
    perf={'real_continuous_seconds':soak['elapsed_real_seconds']if soak else None,'completed_real_30_minutes':bool(soak and soak['completed_required_duration']and not soak['errors']and soak['same_code_entire_run']),'errors':soak['errors']if soak else None,'gpu_vram_measured':False,'comparison':'phase9fixedroutefirstscene4156→3378ms,pooledrAFP99216.8→283.4ms; regression retained, no universal60FPS','phase10_condition':'same software machine; additional rule/browser/rebuild tasks ran concurrently in the early part; not a new paired performance benchmark'}
    if soak:
        rows=soak['cycles'];tail=[r for r in rows if r['elapsed_real_seconds']>=soak['elapsed_real_seconds']-600];ys=[r['jsHeapAfterForcedGC']['usedSize']for r in tail];xs=[r['elapsed_real_seconds']/60 for r in tail];xm=sum(xs)/len(xs);ym=sum(ys)/len(ys);slope=sum((x-xm)*(y-ym)for x,y in zip(xs,ys))/sum((x-xm)**2 for x in xs)
        perf.update({'cycles':len(rows),'requests':soak['requestCount'],'failed_requests':soak['failedRequests'],'failed_request_reason_limit':'legacy soak harness counts requestfailed including cancellations but does not retain errorText; do not claim zero network failures. Fresh package test separately logs reasons.','tail_after_forced_gc_main_heap_mib_min':min(ys)/1048576,'tail_after_forced_gc_main_heap_mib_max':max(ys)/1048576,'tail_slope_mib_per_minute':slope/1048576,'main_document_navigated_once':soak['continuous_main_document'],'root_created':rows[-1]['runtime']['created'],'root_destroyed':rows[-1]['runtime']['destroyed'],'tile_unloaded_events':rows[-1]['unloadedTotal'],'note':'main JS isolate after explicitly forcedGC percycle; resource caches warm, estimatedGPU notmeasuredVRAM; bounded observed window notproof all leaks absent; root destruction observed, no leaf tileUnload events if0'})
    receipt={'schema_version':10,'at_utc':now(),'source_version':census['source_version'],'code_base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'worktree_candidate_fingerprint':'soak/result.json codeFingerprint + input-lock, not a claim HEAD was clean at test time','overall':'partial reality build; complete published runtime delivered only when package receipts exist','complete_real_city_exteriors':False,'complete_current_fine_buildings':0,'independent_reality_error_m':None,'requirements':results,'performance':perf,'initial_failures_retained':['tests.log localTCPsandboxrestriction; rerun elevated tests-final.log passed','update-tests initially caught neighbour-map weakness; fixed, final realowner tests passed','single-browser initial policy-navigation race; newpage fallback fixed without bypassing enterprise policy']}
    atomic_json(out/'acceptance.json',receipt)
    rows='\n'.join(f"|{r['requirement']}|{r['status']}|{r['evidence']}|{r['note']}|"for r in results)
    md=f'''# 最终验收报告 · 部分完成

当前工程交付全部已发布五区资源及检查工具；**未达到五区全部可信主体、屋顶与逐立面复刻目标**，不能宣布全项目现实真实性验收通过。实体分母、版本、排除与未知见[真实性报告](AUTHENTICITY_FINAL.md)。完整精细当前建筑0，独立实测现实误差未知。

## 实际运行证据

本轮类型检查与Vite构建{'通过'if built else'待验证'}，57项规则测试{'通过'if tests else'待验证'}；实际浏览器：坐标/地形8组、地标6组及12生成视角、立面8组/12AOI、检查器12组/25观察点、故障11组、单文件6组。浏览器截图只辅助实际操作与日志，不代替资料/几何/状态检查。首次普通沙箱测试因本地TCP权限失败，保留失败日志，在允许127.0.0.1监听后重跑通过，没有隐藏失败。

真实连续浏览：{perf['real_continuous_seconds'] if soak else'尚未完成'}秒，完成30分钟条件：{perf['completed_real_30_minutes']}；{'周期'+str(perf['cycles'])+'，请求'+str(perf['requests'])+'，失败请求'+str(perf['failed_requests'])if soak else'仍在运行，不能预先写通过'}。冻结候选资产指纹见stage10/soak/result.json。测试时HEAD为来源基线，工作区包含本轮代码，实际bundle指纹才是运行候选证据。早期同时运行其他回归/重建，不冒称严格独占性能对照。

连续harness的requestfailed计数包含取消但没有保留errorText，故不称零网络失败；{('最终包新缓存记录'+str(len(browser['requests']))+'请求、'+str(len(browser['failedRequests']))+'失败，HTTP全部成功且无外网请求。')if browser else'最终包将另记录每次请求及失败原因。'} 末十分钟主JS堆在显式GC后{'约'+str(round(perf['tail_after_forced_gc_main_heap_mib_min'],2))+'—'+str(round(perf['tail_after_forced_gc_main_heap_mib_max'],2))+'MiB，斜率'+str(round(perf['tail_slope_mib_per_minute'],3))+'MiB/分钟'if soak else'未完成统计'}，不是GPU显存。已观察根创建/销毁，但叶tileUnload事件为0时不能称该事件压力路径已覆盖。

首轮分包浏览测试把布鲁克林大桥曼哈顿桥头误当成布鲁克林区，最终“实际GLB每区请求”断言拦下，保留package-first-failure记录。改用资料明确的曼哈顿大桥DUMBO桥头后通过。旧phase9v1同机位性能对照保留，但其brooklyn步骤不算该行政区覆盖；新路线见config/final-review-route.json。

环境为Debian13/Linux x86_64，Node24.19、Python3.12.14、Chromium154.0.8037.57/ANGLE SwiftShader软件渲染，1440×1000、DPR1、均衡0.9x；390×844/844×390触控为模拟环境。真实GPU显存未测、移动真机/其他浏览器未测。阶段9同条件对照首场景4.156→3.378秒、JS峰值约94.6→50.3MiB，同时rAFP99由216.8恶化到283.4ms；保留该取舍，不能承诺60FPS。当前30分钟主JS堆尾部数据见acceptance.json，不与显存混称。

全资源审计：{resource['runtime_files']if resource else'待审计'}文件、{resource['glb_headers_checked']if resource else'待审计'}GLB头、{resource['local_references_checked']if resource else'待审计'}本地引用，错误{len(resource['errors'])if resource else'未知'}。完整包的实际大小/逐文件SHA/各分包SHA以包外delivery-manifest.json、SHA256SUMS、stage10/package.json为准，避免文档内自校验循环。{'新目录完整解压及禁外网新缓存浏览已实测，五区原始叶实际请求、稳定ID拾取、地面和预览通过。'if browser else'新目录组装/禁外网浏览尚待执行，此处不提前写通过。'}

## 逐项状态

|用户项目|状态|证据（主要在reports/stage10，文档另列）|范围和限制|
|---|---|---|---|
{rows}

## 交付与后续

按docs/DELIVERY.md组装六个实物分包，执行`python3 nyc-local/start-local.py --port 8080`，访问`http://127.0.0.1:8080/index.html`。本地HTTP不需外网；file://默认被本机企业策略拦截。preview-single.html只为4块1936正面和部分WTC的单文件，局部完整现状建筑仍0。

开发源码、固定依赖、真实小样本、来源清单、完整运行载荷分别交付；多GiB原始主库/历史3dm/研究原件保留工作区，未知权利原件不进入分发包，完整原始离线重建仍需这些输入。没有因性能/体积改变楼高、删除楼、缩小城市或损坏Tinnis。

本轮修复更新邻楼丢失保护、回退历史状态、单文件企业策略失败后的导航竞态、历史照片正面默认朝向和未知背面镜像问题。原精细模型未改；新预览经实际正面照片/180度背面中性像素检查。未来最小输入：统一目标历元、单位与地面框架确认、可分发现状尺度/四向参考、独立分层测量、屋顶点云和真实墙基线。见KNOWN_GAPS与NEXT_STEPS；不自动开始新的建模阶段。
'''
    (ROOT/'reports/FINAL_ACCEPTANCE.md').write_text(md)
    print('ACCEPTANCE',len(results),'items;',CounterStatus(results),'real30min',perf['completed_real_30_minutes'])


def CounterStatus(rows):
    from collections import Counter
    return dict(Counter(r['status']for r in rows))


if __name__=='__main__':main()
