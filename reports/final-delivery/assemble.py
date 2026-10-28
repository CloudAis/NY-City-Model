#!/usr/bin/env python3
"""Verify actual local part archives, safely assemble and verify every runtime byte."""
import argparse,json,hashlib,zipfile,shutil,stat,os
from pathlib import Path


def sha(path):
    h=hashlib.sha256()
    with path.open('rb')as f:
        while chunk:=f.read(1024*1024):h.update(chunk)
    return h.hexdigest()


def verify(root,manifest):
    errors=[]
    for f in manifest['files']:
        p=root/f['path']
        if not p.is_file()or p.is_symlink()or p.stat().st_size!=f['bytes']or sha(p)!=f['sha256']:errors.append(f['path'])
    if errors:raise ValueError('运行资源校验失败：'+str(errors[:12]))
    return len(manifest['files'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parts-dir',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--output',type=Path,default=Path('nyc-local'));p.add_argument('--verify-only',action='store_true');a=p.parse_args()
    manifest=json.loads((a.parts_dir/'delivery-manifest.json').read_text());out=a.output.resolve()
    if a.verify_only:print('VERIFIED',verify(out,manifest),'runtime files');return
    if out.exists()and any(out.iterdir()):raise ValueError('输出目录非空；请用新目录或--verify-only，不覆盖已有工作。')
    space=shutil.disk_usage(out.parent if out.parent.exists()else Path.cwd()).free
    if space<manifest['runtime_uncompressed_bytes']+256*1024**2:raise ValueError('磁盘空间不足；完整运行资源约'+str(manifest['runtime_uncompressed_bytes'])+'字节')
    for part in manifest['runtime_parts']:
        file=a.parts_dir/part['name']
        if not file.is_file()or sha(file)!=part['sha256']:raise ValueError('分包缺失或SHA不符：'+part['name'])
    out.mkdir(parents=True,exist_ok=True)
    try:
        for part in manifest['runtime_parts']:
            with zipfile.ZipFile(a.parts_dir/part['name'])as z:
                for info in z.infolist():
                    q=Path(info.filename)
                    if q.is_absolute()or'..'in q.parts or stat.S_ISLNK(info.external_attr>>16):raise ValueError('拒绝不安全压缩路径')
                if z.testzip()is not None:raise ValueError('CRC失败：'+part['name'])
                z.extractall(out)
            print('EXTRACTED',part['name'],flush=True)
        for name in ['start-local.py','update-local.py']:
            if(a.parts_dir/name).is_file():shutil.copy2(a.parts_dir/name,out/name)
        shutil.copy2(a.parts_dir/'delivery-manifest.json',out/'delivery-manifest.json')
        print('ASSEMBLED',verify(out,manifest),'files at',out,flush=True)
    except BaseException:
        # Only this newly created empty output is owned by this invocation.
        shutil.rmtree(out);raise


if __name__=='__main__':main()
