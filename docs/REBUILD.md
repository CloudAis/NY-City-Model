# 重建输入与命令

固定同一工程，不生成替代演示。依赖锁：Node24.19.0、npm11.9.0，Cesium1.146.0、Vite8.3.5、TypeScript7.0.2、playwright-core1.56.1；Python3.12.14，GIS版本见`requirements-lock.txt`。图像历史处理另用系统Pillow11.1.0/numpy2.2.4，GDAL CLI；不是仅安装Node即可从原始GIS重建。

## 重建浏览器程序

解压源码，保留锁文件。依赖已缓存时可离线构建；新机器首次`npm ci`需要注册表或自行准备完整npm缓存，不把它说成运行包离线失败。

```bash
npm ci
npm run check
npm run build
npm run dev
# 开发 http://127.0.0.1:5180/release.html
```

源码包保留小样本；要在克隆目录重建**当前全部发布资源**，先组装完整六包，再把`nyc-local/app/datasets/`全部复制到源码`assets/`（目录内文件对应同名）；它们是已经处理的真实资源，无须重新抓取。`npm run build`把assets与Cesium依赖复制至dist，再用README的127.0.0.1 HTTP命令启动。不要用旧浏览器缓存弥补缺目录。

## 重新处理来源

全市原库`data/processed/city/buildings.sqlite`、`data/processed/building-stage4/city/associations.sqlite`、各原始page/receipt、context.gpkg、PLUTO、2014历史3dm及DEM/地理参考完整留在工作区。SHA/实际路径见阶段10input-lock及阶段9/10input-integrity。源码包未复制多GiB主库和未知再分发权的研究原件；**不声称源码ZIP能够独立离线重建全部原始证据**。需要完整来源再处理时保留这些本地输入，或按README阶段2命令重新获取官方资源并保存新抓取版本。

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt
# 读取真实主库，不覆盖raw；每次不同输入/处理版本用新work/output
.venv/bin/python scripts/build_buildings.py --id nyc:footprints:doitt:1114961 --work data/intermediate/rebuild-id-work --output data/intermediate/rebuild-id
.venv/bin/python scripts/build_buildings.py --borough manhattan --tile 597 121 --work data/intermediate/rebuild-tile-work --output data/intermediate/rebuild-tile
.venv/bin/python scripts/build_buildings.py --borough manhattan --work data/intermediate/rebuild-manhattan-work --output data/intermediate/rebuild-manhattan
```

单ID是独立检查结果，**不能覆盖全owner瓦片**。本轮实际重建单ID1来源记录、完整owner20记录，GLB与原包字节一致；实际全曼哈顿重建索引45,172条，未重新发布该区全部GLB。已发布全市原始几何仍未改。更新所有相关catalog/metadata/manifest并验证完整ID集合，再创建增量补丁。

## 重现最终检查

```bash
npm test
npm run build
.venv/bin/python scripts/final_census.py
.venv/bin/python scripts/final_review.py
.venv/bin/python scripts/acquire_final_evidence.py
.venv/bin/python scripts/final_evidence_report.py
NYC_REPORT_DIR=reports/stage10/inspection NYC_OBSERVATION_REPORT=reports/stage10/observations.json node tests/inspection-browser.mjs
NYC_REPORT_DIR=reports/stage10/foundation node tests/foundation-browser.mjs
NYC_REPORT_DIR=reports/stage10/landmarks node tests/landmarks-browser.mjs
NYC_REPORT_DIR=reports/stage10/facades node tests/facades-browser.mjs
node tests/final-preview.mjs
NYC_REPORT_DIR=reports/stage10/soak node tests/performance/soak.mjs
```

连续测试需真实30分钟，不能把`NYC_SOAK_SECONDS`缩短当完整通过。重跑用新报告目录，避免把历史运行混为本轮；部分早期脚本默认写历史目录，应显式传上述report环境变量。浏览器脚本需要允许本地监听、Chromium和WebGL2。数据网络抓取脚本只在实际需要更新资料时执行，不是启动前提；动态源一致性限制见独立证据清单。

资源锁定后：`final_resource_audit.py`→`package_final.py`→新目录`assemble.py`→`tests/final-package.mjs`→`package_final_source.py`。原始资料只追加；新版本变化不能覆盖旧page或静默改稳定ID。
