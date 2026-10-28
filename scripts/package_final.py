"""Standalone current runtime parts. Every city resource is in a real archive, no old base."""
import json,zipfile,shutil,hashlib,argparse
from pathlib import Path
from nyc.download import ROOT,sha,atomic_json,now

BOROUGHS=['manhattan','brooklyn','queens','bronx','staten-island']


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reuse-city',action='store_true');args=parser.parse_args()
    app=ROOT/'dist';out=ROOT/'reports/final-delivery';out.mkdir(parents=True,exist_ok=True)
    audit=json.loads((ROOT/'reports/stage10/resource-audit.json').read_text())
    if audit['errors']:raise ValueError('resource audit not clean')
    original=json.loads((ROOT/'data/manifests/stage10/runtime-files.json').read_text());basis={f['path']:f['license_id']for f in original['files']}
    files={}
    for p in sorted(app.rglob('*')):
        if not p.is_file():continue
        name='app/'+str(p.relative_to(app));files[name]=p
    # Entry makes evidence gaps visible; retain original source inspector separately.
    files['app/index.html']=app/'release.html';files['app/source-audit.html']=app/'source-audit.html'
    for folder in ['docs','data/manifests']:
        for p in sorted((ROOT/folder).rglob('*')):
            if p.is_file():files['app/release-notes/'+str(p.relative_to(ROOT))]=p
    for p in sorted((ROOT/'reports').glob('*.md')):files['app/release-notes/reports/'+p.name]=p
    # Keep compact actual final receipts available offline; archive self hashes stay outside.
    for p in sorted((ROOT/'reports/stage10').glob('*')):
        if p.is_file()and p.suffix in ['.json','.csv']and p.stat().st_size<2*1024**2 and p.name not in ['package.json','source-package.json']:
            files['app/release-notes/reports/stage10/'+p.name]=p
    for name in ['README.md','THIRD_PARTY_NOTICES.md']:files['app/release-notes/'+name]=ROOT/name
    entries=[{'path':name,'bytes':p.stat().st_size,'sha256':sha(p),'license_id':basis.get(name,'project_generated_audit_and_original_source_notices')}for name,p in files.items()]
    entry_map={f['path']:f for f in entries};groups={'common':{},**{b:{}for b in BOROUGHS}}
    for name,p in files.items():
        parts=Path(name).parts;b=parts[3]if parts[:3]==('app','datasets','buildings-city')and len(parts)>3 and parts[3]in BOROUGHS else'common';groups[b][name]=p
    archives=[];previous=json.loads((out/'delivery-manifest.json').read_text())if args.reuse_city and(out/'delivery-manifest.json').exists()else None
    for b,group in groups.items():
        name='nyc-evidence-'+b+'.zip';target=out/name;tmp=target.with_suffix('.zip.tmp')
        if b!='common'and previous:
            old=next((x for x in previous['runtime_parts']if x['name']==name),None);old_files={f['path']:(f['bytes'],f['sha256'])for f in previous['files']if f['path'].startswith('app/datasets/buildings-city/'+b+'/')};new_files={n:(entry_map[n]['bytes'],entry_map[n]['sha256'])for n in group}
            if old and old_files==new_files and target.is_file()and sha(target)==old['sha256']:
                archives.append(old);print('REUSED_VERIFIED_UNCHANGED_CITY_ARCHIVE',b,flush=True);continue
        with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4,allowZip64=True)as z:
            for path,p in group.items():z.write(p,path)
        with zipfile.ZipFile(tmp)as z:
            if z.testzip():raise ValueError('CRC failed '+name)
            for path,p in group.items():
                if hashlib.sha256(z.read(path)).hexdigest()!=entry_map[path]['sha256']:raise ValueError('archive SHA mismatch '+path)
        tmp.replace(target);archives.append({'name':name,'bytes':target.stat().st_size,'sha256':sha(target),'files':len(group),'uncompressed_bytes':sum(p.stat().st_size for p in group.values())});print('PACKAGED',b,archives[-1]['bytes'],len(group),flush=True)
    manifest={'schema_version':10,'kind':'standalone_current_published_evidence_runtime_NOT_complete_city_exterior','at_utc':now(),'source_version':'2026-10-27-city','old_base_required':False,'entry':'app/index.html','complete_current_fine_buildings':0,'runtime_parts':archives,'runtime_uncompressed_bytes':sum(f['bytes']for f in entries),'files':entries,'license_classes':{**original['license_classes'],'project_generated_audit_and_original_source_notices':{'basis':'project audit text and original source metadata links/notices; no unknown-rights reference originals'}},'assembly':'six actual local archives; all city strict/hypothesis/catalog/metadata resources retained; no fallback to workspace or web','checksum_limit':'SHA integrity only, not a signature or independent statement of authenticity'}
    atomic_json(out/'delivery-manifest.json',manifest)
    for p in (ROOT/'delivery').glob('*.py'):shutil.copy2(p,out/p.name)
    shutil.copy2(ROOT/'docs/DELIVERY.md',out/'START_HERE.md');shutil.copy2(ROOT/'preview-single.html',out/'preview-single.html')
    checks=[*archives,*[{'name':p.name,'sha256':sha(p)}for p in sorted(out.iterdir())if p.is_file()and p.name not in [a['name']for a in archives]and p.name not in ['SHA256SUMS','nyc-developer-source.zip']]]
    (out/'SHA256SUMS').write_text(''.join(f"{r['sha256']}  {r['name']}\n"for r in checks))
    atomic_json(ROOT/'reports/stage10/package.json',{'at_utc':now(),'runtime_parts':archives,'runtime_file_count':len(entries),'runtime_uncompressed_bytes':manifest['runtime_uncompressed_bytes'],'manifest_sha256':sha(out/'delivery-manifest.json'),'crc_and_actual_archive_payload_sha_verified':True,'complete_runtime':True,'complete_city_exteriors':False})
    print('COMPLETE_RUNTIME',len(entries),manifest['runtime_uncompressed_bytes'],flush=True)


if __name__=='__main__':main()
