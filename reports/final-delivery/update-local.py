#!/usr/bin/env python3
"""Apply/rollback checksummed DATA-only patches while the local server is stopped.

A building change republishes its complete owner tile, including unchanged neighbours.
This is a local journaled update, not a concurrent multi-file server transaction.
"""
import argparse,hashlib,json,zipfile,struct,shutil,os,datetime
from pathlib import Path,PurePosixPath


def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        while b:=f.read(1024*1024):h.update(b)
    return h.hexdigest()


def write(p,data):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp')
    t.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');os.replace(t,p)


def safe(name):
    q=PurePosixPath(name)
    if q.is_absolute()or'..'in q.parts or not name.startswith('app/datasets/')or'\\'in name:raise ValueError('only safe app/datasets paths can be patched')
    return name


def ids(p):
    if p.suffix=='.glb':
        with p.open('rb')as f:
            magic,version,total,n,kind=struct.unpack('<4sIIII',f.read(20));d=json.loads(f.read(n))
        if(magic,version,total,kind)!=(b'glTF',2,p.stat().st_size,0x4e4f534a):raise ValueError('invalid GLB')
    elif p.suffix=='.json':d=json.loads(p.read_text())
    else:return set()
    # Tile metadata's authoritative objects must agree with its feature-ID map.
    if isinstance(d,dict)and isinstance(d.get('objects'),list):
        physical={x['id']for x in d['objects']}
        if 'feature_ids'in d and set(d['feature_ids'])!=physical:raise ValueError('stable IDs removed or metadata feature map inconsistent')
        return physical
    found=set()
    def visit(v):
        if isinstance(v,dict):
            for k,x in v.items():
                if k=='id'and isinstance(x,str)and x.startswith('nyc:footprints:'):found.add(x)
                elif k=='feature_ids'and isinstance(x,list):found.update(x)
                else:visit(x)
        elif isinstance(v,list):
            for x in v:visit(x)
    visit(d);return found


def apply(root,archive):
    current=json.loads((root/'delivery-manifest.json').read_text());known={f['path']:f for f in current['files']}
    with zipfile.ZipFile(archive)as z:
        m=json.loads(z.read('patch.json'));key=m['id']
        if not key or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'for c in key):raise ValueError('invalid patch id')
        if m['scope']not in ['building','tile','borough']or not m.get('source_version')or not m.get('provenance'):raise ValueError('scope/source/history missing')
        history=root/'.updates'/key
        if history.exists():raise ValueError('patch id already exists; do not replay')
        if any(json.loads(p.read_text()).get('state')not in ['committed','rolled_back']for p in (root/'.updates').glob('*/journal.json')):raise ValueError('resolve or rollback an incomplete patch first')
        rows=m['files'];names=[safe(f['path'])for f in rows]
        if len(names)!=len(set(names)):raise ValueError('duplicate file path')
        if set(z.namelist())!={'patch.json',*names}:raise ValueError('archive contains undeclared files')
        # Validate every old file against the installed manifest BEFORE any mutation.
        for f in rows:
            p=root/f['path'];old=f['old_sha256']
            if old is None:
                if p.exists()or f['path']in known:raise ValueError('new file already exists')
            elif f['path']not in known or known[f['path']]['sha256']!=old or not p.is_file()or p.is_symlink()or sha(p)!=old:raise ValueError('old SHA mismatch: '+f['path'])
        history.mkdir(parents=True);stage=history/'staged'
        try:
            affected=set(m.get('stable_ids',[]));retained=set()
            for f in rows:
                data=z.read(f['path']);p=stage/f['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
                if len(data)!=f['bytes']or sha(p)!=f['sha256']:raise ValueError('new SHA/size mismatch')
                before=ids(root/f['path'])if f['old_sha256']else set();after=ids(p)
                if not before<=after:raise ValueError('stable IDs removed: republish complete owner tile, not a one-object file')
                retained|=after
            if affected and not affected<=retained:raise ValueError('affected stable IDs absent from actual replacement data')
            shutil.copy2(root/'delivery-manifest.json',history/'manifest-before.json');write(history/'patch.json',m)
            write(history/'journal.json',{'state':'prepared','applied':[],'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
            applied=[]
            try:
                for f in rows:
                    p=root/f['path'];backup=history/'before'/f['path']
                    if p.exists():backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,backup)
                    applied.append(f['path']);write(history/'journal.json',{'state':'applying','applied':applied})
                    p.parent.mkdir(parents=True,exist_ok=True);os.replace(stage/f['path'],p)
                    known[f['path']]={**known.get(f['path'],{'license_id':f.get('license_id','patch_provenance_required')}),**{k:f[k]for k in ['path','bytes','sha256']}}
                current['files']=list(known.values());current['runtime_uncompressed_bytes']=sum(f['bytes']for f in known.values());current.setdefault('updates',[]).append({'id':key,'scope':m['scope'],'source_version':m['source_version'],'provenance':m['provenance']})
                write(root/'delivery-manifest.json',current);write(history/'journal.json',{'state':'committed','applied':applied})
            except BaseException:
                rollback(root,key,allow_prepared=True);raise
        except BaseException:
            if history.exists()and not(history/'journal.json').exists():shutil.rmtree(history)
            raise
    return key


def rollback(root,key,allow_prepared=False):
    if not key or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'for c in key):raise ValueError('invalid patch id')
    history=root/'.updates'/key;j=json.loads((history/'journal.json').read_text());m=json.loads((history/'patch.json').read_text())
    if j['state']=='rolled_back':raise ValueError('already rolled back')
    current=json.loads((root/'delivery-manifest.json').read_text())
    if j['state']=='committed'and (not current.get('updates')or current['updates'][-1]['id']!=key):raise ValueError('rollback must be in reverse application order')
    if not allow_prepared:
        expected={f['path']:f for f in m['files']}
        for name in j['applied']:
            actual=sha(root/name)if(root/name).is_file()else None
            allowed={expected[name]['sha256']}
            # Journal is written BEFORE replace: a killed process can leave old bytes.
            if j['state']in ['prepared','applying']:allowed.add(expected[name]['old_sha256'])
            if actual not in allowed:raise ValueError('file changed after patch; preserve it before rollback')
    for name in reversed(j['applied']):
        b=history/'before'/name;p=root/name
        if b.exists():shutil.copy2(b,p)
        elif p.exists():p.unlink()
    shutil.copy2(history/'manifest-before.json',root/'delivery-manifest.json');write(history/'journal.json',{**j,'state':'rolled_back'})


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--apply',type=Path);g.add_argument('--rollback');a=p.parse_args();root=a.root.resolve()
    if a.apply:print('APPLIED',apply(root,a.apply))
    else:rollback(root,a.rollback);print('ROLLED_BACK',a.rollback)


if __name__=='__main__':main()
