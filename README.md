# 纽约真实尺度 3D HTML

固定工程：`/workspace/nyc-3d-html`。当前执行阶段1、2；最终五区覆盖，先取得下城/中城真实样区。默认显示官方轮廓，不用虚构楼高或街道。

安装：`npm ci`；`python3 -m venv .venv`；`.venv/bin/pip install -r requirements-lock.txt`。启动 `npm run dev`（5180），构建 `npm run build`。Python测试 `npm test`。浏览器验证 `npm run test:browser`；单文件生成 `.venv/bin/python scripts/single_preview.py`，输出 `reports/nyc-real-sample-preview.html`。企业策略阻止当前浏览器file://；内容已在Chromium完全离线执行验证，未宣称双击已测。

文档入口 [项目说明](docs/PROJECT_BRIEF.md)、[进度](docs/PROGRESS.md)、[下一步](docs/NEXT_STEPS.md)、[缺口](docs/KNOWN_GAPS.md)。原始数据只追加保存，派生物不能覆盖raw。
