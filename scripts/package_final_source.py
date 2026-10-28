"""Development source and real compact inputs, not a misleading offline rebuild of missing raw."""
import json,zipfile,subprocess
from nyc.download import ROOT,sha,atomic_json,now


def main():
    out=ROOT/'reports/final-delivery';files={}
    tracked=subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
    for name in tracked:
        p=ROOT/name
        if not p.is_file()or name in ['reports/stage10/source-package.json','reports/stage10/source-package.log','reports/stage10/source-package-final.log','reports/stage10/delivery-catalog.json']or name.startswith(('reports/final-delivery/','reports/stage10/soak/'))or p.suffix in ['.zip','.tmp','.png']and name.startswith('reports/'):continue
        if p.stat().st_size>32*1024**2:continue
        files['source/'+name]=p
    for p in (ROOT/'reports/stage10').rglob('*'):
        if p.is_file()and p.name not in ['source-package.json','source-package.log','source-package-final.log','delivery-catalog.json']and p.suffix in ['.json','.csv','.md','.log','.gz']and p.stat().st_size<32*1024**2 and'cycles.jsonl'not in p.name:files['source/'+str(p.relative_to(ROOT))]=p
    # Explicitly retain newly acquired bounded, public administrative inputs.
    for p in (ROOT/'data/raw/stage10').rglob('*'):
        if p.is_file():files['source/'+str(p.relative_to(ROOT))]=p
    target=out/'nyc-developer-source.zip'
    payload=[{'path':n,'bytes':p.stat().st_size,'sha256':sha(p)}for n,p in sorted(files.items())]
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4)as z:
        for name,p in sorted(files.items()):z.write(p,name)
        z.writestr('REBUILD_SCOPE.txt','源码、锁文件、小样本与清单。全部已发布五区资源在六个runtime分包；复制app/datasets到source/assets后可离线重建页面。全量原始GIS/SQLite/研究原件保留工作区，非此源码包内容。完整源数据重采需网络及足够磁盘；不声称该包独立重建所有源证据。详见source/docs/REBUILD.md。\n')
        z.writestr('SOURCE_FILES.json',json.dumps({'files':payload,'source_archive_sha_is_outside_only':True},ensure_ascii=False,indent=2))
    with zipfile.ZipFile(target)as z:
        if z.testzip():raise ValueError('source CRC failed')
        import hashlib
        for f in payload:
            if hashlib.sha256(z.read(f['path'])).hexdigest()!=f['sha256']:raise ValueError('source payload SHA mismatch '+f['path'])
    row={'at_utc':now(),'name':target.name,'bytes':target.stat().st_size,'sha256':sha(target),'files':len(files),'actual_crc_and_every_payload_sha_verified':True,'complete_raw_offline_rebuild':False,'all_published_runtime_resources_delivered_separately':True}
    atomic_json(ROOT/'reports/stage10/source-package.json',row)
    with(out/'SHA256SUMS').open('a')as f:f.write(row['sha256']+'  '+row['name']+'\n')
    print('SOURCE_PACKAGE',row['bytes'],len(files))


if __name__=='__main__':main()
