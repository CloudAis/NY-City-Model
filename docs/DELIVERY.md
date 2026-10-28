# 第十阶段交付与启动

这是**部分完成的真实数据工程**，不是五区完整建筑外观复刻。完整本地运行包包含当前全部已发布五区资源；“运行资源完整”不代表建筑主体、屋顶、立面或现实精度已完成。统计版本 `2026-10-27-city`，审查日期2026-10-28（Asia/Singapore），来源观测日仍单独保留。

## 六个实际运行分包

在 `reports/final-delivery/` 下载/保留以下文件到同一目录：

- `nyc-evidence-common.zip`：页面、脚本、Cesium/Worker/CSS、许可、全局索引、环境、地形、地标及历史立面片段、单文件预览、文档。
- `nyc-evidence-manhattan.zip`、`nyc-evidence-brooklyn.zip`、`nyc-evidence-queens.zip`、`nyc-evidence-bronx.zip`、`nyc-evidence-staten-island.zip`：对应来源分区的全部严格轮廓、可选假设包络、逐瓦片属性和目录。
- `delivery-manifest.json`、`SHA256SUMS`、`assemble.py`、`start-local.py`、`update-local.py`。

不需要stage4/7/8/9旧包、不需要项目工作区、不需要云凭据。校验和及实际文件大小以 `delivery-manifest.json` 和 `reports/stage10/package.json` 为准。不要只下载common后声称取得五区运行包。完整解压约6.2GiB，建议预留8GiB以上；压缩包另占磁盘。

## 实际启动方法

需要Python3（仅标准库），GPU浏览器需WebGL2。进入分包目录：

```bash
python3 assemble.py --parts-dir . --output ./nyc-local
python3 nyc-local/start-local.py --port 8080
```

打开 **http://127.0.0.1:8080/index.html**。启动器只绑定127.0.0.1；Ctrl+C停止。组装器拒绝覆盖非空目录，检查所有分包SHA、ZIP路径/CRC及实际解压文件SHA。已有组装结果可用：

```bash
python3 assemble.py --parts-dir . --output ./nyc-local --verify-only
```

也可按完整清单解压六包至同一个新目录，执行：

```bash
python3 -m http.server 8080 --bind 127.0.0.1 --directory nyc-local/app
```

运行时不需要外网。首次开发依赖安装/重新获取源数据需要网络，与运行包不同。多文件Cesium工程通过本地HTTP加载，**不承诺file://双击**。

## 入口与操作

`index.html`先展示覆盖与未知，`inspection.html`为五区检查器；另有`source-audit.html`、`terrain.html`、`buildings.html`、`landmarks.html`、`facades.html`。鼠标旋转、平移、滚轮缩放；WASD/QE自由飞行，Esc取消；触控旋转及双指平移缩放。地面模式仅开放八个有真实2017DEM和保守地面碰撞的局部范围，不能在未配准的全市自由贴地漫游，也没有虚构室内/桥面碰撞。

三档画质见 `QUALITY.md`。严格证据模式默认不显示未知高度实体；可选高度假设包络不算可信楼体。全城概览不会同时加载所有细节，放大后按局部请求体加载；所有7,383严格叶和原始几何仍在包内。页面和导出截图保留署名。

## 独立单文件

`preview-single.html`内嵌真实原GLB与四张历史派生纹理，无外部依赖。范围为Grove Street4—10号四块**1936历史正面片段**，另可切换OneWTC**部分文献体量**；完整现状精细建筑数0。它不是完成街段或全纽约模型，未知背面/屋顶/入口不补造。

本环境实际HTTP和离线内容嵌入通过；默认file://导航被Chromium企业策略 `ERR_BLOCKED_BY_ADMINISTRATOR` 拦截，未绕过策略。可使用上述本地HTTP方式。无此策略的普通浏览器双击仍待实际验证。WebGL2缺失会显示明确错误并结束加载。嵌入宿主需允许内联脚本、data图像和WebGL，禁止脚本的沙箱不受支持。

## 数据和许可

完整来源清单见 `data/manifests/`；每个运行文件在交付清单中有SHA、字节数和许可依据分类。保留Cesium及各第三方notice、NYC/NYS来源、LOC HABS NY-449政府原照片/图纸署名。未知使用权的2024正射、原研究PDF/照片、商业街景和商业实景瓦片不进入离线包。代码没有被擅自赋予新的开源许可证；取得网页不等于取得全部第三方图像再分发权。

## 开发与更新

另有 `nyc-developer-source.zip`：源码、锁文件、脚本、配置、规则/浏览器测试、文档、小样本和新取得的DOB行政证据。大原始GIS、全量SQLite、历史3dm原件仍完整保存在原工作区，未因打包删除；它们不是源码包中的全部重建输入。离线页面重建和完整来源再处理区别见 `REBUILD.md`。

增量更新按建筑、完整owner瓦片或行政区准备，保留稳定ID、来源版本/历史，使用 `UPDATE.md` 的工具；必须先停本地服务器。无权据此删除邻楼或把单栋结果直接覆盖整个owner瓦片。

实际验收结果见 `reports/FINAL_ACCEPTANCE.md`、`reports/AUTHENTICITY_FINAL.md` 和 `reports/stage10/`。真机移动、其他浏览器、独立测绘、现状逐立面及全球高程等未完成项不会用截图或计算误差替代。
