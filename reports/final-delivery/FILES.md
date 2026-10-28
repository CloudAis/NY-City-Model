# GitHub完整运行资源

部分完成的真实数据工程；完整当前精细建筑0。全部实际运行ZIP和源码ZIP以32MiB以下分块存于[独立数据分支](https://github.com/CloudAis/NY-City-Model/tree/offline-packages-v0.1.0-evidence-20261028)；普通Git传输，不使用Git LFS，不新增自动化权限。

```bash
git clone --single-branch --depth 1 --branch offline-packages-v0.1.0-evidence-20261028 https://github.com/CloudAis/NY-City-Model.git nyc-offline
cd nyc-offline
python3 join-packages.py --output packages
python3 packages/assemble.py --parts-dir packages --output nyc-local
python3 nyc-local/start-local.py
# http://127.0.0.1:8080/
```

建议预留12GiB以上空间（Git副本、分块、还原ZIP及运行目录）。脚本只在本地拼回已经实际上传的字节，不从服务端再抓纽约数据。还原后ZIP与验收原件SHA相同。

|实际文件|字节|SHA256|
|---|---:|---|
|[FINAL_RECEIPT.md](https://github.com/CloudAis/NY-City-Model/tree/offline-packages-v0.1.0-evidence-20261028/FINAL_RECEIPT.md)|3,150|90ee126607f847ada26f4f0605b7f5aa1ae1179b3dab3db94386bff3b335b5d1|
|[START_HERE.md](https://github.com/CloudAis/NY-City-Model/tree/offline-packages-v0.1.0-evidence-20261028/START_HERE.md)|4,985|86f623a1b57541c7fc88a2e86ec4d0fd4097d2665c85db2aa000cf52f78661a8|
|[assemble.py](https://github.com/CloudAis/NY-City-Model/tree/offline-packages-v0.1.0-evidence-20261028/assemble.py)|2,774|9f2e22c4800202156b797e4ccd3d00cd2a0a43cb1f62f21a3fbe48daf8a0c41e|
|[delivery-manifest.json](https://github.com/CloudAis/NY-City-Model/tree/offline-packages-v0.1.0-evidence-20261028/delivery-manifest.json)|6,671,918|9307c95280e81ccdd17a6637c7d8fa3fbacdc7d76aca85ae56f20a9f120dc71e|
|[nyc-developer-source.zip](https://github.com/CloudAis/NY-City-Model/tree/offline-packages-v0.1.0-evidence-20261028/parts/nyc-developer-source.zip)|61,530,580|ff0647dbd742b71e211ac60861fc40e05dd249778c7e6ca3054505f246fb7a01|
|[nyc-evidence-bronx.zip](https://github.com/CloudAis/NY-City-Model/tree/offline-packages-v0.1.0-evidence-20261028/parts/nyc-evidence-bronx.zip)|136,771,932|90733c88146dacb749f560da8739ab0021c8cc68c93af58bcdca9a3d9067b12d|
|[nyc-evidence-brooklyn.zip](https://github.com/CloudAis/NY-City-Model/tree/offline-packages-v0.1.0-evidence-20261028/parts/nyc-evidence-brooklyn.zip)|363,533,864|b40d06b964486a1159fab9e332394d02d7434c39ec3bfbf559c736caf120b125|
|[nyc-evidence-common.zip](https://github.com/CloudAis/NY-City-Model/tree/offline-packages-v0.1.0-evidence-20261028/parts/nyc-evidence-common.zip)|215,234,523|82903f620423d47d482549ae1ceb4a2f0681c31197e115400fa254ba71ad102c|
|[nyc-evidence-manhattan.zip](https://github.com/CloudAis/NY-City-Model/tree/offline-packages-v0.1.0-evidence-20261028/parts/nyc-evidence-manhattan.zip)|71,692,556|455fe1357cb6a374aa9e3e27212d72525d5fca3eb16396fa792bb32c3601c7b3|
|[nyc-evidence-queens.zip](https://github.com/CloudAis/NY-City-Model/tree/offline-packages-v0.1.0-evidence-20261028/parts/nyc-evidence-queens.zip)|497,719,582|46cc967471af3c6249e4a94c6493197908e715921c387c3b64d3805666483c0a|
|[nyc-evidence-staten-island.zip](https://github.com/CloudAis/NY-City-Model/tree/offline-packages-v0.1.0-evidence-20261028/parts/nyc-evidence-staten-island.zip)|163,016,737|9441d9d2b98626c5181fa7e250ebb88aa2d1a7deea8159e39bcc65fbfd036bd2|
|[preview-single.html](https://github.com/CloudAis/NY-City-Model/tree/offline-packages-v0.1.0-evidence-20261028/preview-single.html)|1,429,325|5c9b4d5c4529113f4820c9d1eedc2d63708aa569ddbfd8284caf356da0247780|
|[start-local.py](https://github.com/CloudAis/NY-City-Model/tree/offline-packages-v0.1.0-evidence-20261028/start-local.py)|1,277|73a3fc94c09e48bce35da6a0e0fd6f5a34539e827b6f6a1c80cdc19daf32ad3a|
|[update-local.py](https://github.com/CloudAis/NY-City-Model/tree/offline-packages-v0.1.0-evidence-20261028/update-local.py)|7,787|19c4404c79c77085c07a8d4e5c84019e277ab882164bb0dd2845a531f8bf2f0a|
