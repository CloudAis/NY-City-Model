# 实际交付文件

当前部分完成的真实数据工程。**完整运行资产不等于完成五区真实建筑外观。** 完整当前精细建筑0；五区1,082,930来源轮廓，2个部分地标表示，4个1936历史正面片段。现实测量精度未知。

下载六个nyc-evidence ZIP及manifest/三个Python脚本到同一目录，不需要旧包。运行资源解压约6.2GiB，建议8GiB以上可用空间。脚本/清单是辅助文件，实际模型与资源已在分包中。

```bash
python3 assemble.py --parts-dir . --output ./nyc-local
python3 nyc-local/start-local.py --port 8080
# http://127.0.0.1:8080/index.html
```

单文件preview只含真实局部历史/部分体量。默认file被本机企业策略阻止；HTTP及离线嵌入通过。开发源码ZIP不含全部原始GIS/大主库，完整运行数据在六分包，原始全量输入仍保留原工作区。详细说明见START_HERE.md、docs/REBUILD.md和最终验收报告。

|实际文件|字节|SHA256|
|---|---:|---|
|[nyc-evidence-common.zip](/workspace/nyc-3d-html/reports/final-delivery/nyc-evidence-common.zip)|215,234,523|82903f620423d47d482549ae1ceb4a2f0681c31197e115400fa254ba71ad102c|
|[nyc-evidence-manhattan.zip](/workspace/nyc-3d-html/reports/final-delivery/nyc-evidence-manhattan.zip)|71,692,556|455fe1357cb6a374aa9e3e27212d72525d5fca3eb16396fa792bb32c3601c7b3|
|[nyc-evidence-brooklyn.zip](/workspace/nyc-3d-html/reports/final-delivery/nyc-evidence-brooklyn.zip)|363,533,864|b40d06b964486a1159fab9e332394d02d7434c39ec3bfbf559c736caf120b125|
|[nyc-evidence-queens.zip](/workspace/nyc-3d-html/reports/final-delivery/nyc-evidence-queens.zip)|497,719,582|46cc967471af3c6249e4a94c6493197908e715921c387c3b64d3805666483c0a|
|[nyc-evidence-bronx.zip](/workspace/nyc-3d-html/reports/final-delivery/nyc-evidence-bronx.zip)|136,771,932|90733c88146dacb749f560da8739ab0021c8cc68c93af58bcdca9a3d9067b12d|
|[nyc-evidence-staten-island.zip](/workspace/nyc-3d-html/reports/final-delivery/nyc-evidence-staten-island.zip)|163,016,737|9441d9d2b98626c5181fa7e250ebb88aa2d1a7deea8159e39bcc65fbfd036bd2|
|[nyc-developer-source.zip](/workspace/nyc-3d-html/reports/final-delivery/nyc-developer-source.zip)|61,530,580|ff0647dbd742b71e211ac60861fc40e05dd249778c7e6ca3054505f246fb7a01|
|[preview-single.html](/workspace/nyc-3d-html/reports/final-delivery/preview-single.html)|1,429,325|5c9b4d5c4529113f4820c9d1eedc2d63708aa569ddbfd8284caf356da0247780|
|[delivery-manifest.json](/workspace/nyc-3d-html/reports/final-delivery/delivery-manifest.json)|6,671,918|9307c95280e81ccdd17a6637c7d8fa3fbacdc7d76aca85ae56f20a9f120dc71e|
|[assemble.py](/workspace/nyc-3d-html/reports/final-delivery/assemble.py)|2,774|9f2e22c4800202156b797e4ccd3d00cd2a0a43cb1f62f21a3fbe48daf8a0c41e|
|[start-local.py](/workspace/nyc-3d-html/reports/final-delivery/start-local.py)|1,277|73a3fc94c09e48bce35da6a0e0fd6f5a34539e827b6f6a1c80cdc19daf32ad3a|
|[update-local.py](/workspace/nyc-3d-html/reports/final-delivery/update-local.py)|7,787|19c4404c79c77085c07a8d4e5c84019e277ab882164bb0dd2845a531f8bf2f0a|
|[START_HERE.md](/workspace/nyc-3d-html/reports/final-delivery/START_HERE.md)|4,985|86f623a1b57541c7fc88a2e86ec4d0fd4097d2665c85db2aa000cf52f78661a8|
|[FINAL_RECEIPT.md](/workspace/nyc-3d-html/reports/final-delivery/FINAL_RECEIPT.md)|3,150|90ee126607f847ada26f4f0605b7f5aa1ae1179b3dab3db94386bff3b335b5d1|
