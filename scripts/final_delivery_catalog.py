"""Publish links and hashes for the actual local artifacts, never placeholder downloads."""
import json,shutil
from nyc.download import ROOT,sha,atomic_json,now


def main():
    out=ROOT/'reports/final-delivery';m=json.loads((out/'delivery-manifest.json').read_text());s=json.loads((ROOT/'reports/stage10/source-package.json').read_text());browser=json.loads((ROOT/'reports/stage10/package-browser.json').read_text())
    shutil.copy2(ROOT/'reports/DELIVERY_FINAL_APPENDIX.md',out/'FINAL_RECEIPT.md')
    names=[p['name']for p in m['runtime_parts']]+['nyc-developer-source.zip','preview-single.html','delivery-manifest.json','assemble.py','start-local.py','update-local.py','START_HERE.md','FINAL_RECEIPT.md']
    rows=[]
    for name in names:
        p=out/name
        if not p.is_file():raise ValueError('missing actual delivery '+name)
        rows.append({'name':name,'bytes':p.stat().st_size,'sha256':sha(p)})
    assert next(r['sha256']for r in rows if r['name']==s['name'])==s['sha256']
    text='''# 实际交付文件

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
'''
    for r in rows:text+=f"|[{r['name']}]({out/r['name']})|{r['bytes']:,}|{r['sha256']}|\n"
    (out/'FILES.md').write_text(text)
    checksum_files=[p for p in sorted(out.iterdir())if p.is_file()and p.name!='SHA256SUMS'and not p.name.endswith('.tmp')]
    (out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.name+'\n'for p in checksum_files))
    atomic_json(ROOT/'reports/stage10/delivery-catalog.json',{'at_utc':now(),'files':rows,'runtime_compressed_bytes':sum(r['bytes']for r in rows if r['name'].startswith('nyc-evidence-')),'runtime_file_count':len(m['files']),'runtime_bytes':m['runtime_uncompressed_bytes'],'final_independent_directory':browser['assembled_root'],'fresh_cache_requests':len(browser['requests']),'fresh_cache_failed_requests':browser['failedRequests'],'fresh_cache_bad_http':[r for r in browser['responses']if r['status']>=400],'actual_five_borough_glb':True,'outside_requests':browser['external_requests'],'complete_real_city_exteriors':False,'source_crc_and_payload_sha_verified':s['actual_crc_and_every_payload_sha_verified']})
    print('CATALOG',len(rows),'actual linked artifacts; standalone bytes',m['runtime_uncompressed_bytes'])


if __name__=='__main__':main()
