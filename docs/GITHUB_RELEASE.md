# GitHub发布与更新

# 纽约五区来源轮廓与检查工具 · 部分完成版

**源码及完整运行资源已经按原验收范围发布。完整当前精细建筑0，未达到纽约完整外观复刻目标。**

## 实际下载位置

[开发工程与报告](https://github.com/CloudAis/NY-City-Model) · [全部实际运行资源的数据分支](https://github.com/CloudAis/NY-City-Model/tree/offline-packages-v0.1.0-evidence-20261028) · [文件/校验清单](https://github.com/CloudAis/NY-City-Model/blob/main/reports/final-delivery/FILES.md)

**本版本的实际大资源在数据分支，不是下方Release附件。** 七个ZIP（六个运行分包和源码）按32MiB分块保存，总数据约1.5GB；拼接后与原始验收ZIP的SHA256一致。没有只给下载脚本替代数据，也没有随机楼群补齐未知。

```bash
git clone --single-branch --depth 1 --branch offline-packages-v0.1.0-evidence-20261028 https://github.com/CloudAis/NY-City-Model.git nyc-offline
cd nyc-offline
python3 join-packages.py --output packages
python3 packages/assemble.py --parts-dir packages --output nyc-local
python3 nyc-local/start-local.py
# http://127.0.0.1:8080/
```

建议12GiB以上可用空间。下载后拼接、SHA校验、127.0.0.1本地HTTP运行不需外网。多文件file://不受支持；preview单文件默认file导航被测试环境企业策略阻止，HTTP及离线内容嵌入通过。

## 覆盖和验收范围

- 五区1,082,964来源记录，发布1,082,930非占位轮廓；抓取标签2026-10-27-city，不等于观测年份。
- 两个部分地标表示、四块1936历史正面；完整当前精细建筑0，可靠全城屋顶/逐立面仍未完成。
- 334来源对象复核证明源到模型的转换忠实度，独立现实测量0；不能报告现实尺寸精度。
- 构建、类型检查和57规则通过；连续浏览30分5秒无页面异常，但40次requestfailed未保留原因。最终独立目录空缓存禁外网260请求全部成功。软件WebGL仍有长帧，真机GPU/移动未测。

源码验收基线717a2e4，模型、纹理和七个ZIP原字节不变。当前Git分块与还原操作另有本地实际还原校验、服务器Git对象清单核对；详见仓库reports/github-publication.json。

## 发布方式说明

当前环境向uploads.github.com上传附件返回401，API和普通Git写入正常。新增持久Actions发布权限未获自动审批，未启用该方案；采用普通Git资源分支完成发布，不引入Git LFS、付费服务或自动化写权限。原main README历史已合并保留。

原始全量GIS/大库和未知许可研究原件仍在原工作区，未全部上传。NYC/NYS/LOC与Cesium等署名/条款保留，未擅自给项目添加新的开源许可证。
