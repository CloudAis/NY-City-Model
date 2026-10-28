"""Measured before/after and continuous-run reports, never promote pending checks."""
import json,math,statistics,datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from nyc.download import ROOT,atomic_json,now


def load(name):return json.loads((ROOT/'reports/stage9'/name).read_text())
def pct(values,p):
    values=sorted(values)
    return values[min(len(values)-1,math.floor(len(values)*p))]if values else None
def main():
    b=load('baseline-verified.json');a=load('optimized-final.json');first=load('optimized.json');env=load('environment.json');integrity=load('input-integrity.json');visual=load('visual.json')
    assert b['route']==a['route']and b['hardware']==a['hardware']and b['probe_version']==a['probe_version']==2
    rows=[]
    for old,new in zip(b['steps'],a['steps']):
        rows.append({'step':old['id'],'baseline':old['measurement'],'optimized':new['measurement'],'baseline_new_requests':old['new_requests'],'optimized_new_requests':new['new_requests'],'baseline_loaded_total':old['viewer']['loadedTotal'],'optimized_loaded_total':new['viewer']['loadedTotal']})
    def aggregate(run):
        intervals=[r for s in run['steps']for r in s['sample_trace']]
        return {'raf_ms':{f'p{int(p*100)}':pct([r[1]for r in intervals],p)for p in [.5,.95,.99]},'render_active_raf_ms':{f'p{int(p*100)}':pct([r[1]for r in intervals if r[2]>0],p)for p in [.5,.95,.99]},'long_tasks':sum(s['measurement']['long_tasks']['count']for s in run['steps']),'long_task_total_ms':sum(s['measurement']['long_tasks']['total_ms']for s in run['steps']),'js_heap_observed_peak_bytes':max(s['measurement']['jsHeap']['used']for s in run['steps']),'known_buffer_estimate_peak_bytes':max(s['measurement']['resources']['known_buffer_bytes']for s in run['steps']),'requests':len(run['requests']),'diagnostic_panel_dom_updates':max(s['measurement']['domWrites']['diagnosticPanel']for s in run['steps'])}
    comparison={'at_utc':now(),'baseline_commit':b['code_commit'],'optimized_commit':a['code_commit'],'first_real_scene_ms':{'baseline':b['first_real_scene_ms'],'optimized':a['first_real_scene_ms']},'same_hardware_viewport_dpr_quality_route_and_probe':True,'baseline':aggregate(b),'optimized':aggregate(a),'steps':rows,'sample_size':'one controlled route run per final candidate; no statistical significance or universal60FPS claim','initial_candidate_retained':'optimized.json (4aa78c1); changed foveated/progressive settings to match baseline before final ebc86ce run','physical_gpu_vram_measured_bytes':None,'data_integrity_errors':integrity['errors'],'fixed_view_numeric':visual['numeric'],'baseline_teardown_errors':visual['errors'],'geometry_or_texture_lossy_compression':'none','source_model_geometry_change_m':0,'zero_change_basis':'originalGLB bytes, complete leaf transforms/bounds/request volumes/feature maps retained; not reality accuracy'}
    atomic_json(ROOT/'reports/stage9/comparison.json',comparison)
    text=f'''# 性能对照 · 2026-10-28（Asia/Singapore）

现有工程同路线性能与稳定性改造，基线{b['code_commit'][:7]}，最终候选{a['code_commit'][:7]}。完整源数据/原精细资产保持；当前城市主体/全球Z缺口不因性能阶段完成。

## 设备与协议

Debian13 / Linux x86_64，Xeon8573C虚拟机，lscpu暴露5逻辑CPU，cgroup配额4CPU、32GiB内存。Chromium{a['browser']}，ANGLE SwiftShader软件WebGL2；没有物理GPU显存实测。Node24.19.0，Vite8.3.5、Cesium1.146.0、TS7.0.2固定。实际完整环境见stage9/environment.json与每次hardware字段。

1440×1000、DPR1、均衡0.9×，相同nyc-fixed-route-v1、相同probeVersion2，浏览器HTTP缓存关闭、OS文件缓存未清空。前后浏览器顺序运行，比较期间无其他图形测试。首个真实场景要求实际道路瓦片解析并出现WebGL绘制，非启动占位点，更不是全城全部就绪。后续回归/哈希/打包负载另录在soak/background-work.json，不混入受控前后基准。

rAF分位数是含静止时段的UI心跳，render_active另计实际提交绘制的间隔，均不是GPU计时。绘制调用/三角形是实际WebGL提交（含多帧重复），不能当独立建筑数量；源轮廓主要是LINES。JS堆是浏览器接口当时采样、未在短路线强制GC；不以此声明精确分配节省。GPU只报告已知缓冲分配与Cesium估算，纹理/驱动/帧缓冲总显存未知。探针本身有开销，两侧同样安装。

## 逐段结果（毫秒）

|路线|基线rAF P50/P95/P99|候选rAF P50/P95/P99|新请求 基线→候选|
|---|---|---|---|
'''
    for r in rows:
        x,y=r['baseline']['raf_ms'],r['optimized']['raf_ms'];text+=f"|{r['step']}|{x['p50']:.1f}/{x['p95']:.1f}/{x['p99']:.1f}|{y['p50']:.1f}/{y['p95']:.1f}/{y['p99']:.1f}|{r['baseline_new_requests']}→{r['optimized_new_requests']}|\n"
    old,new=comparison['baseline'],comparison['optimized']
    text+=f'''
首个真实场景：{b['first_real_scene_ms']}→{a['first_real_scene_ms']}ms。合并样本rAF P95：{old['raf_ms']['p95']:.1f}→{new['raf_ms']['p95']:.1f}ms，P99：{old['raf_ms']['p99']:.1f}→{new['raf_ms']['p99']:.1f}ms。JS堆观察峰值{old['js_heap_observed_peak_bytes']/1048576:.1f}→{new['js_heap_observed_peak_bytes']/1048576:.1f}MiB；诊断面板DOM更新{old['diagnostic_panel_dom_updates']}→{new['diagnostic_panel_dom_updates']}；总请求{old['requests']}→{new['requests']}。每段详细draw、triangles、tile、longtask、内存和原始帧间隔在comparison.json及两个原报告。

内存/诊断开销降低，帧时并非一致改善。跨区与首次显示仍有明显长帧，部分P99/首景时间更差；本轮不宣称已达到统一帧时目标或60FPS。最终只是一对同条件测量，不能推断统计显著性。初始4aa78c1方案数据保留optimized.json；后来恢复与基线一致的foveated/progressive设置再测，未挑选隐藏较差结果。尚未执行单项CPU/GPU因果剖析，不能将所有长帧归因某个驱动或函数。

## 每项改动、依据与取舍

1. 旧五区根目录一次解析4.2MB左右并扫描平铺叶。新增按密度中位拆分的空间目录，330页，每页≤32原叶/≤32k紧凑源元数据；父球保守包住子球。每个原GLB最大仅约1.38MB，已有≤200来源对象批次，故没有为成绩重新裁楼/改网格。全部7383严格叶完整保留、变换/包围体/请求范围和feature关联一致。代价是额外JSON请求；逐段请求增加可见，不能称网络总量普降。
2. 根创建并发2；Cesium请求全局12/每主机6；查询Worker原生fetch并发4、解析单Worker。软创建预算纹理2/程序2/缓冲4ms（总8ms），实际形状检查确认生效。单个GL上传/编译工作不可抢占，8ms不是最坏帧保证。视锥/引擎地平线剔除、运动剔除及目的地预取沿用；最终恢复基线foveated和0.3渐进设置，不引入低模。
3. 样式缓存8项，仅选中/悬停/证据色变化时重设；事件计数合并为250ms刷新，关闭的诊断面板不反复写HTML。上列DOM计数可直接对照；FPS因果贡献未独立隔离测量。材质高亮仍按feature ID，实际拾取回归通过。
4. 查询移入Worker，重复桶请求合并，14项/8MiB字符大小估算LRU，未知查询不虚构名称；8秒请求期限、有限重试/冷却，22秒RPC期限。估算不是Worker真实堆字节。根有12秒Abort期限，其他CesiumXHR15秒、最多一次重试；适配器与1.146源码绑定，升级需重新核对。过期根销毁、监听器/Worker/定时器释放，原模型仍可重载。
5. 显式渲染循环在绘制前检查真实尺寸/上下文，隐藏/局部地面时暂停世界绘制；静止场景按需提交。修复旧关闭页/失焦回调、查询晚到覆盖视角和悬停节流问题。恢复采用重新加载并核对保存视角，不宣称同一GPU对象原地复活。
6. 三档见docs/QUALITY.md；全档几何和原纹理不变，没有有损压缩。自动画质可关、30秒迟滞、有上下限、手动优先。近/远裁切和局部坐标保留真实源尺寸。原7500m完整建筑细节距离门槛保留，80km全城段不是全城精细建筑同时绘制测试。

这些改动作为组合完成前后测量，未对每项单独做因果A/B。主数据、静态索引、原始精细表示与旧数据资产的完整性见input-integrity.json；候选并未通过删模型/缩城取得内存结果。

## 保真

三处真实固定相机、相同中性光和原始精度画布区域截图（含界面叠层）对照：中城RGB平均差0，Brooklyn/Queens差异见visual.json，均接近零。截图不是现实误差测量。原始GLB字节与局部/世界矩阵逐项保持，新增几何形变0只表示本轮未改数据；源测绘/高度/立面误差仍未知。旧基线关闭页面的已知scene访问错误单独记录，候选渲染/关闭错误为0。

完整稳定性与至少30分钟实跑是否完成，只以STABILITY_REVIEW和soak/result.json为准，不以本对照代替。
'''
    (ROOT/'reports/PERFORMANCE_REVIEW.md').write_text(text)
    result=ROOT/'reports/stage9/soak/result.json'
    if not result.exists():
        (ROOT/'reports/STABILITY_REVIEW.md').write_text('# 稳定性检查进行中\n\n真实30分钟连续浏览尚未完成，不得记通过。已有11故障组/规则/对照记录，等待soak/result.json。\n');return
    soak=json.loads(result.read_text());cycles=soak['cycles'];last=[r for r in cycles if r['elapsed_real_seconds']>=soak['elapsed_real_seconds']-600]
    heap=[r['jsHeapAfterForcedGC']['usedSize']/1048576 for r in last];times=[r['elapsed_real_seconds']/60 for r in last]
    meanx=statistics.mean(times);meany=statistics.mean(heap);den=sum((x-meanx)**2 for x in times);slope=sum((x-meanx)*(y-meany)for x,y in zip(times,heap))/den if den else None
    trend={'last_ten_minutes_samples':len(last),'js_heap_after_forced_gc_min_mib':min(heap),'max_mib':max(heap),'slope_mib_per_minute':slope,'heap_forced_gc_is_intrusive':True,'memory_scope':'CDP main-isolate heap; query Worker cache separately estimated; no VRAM interface','estimated_cesium_peak_bytes':max(r['estimatedCesiumResourceBytes']for r in cycles),'known_webgl_buffer_estimate_peak_bytes':max(r['resources']['known_buffer_bytes']for r in cycles),'observed_live_heap_plateau':slope is not None and abs(slope)<1 and max(heap)-min(heap)<12}
    atomic_json(ROOT/'reports/stage9/memory-trend.json',trend)
    faults=load('faults.json')
    local_start=datetime.datetime.fromisoformat(soak['started_utc'].replace('Z','+00:00')).astimezone(ZoneInfo('Asia/Singapore')).isoformat(timespec='seconds')
    local_end=datetime.datetime.fromisoformat(soak['completed_utc'].replace('Z','+00:00')).astimezone(ZoneInfo('Asia/Singapore')).isoformat(timespec='seconds')
    stability=f'''# 稳定性 · 2026-10-28（Asia/Singapore）

冻结候选{soak['code_commit'][:7]}，实际连续{soak['elapsed_real_seconds']:.1f}现实秒，{len(cycles)}轮完整代表性操作。开始{local_start}，结束{local_end}（Asia/Singapore；原始审计UTC保留在JSON）。未使用虚拟时间/模拟加速；主文档未重载，构建指纹前后相同={soak['same_code_entire_run']}，满足至少30分钟={soak['completed_required_duration']}。

全城俯视→中城缩放/环绕/查询/俯视→midtown或CentralPark真实DEM受限行走→Brooklyn/Queens/Bronx/Staten跨区→轮换码头/公园/坡地等额外区→图层/树点/取消飞行→返回中城。完整cycles/30秒心跳在soak目录。街道步是2017DEM检查，不是完整当代街景或桥面漫游。首次脚本误用滚轮参数的短失败已留soak-harness-first-failure，未计入有效运行，修正后重新计时。

未记录页面/渲染异常{len(soak['errors'])}，未发生主文档重载/以重载掩盖崩溃。请求总数{soak['requestCount']}，请求失败/取消合计{soak['failedRequests']}（取消不自动等于数据错误，应用错误另列）。没有观察到主场景纹理丢失；原精细地标/历史照片另外做既有入口回归，不能把它们未进入全球场景称全城精细模型压力测试。

每轮相同返回点采样CDP主isolate JS堆：强制GC前/后都保存，GC影响如实记录。最后10分钟{len(last)}个样本，GC后堆{min(heap):.2f}—{max(heap):.2f}MiB，斜率{slope:.3f}MiB/分钟；按本项目<1MiB/分钟且波动<12MiB判据观察到近似平台={trend['observed_live_heap_plateau']}。这是有限路线的活对象证据，不证明无泄漏；Worker字符缓存估算与浏览器全部进程RSS不混同主堆。

Cesium资源估算峰值{trend['estimated_cesium_peak_bytes']/1048576:.2f}MiB，探针已知WebGL缓冲估算峰值{trend['known_webgl_buffer_estimate_peak_bytes']/1048576:.2f}MiB；无实测显存。瓦片缓存卸载和整根销毁分别由unloadedTotal/runtime.destroyed记录，整体销毁不冒充引擎tileUnload次数。相机/界面/缓存切换没有改主数据，最终完整性校验另列。

## 故障与回归

故障浏览器实际{len(faults['checks'])}组通过，非预期错误{len(faults['errors'])}：三档/手动优先、快速切换/过期结果、Worker取消、404、损坏GLB、12秒根超时、15秒内容XHR有限重试、断网/手动重试恢复、冻结切回/resize、真实WEBGL_lose_context/restore世界重建及局部地面恢复。故意制造的控制台错误保留expectedConsole，不掩盖非预期错误。网络/上下文扩展作用于实际软件WebGL浏览器，不是假数据或模拟器改时间。

背景可见性实际观察：{json.dumps(faults['observations'],ensure_ascii=False)}。测试使用第二页和CDP真实freeze/active；若headless未报告hidden，不能视作真实操作系统切后台已测。无真实手机、硬件GPU、其他浏览器和真实OOM；移动检查仅浏览器尺寸/CDP触点仿真。GPU原地重建没有实现，采用显式完整页面重建恢复，独立于不重载的30分钟正常运行。

55规则、4运行策略组、12新交互（25实际观察区）、原地形8/地标6/立面8回归结果分别在stage9。构建有Cesium大chunk提示。并行回归/完整性读取等额外系统负载写入soak/background-work.json；它们不混入隔离的短路线前后比较。新发现的零尺寸帧缓冲、旧文档销毁回调、元数据超时钩子失效、首次重试冷却和异步导航竞态均已修复并复测。

全球正高/椭球高、桥面及完整可信主体/屋顶/现状立面仍是前期证据缺口。本轮不宣布全纽约复刻完成，也没有为性能移动/缩放/删除建筑。长帧与首景目标未全面改善，见PERFORMANCE_REVIEW，下一轮需真实GPU设备与进一步CPU/GPU剖析。
'''
    (ROOT/'reports/STABILITY_REVIEW.md').write_text(stability)
    # Separate scientific-like memory curves: every line has an explicit scope/unit.
    width,height=960,370;left,bottom=65,315;span=max(r['elapsed_real_seconds']for r in cycles)
    series=[('JS主堆 GC后（MiB）','#356875',[r['jsHeapAfterForcedGC']['usedSize']/1048576 for r in cycles]),('Cesium资源估算（MiB，非显存实测）','#a37b35',[r['estimatedCesiumResourceBytes']/1048576 for r in cycles])]
    top=max(max(v)for _,_,v in series)*1.12
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="#f4f6ef"/><g font-family="sans-serif" font-size="13" fill="#263d46"><text x="65" y="25">真实连续浏览：主堆与资源估算分开记录；不等于实测显存</text><path d="M65 45V315H930" fill="none" stroke="#718b8d"/>' ]
    for name,color,values in series:
        points=' '.join(f'{left+r["elapsed_real_seconds"]/span*855:.1f},{bottom-v/top*255:.1f}'for r,v in zip(cycles,values));svg.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2"/><text x="65" y="{345 if color=="#356875"else 365}" fill="{color}">{name}</text>')
    for minute in range(0,math.ceil(span/60)+1,5):svg.append(f'<text x="{left+minute*60/span*855:.0f}" y="332">{minute}分</text>')
    for value in range(0,math.ceil(top),10):svg.append(f'<text x="8" y="{bottom-value/top*255:.0f}">{value}MiB</text>')
    svg.append('</g></svg>');(ROOT/'reports/stage9/memory.svg').write_text(''.join(svg))
    print('REPORTED real_seconds',soak['elapsed_real_seconds'],'cycles',len(cycles),'heap slope',slope,'plateau',trend['observed_live_heap_plateau'])


if __name__=='__main__':main()
