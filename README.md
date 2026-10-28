# NYC离线运行资源 · 部分完成版

本分支存放真实的全部七个ZIP（六个运行分包+源码），为适应Git单文件大小限制按32MiB分块；原ZIP/模型/纹理字节不变。不使用Git LFS，无云服务或付费API启动前提。完整当前精细建筑0；五区1,082,930来源轮廓、2个部分地标、4历史正面。

**READY.json未出现时表示上传尚未完成。** join-packages.py会拒绝不完整文件，不以下载脚本或占位楼群冒充缺失数据。


```bash
python3 join-packages.py --verify-only
python3 join-packages.py --output packages
python3 packages/assemble.py --parts-dir packages --output nyc-local
python3 nyc-local/start-local.py
# http://127.0.0.1:8080/
```

建议12GiB以上可用空间。初次下载GitHub需要网络；下载完整后上述拼接、校验、HTTP运行均无需外网。多文件file://不受支持，单文件preview的默认file导航在原测试环境被企业策略拦截。

[开发源码与报告](https://github.com/CloudAis/NY-City-Model) · [文件清单](FILES.md) · [原始逐文件运行清单](delivery-manifest.json)。完整原始GIS/大库/未知许可研究原件并未全部上传；这不影响本分支已经实际提供的全部已发布运行资源。

运输校验可执行 `python3 test-join.py`：4项检查覆盖真实启动文件还原、损坏拒绝、缺少READY及已有输出文件保护；全部七个ZIP另已实际完整拼回并逐SHA核对。
