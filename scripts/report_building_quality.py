"""Write the handoff from measured reports, not planned acceptance criteria."""
import json
from pathlib import Path
from nyc.download import ROOT,atomic_json,sha,now
def main():
 q=json.loads((ROOT/'reports/stage4/quality-report.json').read_text());browser=json.loads((ROOT/'reports/stage4/browser.json').read_text());foundation=json.loads((ROOT/'reports/stage4/foundation/browser.json').read_text());rebuild=json.loads((ROOT/'reports/stage4/rebuild-check.json').read_text())
 if browser['errors']or foundation['errors']or not rebuild['single_tile_repair_byte_identical']:raise ValueError('verification has unresolved errors')
 tests=(ROOT/'reports/stage4/tests.log').read_text()
 if 'Ran 28 tests'not in tests or not tests.rstrip().endswith('OK'):raise ValueError('complete rule checks did not pass')
 table='\n'.join('|'+ '|'.join(str(v)for v in[b['borough'],b['source_records'],b['published_outline_entities'],b['geometry_parts'],b['source_height_numeric_valid'],0,b['hypothesis_eligible'],0,0])+'|'for b in q['boroughs'])
 md=f"""# 建筑表示与质量 · 阶段4

2026-10-27（Asia/Singapore）；机器明细的at使用UTC。输入是第二阶段2026-10-27-city抓取标签，不是官方2026现状测绘版本。

已发布五区全部取得的非占位来源轮廓，以及显式可选、默认关闭的来源高度假设包络。**可信建筑主体、可靠屋顶和精细立面尚未完成，数量均为0**；不将假设体量冒称已核验纽约建筑。未下载新数据或用随机建筑补缺口。

## 覆盖与口径

|分区|来源记录|发布轮廓实体|输入几何部件|数值有效的源feet高度|可信米制高度|可选假设包络|可靠屋顶|精细立面|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{table}

分母为全部{q['raw_source_records']:,}条来源记录；排除{q['excluded_placeholders']}条官方占位三角形，发布{q['published_outline_entities']:,}来源实体/{q['published_outline_parts']:,}几何部件。俯视轮廓覆盖率{q['ratios']['source_outline_published']*100:.8f}%；非占位分母{q['nonplaceholder_denominator']:,}上的轮廓覆盖100%。可信米制高度、可靠屋顶、精细立面比例各0%。来源实体不保证物理建筑一对一，停车、棚、罐、架空连廊等类型保留标签。

“数值有效”只指正值及来源基本范围检查，不能证明foot种类、独立准确度、屋顶形状、观测年代或完整主体。语义等级outline_only与渲染LOD分开；假设包络不会提升证据等级。

## 几何、身份与资源

- 不用矩形包围盒替代实物轮廓；保留凹角、斜边、朝向、内洞和原部件ID。500m格网只决定完整对象归属，不裁断建筑，不自动合并共墙/连体/同BIN对象。
- 严格GLB仅为真实俯视外轮廓。官方说明是directly-above perimeter，不能据此认定底层墙线、挑檐或悬挑的支撑形状。
- 可选假设包络使用该对象原始HEIGHT_ROOF × 明示international-foot假设0.3048；原feet和US survey foot比较区间均保存，canonical仍null。无屋顶封盖、无虚构塔楼/退台/机房/水塔/坡屋顶/室内。
- 基底是明确的WGS84椭球显示参考+0.25m，不是实测地面。NAVD88/参考框架冲突继续阻止物理基底和世界高程落位。
- GLB含显式UINT32面索引、法线、EXT_mesh_features/EXT_structural_metadata、每对象源ID与部件表；3D Tiles1.1保存实际包围体、ENU→ECEF矩阵及几何误差。矩阵只施加一次。中性材质无装饰贴图。
- 完整原始记录、来源实体、几何部件、owner格与可见对象由data/processed/building-stage4/city/associations.sqlite和瓦片JSON关联；逐文件SHA在data/manifests/stage4/generated-files.jsonl。
- 全城俯视明确暂停这些完整细节瓦片，7000m以下按视野和叶节点viewerRequestVolume载入；没有伪造的低细节盒楼。普通构建用同卷硬链接节省第二份数GiB资源，ZIP是普通独立字节。

## 实际验证

先在下城299/中城812条来源记录运行同一管线并通过5项几何规则，随后扩展五区。

全量资源逐SHA验证{q['output_resource_files_verified']:,}个文件，输出ID无跨瓦片重复；输入/输出/占位及部件数量核对通过。所有来源缺失/异常HEIGHT_ROOF的721条另行检查已存PLUTO候选、未匹配旧模型和未取得LiDAR，未恢复任何可信楼高；见height-gaps.json。其他正值feet仍有单位缺口。

实际抽查{q['reviewed_actual_objects']}个来源对象：五区每区40个分层对象，另加真实内洞记录（候选{q['review_actual_courtyard_candidates']}，与基本集合去重）。高低数值高度、复杂轮廓、大体量、PLUTO工业地块候选均有记录。工业属性保持parcel scope；**已核验复杂屋顶0、独立确认的工业建筑用途0**，不能把复杂轮廓或地块用途冒充这些证据。

抽查逐项核对原始页SHA/OBJECTID、来源几何、部件、GLB索引/法线/方向、源轮廓恢复误差和显式假设高度。GPU轮廓相对保存源最大偏差{q['source_outline_gpu_max_deviation_m']:.10f}m；假设高度跨度数值偏差{q['hypothesis_height_span_max_error_m']:.10f}m。数学屋顶三角剖分测试面积最大差{q['triangulation_area_max_error_m2']:.10g}m²，且不跨内洞；这些测试封盖没有作为真实屋顶发布。

数值误差不等于现场精度。现实位置/楼高误差未知，独立实测0。真实主体的浮空、沉陷、屋顶部件和年代对齐未通过验收。已抽查对象的邻域源多边形相交产生{q['overlap_pairs_flagged']}条检查项，见overlaps.json；这是抽查邻域检查，不是全市穷尽重叠审计。完全相同序列化源几何重复组{len(q['source_geometry_exact_byte_duplicates'])}组，保留身份并进入报告，不自动删楼。

实跑28项Python规则通过；TypeScript/Vite构建通过；本阶段{len(browser['checks'])}组Chromium/SwiftShader浏览器检查通过，既有坐标/方向/真实地形8组回归通过。实际拾取精确源ID、两真实样区/五区局部加载、包络开关、全城俯视、相机、桌面/窄屏、包围框、资源释放，启动请求均本地。修复收起面板把视口压成零宽列的问题；原相机稳定检查改为先等飞行结束，仍要求稳定后完全一致。硬件GPU、多浏览器、真实触摸屏未测。

重复运行样区时几何、编号、关联元数据及mtime保持；主动移走一个派生GLB后自动重建，字节相同且其他瓦片未改；按单建筑ID重建只产生1条来源记录。原始数据不覆盖。2,775个已盘点raw逐SHA未变，主建筑库输入SHA与索引契约一致。

## 可重复命令与下一阶段输入

见README阶段4命令。使用build_buildings.py的--aoi、--borough、--id、--tile选择范围；已索引全市的--force-tile仅重建指定owner格，其余SHA通过才复用。不同数据/处理版本需新work和output；不会默默混入旧缓存。全市大文件在本地，源码Git仅包含清单、管线和两个真实样区。

下一阶段直接消费共用坐标模块、associations.sqlite、真实多边形GLB/feature ID、representation-policy和异常/抽查清单。优先解决foot种类、真实墙基线、地面垂直配准和按日期匹配的分部件屋顶证据；可靠模型/点云证据进入后才提升语义等级。没有自动启动下一阶段。
"""
 (ROOT/'reports/BUILDING_QUALITY.md').write_text(md)
 section=f"""## 阶段4 · 五区来源表示已发布，可信主体受证据阻塞

2026-10-27（Asia/Singapore）。沿用7464214与第三阶段坐标/高程契约，不改Tinnis；先跑下城299、中城812，再用相同管线发布五区{q['raw_source_records']:,}条来源记录中的{q['published_outline_entities']:,}条非占位轮廓。全量关联库、可选高度假设包络、GLB/3D Tiles、来源/处理清单已保存。完整主体/可靠屋顶/精细立面均0，不宣称已完成纽约五区建筑复刻。

保留真实凹角、内洞、部件和朝向；完整对象单一owner格避免重复；占位三角形排除；停车、棚、罐、悬挑、连廊/施工类型不盲目生成假设主体。严格模式高度null；显式包络默认关闭、使用原feet与明示0.3048假设、在椭球显示参考面上检视、未知屋顶不封盖。俯视外轮廓不是已确认墙基线，未编造塔楼、裙房、退台、屋顶、立面或室内。

实际抽查{q['reviewed_actual_objects']}个源对象，覆盖五区分层集合和真实内洞；工业只是PLUTO地块候选，复杂屋顶可靠证据0。GLB恢复源轮廓最大数值差{q['source_outline_gpu_max_deviation_m']:.10f}m；不当作现实测绘精度。721条源缺失/异常高度没有被地块层数或旧模型填充。未知地面/屋顶/年代、邻域相交及重复记录保留可定位原因。

实际验证：28项Python、TS/Vite、{len(browser['checks'])}组新建筑浏览器和8组既有基础回归通过；仅本地资源、精确ID拾取、开关/五区切换、局部/全城视图、相机/窄屏、瓦片释放已操作。修复收起面板零宽视口；稳定检查等待飞行完成后仍精确核对。样区重复不重写瓦片；丢失单瓦片可按原字节修复；按建筑ID重建只产出该记录。2,775已盘点raw未变。

未完成验收：可信建筑主体、真实复杂屋顶、立面、独立现实精度、全球建筑基底接地/浮空沉陷、历史模型当前匹配、真实点云屋顶提取。其原因和比例在reports/BUILDING_QUALITY.md；不以显式假设包络替代这些验收。

"""
 progress=ROOT/'docs/PROGRESS.md';old=progress.read_text();progress.write_text(old.replace('# 阶段实况\n','# 阶段实况\n\n'+section,1))
 nexttext=f"""# 阶段4接续（不自动启动下一阶段）

固定/workspace/nyc-3d-html，先读AGENTS和全套docs、reports/BUILDING_QUALITY.md、GEOGRAPHIC_REGISTRATION.md。检查点基于7464214，当前五区来源轮廓发布完成，可信建筑主体因证据缺口仍未完成。

直接输入：

1. scripts/nyc/coordinates.py（含正式GIS批量顶点转换）和src/geo/coordinates.ts：米/ECEF/分瓦片ENU、显式椭球高。不可用未知正高直接落位。
2. data/processed/building-stage4/city/associations.sqlite：{q['raw_source_records']:,}来源实体、raw引用、部件ID、500m完整对象owner、证据/排除原因、原几何。只读消费，不修改第二阶段库。
3. assets/buildings-city/manifest.json及五区strict/hypothesis.json、GLB、瓦片关联JSON：{q['published_outline_entities']:,}非占位轮廓；默认严格，hypothesis只是明示单位/基底假设且无封盖，不是可信主体。
4. 两个同管线真实样区assets/buildings-pilot-lower、buildings-pilot-midtown，可直接用作快速验证。buildings.html为同工程检视页，index/terrain原入口保留。
5. data/manifests/stage4的来源/表示政策/生成文件SHA，reports/stage4的219对象审计、height-gaps、overlaps、重建与浏览器证据。

优先补足：HEIGHT_ROOF的foot种类；俯视轮廓与墙基线/悬挑关系；单楼基底及垂直基准；原DEM generic NAD83与NAD83(2011)冲突；按年代核对的旧模型GUID↔当前实体关系；真正取得并过滤的屋顶点云与部件高度。未有证据不生成默认高度、统一平屋顶或虚构细节。PLUTO工业地块/最高楼层不传播给每栋楼。未知区域不随机补齐。

抽查有真实内洞与高低源数值，复杂屋顶可靠证据0、真实工业用途独立确认0、现实实测控制0。纯计算误差不能替代现实准确度。所有当前可信主体/屋顶/立面比例0的缺口继续保留。

重建与验收命令见README。大库/全市瓦片/ZIP本地保留，Git只跟踪源码、样本和清单；克隆不等于已取得所有大文件。当前不自动进入下一阶段。

## 历史：阶段3接续

"""
 n=ROOT/'docs/NEXT_STEPS.md';n.write_text(nexttext+n.read_text())
 print('BUILDING_QUALITY_HANDOFF_WRITTEN',flush=True)
if __name__=='__main__':main()
