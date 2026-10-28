#!/usr/bin/env python3
"""Restore real locally downloaded package bytes; no network or invented model data."""
import argparse,hashlib,json,shutil
from pathlib import Path,PurePosixPath


def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        while b:=f.read(1024*1024):h.update(b)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=Path('packages'));p.add_argument('--verify-only',action='store_true');a=p.parse_args();root=Path(__file__).resolve().parent
    if not(root/'READY.json').is_file():raise SystemExit('数据上传/下载尚未完整：缺少READY.json，不继续生成半成品。')
    ready=json.loads((root/'READY.json').read_text())
    if sha(root/'bundle-index.json')!=ready['bundle_index_sha256']:raise ValueError('index SHA mismatch')
    m=json.loads((root/'bundle-index.json').read_text())
    if not a.verify_only:
        if a.output.exists()and any(a.output.iterdir()):raise ValueError('use a new empty output directory')
        a.output.mkdir(parents=True,exist_ok=True)
    for r in m['files']:
        if Path(r['name']).name!=r['name']:raise ValueError('unsafe filename')
        chunks=r.get('chunks',[{'path':r.get('path'),'sha256':r['sha256'],'bytes':r['bytes']}]);h=hashlib.sha256();n=0
        out=None if a.verify_only else(a.output/r['name']).open('wb')
        try:
            for c in chunks:
                rel=PurePosixPath(c['path'])
                if rel.is_absolute()or'..'in rel.parts:raise ValueError('unsafe chunk path')
                q=root/str(rel)
                if not q.is_file()or q.is_symlink()or q.stat().st_size!=c['bytes']or sha(q)!=c['sha256']:raise ValueError('missing/corrupt actual bytes: '+str(rel))
                with q.open('rb')as f:
                    while b:=f.read(1024*1024):h.update(b);n+=len(b);out.write(b)if out else None
        finally:
            if out:out.close()
        if n!=r['bytes']or h.hexdigest()!=r['sha256']:raise ValueError('restored package SHA mismatch: '+r['name'])
        print('VERIFIED',r['name'],n,flush=True)
    print('ALL_REAL_PACKAGE_BYTES_VERIFIED',len(m['files']),flush=True)


if __name__=='__main__':main()
