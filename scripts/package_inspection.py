"""Package the tested 7/8 overlay. The unchanged stage4 city is an explicit prerequisite."""
import json,re,zipfile
from pathlib import Path
from urllib.parse import urlparse
from nyc.download import ROOT,sha,atomic_json,now


def main():
    browser=json.loads((ROOT/'reports/stage8/browser.json').read_text())
    integrity=json.loads((ROOT/'reports/stage7/input-integrity.json').read_text())
    if len(browser['checks'])!=12 or browser['errors'] or len(browser['observations'])!=25:raise ValueError('browser evidence incomplete')
    if integrity['errors'] or not integrity['tinnis_untouched']:raise ValueError('original input integrity failed')
    app=ROOT/'dist';requests={urlparse(u).path for u in browser['requests']}
    for entry in ['inspection.html','terrain.html']:
        refs=re.findall(r'["\']\./(assets/[^"\']+)["\']',(app/entry).read_text())
        if not refs or any('/'+r not in requests for r in refs):raise ValueError('candidate differs from browser-tested '+entry)
    files={}
    for p in sorted(app.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(app)
        if rel.parts[:2]==('datasets','buildings-city'):continue
        files['app/'+str(rel)]=p
    for folder in ['docs','src','scripts','tests','config','bridges','data/manifests/stage7']:
        for p in sorted((ROOT/folder).rglob('*')):
            if p.is_file() and '__pycache__'not in p.parts:files['source/'+str(p.relative_to(ROOT))]=p
    for name in ['AGENTS.md','README.md','package.json','package-lock.json','tsconfig.json','vite.config.ts','inspection.html','terrain.html','index.html']:
        files['source/'+name]=ROOT/name
    for directory in ['reports/stage7','reports/stage8']:
        for p in sorted((ROOT/directory).rglob('*')):
            if p.is_file() and not p.name.startswith('package'):files[str(p.relative_to(ROOT))]=p
    for name in ['ENVIRONMENT_REVIEW.md','INTERACTION_REVIEW.md']:
        files['reports/'+name]=ROOT/'reports'/name
    required=ROOT/'assets/buildings-city/manifest.json'
    manifest={'schema_version':1,'kind':'stage78-overlay-NOT-standalone-full-city','created_at_utc':now(),
        'required_base':{'path':'app/datasets/buildings-city','origin':'unchanged stage4 offline city; also available in current local dist','manifest_sha256':sha(required),'original_stage4_zip_sha256':next(f['sha256']for f in integrity['large_inputs']if f['path']=='reports/nyc-stage4-buildings.zip')},
        'entry':'app/inspection.html','files':[{'path':name,'bytes':p.stat().st_size,'sha256':sha(p)}for name,p in files.items()],
        'scope':'25 environment windows,8 local NAVD88 crops,1,082,964-record search; no completed physical bridge/global height registration',
        'browser_evidence':'reports/stage8/browser.json','copyright':'source notices and licenses in app/licenses and source manifests; no raw DOT/MTA HTML or private reference originals included'}
    out=ROOT/'reports/nyc-stage78-inspection-overlay.zip';temp=out.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5)as z:
        for name,p in files.items():z.write(p,name)
        z.writestr('OVERLAY_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
        z.writestr('START_HERE.txt','第7/8部分离线增量包，非独立全市包。\n先解压已有stage4全市包，再把本包app内容覆盖其app；保留app/datasets/buildings-city。\n或将当前工程dist/datasets/buildings-city原样复制到本包app/datasets/buildings-city。\n进入app运行 python3 -m http.server 8080 --bind 127.0.0.1\n浏览 http://127.0.0.1:8080/inspection.html 。核心请求全部本地，可断网运行。\n道路/桥梁是参考投影，全球垂直配准和完整桥面尚未完成。地面仅八个受限NAVD88检查区。\n原始研究HTML/大数据库未装入本包；source目录含处理脚本与来源清单。\n')
    with zipfile.ZipFile(temp)as z:
        if z.testzip()is not None:raise ValueError('ZIP CRC failed')
        import hashlib
        for f in manifest['files']:
            if hashlib.sha256(z.read(f['path'])).hexdigest()!=f['sha256']:raise ValueError('ZIP payload SHA failed')
    temp.replace(out)
    atomic_json(ROOT/'reports/stage8/package.json',{'at_utc':now(),'path':str(out.relative_to(ROOT)),'bytes':out.stat().st_size,'sha256':sha(out),'files':len(files),'crc_and_all_payload_sha_verified':True,'standalone_full_city':False,'base_requirement':manifest['required_base']})
    print('OVERLAY',out.stat().st_size,'bytes',len(files),'files; all CRC/SHA checked')


if __name__=='__main__':main()
