# 20张实际截图验证记录

- 运行来源：原发布源码64cde3fe8d378612eed762db90169515bd26b3ab；独立已组装运行目录，不使用源码目录资源回退。
- 实际启动：`python3 /tmp/nyc-final-release-20261028/start-local.py --port 8080`，仅监听127.0.0.1。
- 脚本语法：`node --check scripts/capture_published_views.mjs`，通过。
- 实际抓拍：`node scripts/capture_published_views.mjs`，20/20导出完成。先单独试拍1张，再运行正式20张；试拍不混入交付。
- 实际浏览器：Chromium154.0.8037.57，无头SwiftShader/WebGL2；1600×1000、DPR1、high原始精度，自动画质关闭，固定中性光。
- 实际输出：五区各4张，10个预设各2个不同相机角度，20个不同SHA256；1280×912场景画布加70px真实导出署名条，最终1280×982，20张合计7,487,630字节。
- 每张真实相机ECEF米坐标、朝向、目标经纬度、加载层和UTC抓拍时间见manifest.json。高度仅相对展示椭球。
- 数据等待：本区建筑GLB和道路图层实际解析且可见，队列无待处理项连续4次采样后才导出；不是按计时器假装加载完成。
- 实际请求：575个本地响应，0坏HTTP、0requestfailed、0外部请求、0页面错误、0控制台错误；新上下文、HTTP缓存禁用、外网阻断。不是所有数据瓦片的全量网络验收。
- 每张PNG实际使用Pillow解码校验，尺寸与SHA256全部通过；全部20张缩略总览已观察，首张另以原图观察。没有宣称逐栋现实准确性或完成精细外观。
- 10个入口/数据清单SHA在拍摄前后相同；没有改变建筑模型、原始资料、七个交付ZIP或数据分支。
- 已观察限制：来源轮廓没有可信楼体高度；道路/桥梁是投影，水面有观察窗口裁剪边界，环境仅已取得局部窗口；截图保留这些缺口。
- 原文件位于当前目录，`SHA256SUMS`列20张PNG；ZIP另列于`ZIP_SHA256SUMS`。这份记录是新抓拍，不改写之前阶段的测试证据。

复现时先启动相同已组装运行包，再运行：

```bash
NYC_CAPTURE_ROOT=/path/to/nyc-local NYC_CAPTURE_OUTPUT=/tmp/nyc-new-20-views node scripts/capture_published_views.mjs
```

脚本拒绝覆盖已有manifest.json，保留既有抓拍记录；新拍摄因浏览器/设备不同不承诺PNG逐字节一致。
