# GitHub发布与更新

仓库：https://github.com/CloudAis/NY-City-Model

版本：https://github.com/CloudAis/NY-City-Model/releases/tag/v0.1.0-evidence-20261028

# 纽约五区来源轮廓与检查工具 · 部分完成版

源码/验收基线：`717a2e4`。保留来源、坐标、原模型和真实性缺口；本次不新增建模或改动验证过的资源。

## 实际覆盖

- 五区1,082,964来源记录，发布1,082,930非占位轮廓；来源抓取版本2026-10-27-city，不是建筑观测年份。
- 两个部分地标表示、四块1936历史正面；完整当前精细建筑、可靠全城屋顶/逐立面完成数均0。
- 334来源对象审计检查转换忠实度；独立现实测量0，现实尺寸精度未知。全球高程和当前外观资料仍有缺口。

## 下载与启动

在Assets下载六个`nyc-evidence-*.zip`、delivery-manifest.json与三个Python脚本到同一目录。所有运行资源实际包含在分包中，无需旧版本或在线服务。

```bash
python3 assemble.py --parts-dir . --output nyc-local
python3 nyc-local/start-local.py
# http://127.0.0.1:8080/
```

[全部文件、大小与校验和](https://github.com/CloudAis/NY-City-Model/releases/download/v0.1.0-evidence-20261028/FILES.md) · [SHA256SUMS](https://github.com/CloudAis/NY-City-Model/releases/download/v0.1.0-evidence-20261028/SHA256SUMS) · [操作说明](https://github.com/CloudAis/NY-City-Model/releases/download/v0.1.0-evidence-20261028/START_HERE.md) · [最终回执](https://github.com/CloudAis/NY-City-Model/releases/download/v0.1.0-evidence-20261028/FINAL_RECEIPT.md)

七个ZIP含六个完整运行分包和一个源码ZIP；源码、模型、纹理、Worker、Cesium依赖、局部地形、属性均按现有范围交付。全量原始GIS/大主库/未知许可研究原件没有全部上传，源码再处理范围见仓库docs/REBUILD.md。

## 已执行验证

TypeScript/Vite构建和57规则通过。实际连续浏览30分5秒、33轮，无页面异常/重载；连续测试40次requestfailed未记录原因，不能称零网络失败。最终新目录空缓存禁外网260请求全部成功，实际五区GLB/Worker/拾取/地面/预览通过。软件WebGL仍存在长帧；真机GPU/手机未测。

单文件preview仅局部历史证据与部分体量。HTTP及内容嵌入实测可用；默认file://被测试环境企业策略阻止，普通浏览器双击待测。完整现实外观目标未通过，因此以**Prerelease**发布。

原六包、源码ZIP与资源校验和保持不变；GitHub版FILES.md改为可点击下载链接，相应SHA256SUMS目录行已更新。项目未擅自添加新的开源许可，原第三方/NYC/NYS/LOC署名保留，未知许可原图/PDF不作离线纹理分发。
