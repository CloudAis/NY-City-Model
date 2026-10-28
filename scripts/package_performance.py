"""Release the measured performance candidate as an explicit overlay, preserving its full base."""
import json,zipfile,re,hashlib
from urllib.parse import urlparse
from nyc.download import ROOT,sha,atomic_json,now


def main():
    soak=json.loads((ROOT/'reports/stage9/soak/result.json').read_text());faults=json.loads((ROOT/'reports/stage9/faults.json').read_text())
    integrity=json.loads((ROOT/'reports/stage9/input-integrity.json').read_text())
    if not soak['completed_required_duration']or soak['elapsed_real_seconds']<1800 or soak['errors']or not soak['same_code_entire_run']:raise ValueError('30 real-minute frozen-candidate evidence is incomplete')
    if len(faults['checks'])!=11 or faults['errors']or integrity['errors']or not integrity['tinnis_untouched']:raise ValueError('fault or master integrity verification failed')
    browser=json.loads((ROOT/'reports/stage9/inspection/browser.json').read_text());requested={urlparse(u).path for u in browser['requests']};app=ROOT/'dist'
    if len(browser['checks'])!=12 or browser['errors']:raise ValueError('current inspection regression incomplete')
    for f,digest in soak['codeFingerprint'].items():
        if sha(app/'assets'/f)!=digest:raise ValueError('build changed after soak: '+f)
    for entry in ['inspection.html','terrain.html']:
        refs=re.findall(r'["\']\./(assets/[^"\']+)["\']',(app/entry).read_text())
        if not refs or any('/'+r not in requested for r in refs):raise ValueError('browser regression did not load current '+entry)
    files={}
    for p in sorted(app.rglob('*')):
        if p.is_file()and p.relative_to(app).parts[:2]!=('datasets','buildings-city'):files['app/'+str(p.relative_to(app))]=p
    for folder in ['src','scripts','tests','config','docs','bridges','data/manifests/stage7']:
        for p in sorted((ROOT/folder).rglob('*')):
            if p.is_file()and '__pycache__'not in p.parts:files['source/'+str(p.relative_to(ROOT))]=p
    for name in ['README.md','AGENTS.md','package.json','package-lock.json','tsconfig.json','vite.config.ts','inspection.html','terrain.html','index.html']:
        files['source/'+name]=ROOT/name
    for p in sorted((ROOT/'reports/stage9').rglob('*')):
        if p.is_file()and not p.name.startswith('package'):files[str(p.relative_to(ROOT))]=p
    for name in ['PERFORMANCE_REVIEW.md','STABILITY_REVIEW.md']:files['reports/'+name]=ROOT/'reports'/name
    source_base=ROOT/'assets/buildings-city/manifest.json'
    manifest={'schema_version':1,'kind':'performance-overlay-NOT-standalone-full-city','at_utc':now(),'candidate_commit':soak['code_commit'],
      'required_base':{'path':'app/datasets/buildings-city','manifest_sha256':sha(source_base),'source':'unchanged stage4 city base or current project dist','source_records':1082964,'no_buildings_removed':True},
      'entry':'app/inspection.html','geometry_policy':'unchanged original GLBs, transforms, stable feature IDs and textures; no lossy compression','full_master_data':'preserved locally; multi-GiB raw SQLite/original research archives are not duplicated in this runtime overlay',
      'verification':{'real_continuous_seconds':soak['elapsed_real_seconds'],'fault_checks':len(faults['checks']),'inspection_checks':len(browser['checks'])},
      'files':[{'path':name,'bytes':p.stat().st_size,'sha256':sha(p)}for name,p in files.items()]}
    out=ROOT/'reports/nyc-stage9-performance-overlay.zip';temp=out.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5)as z:
        for name,p in files.items():z.write(p,name)
        z.writestr('OVERLAY_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
        z.writestr('START_HERE.txt','性能与稳定性阶段增量包，非独立全纽约完整版。\n覆盖既有stage4或stage78包的app，保留app/datasets/buildings-city；也可从当前dist复制该完整目录。\n进入app：python3 -m http.server 8080 --bind 127.0.0.1\n浏览 http://127.0.0.1:8080/inspection.html 。所有核心请求本地，可断网运行。\n原始精度/均衡/移动三档不替换原几何或纹理。画质与资源预算见source/docs/QUALITY.md。\n软件WebGL固定路线存在长帧取舍，不保证硬件设备60FPS；全球高程、桥面和完整可信建筑主体的前期缺口仍保留。\n完整主数据与原模型未删；此包避免重复复制大基础数据。SHA与实际解压复验凭据随包外提供，避免自校验循环。\n')
    with zipfile.ZipFile(temp)as z:
        if z.testzip()is not None:raise ValueError('CRC failed')
        for f in manifest['files']:
            if hashlib.sha256(z.read(f['path'])).hexdigest()!=f['sha256']:raise ValueError('payload SHA failed')
    temp.replace(out)
    atomic_json(ROOT/'reports/stage9/package.json',{'at_utc':now(),'path':str(out.relative_to(ROOT)),'bytes':out.stat().st_size,'sha256':sha(out),'files':len(files),'crc_and_all_payload_sha_verified':True,'standalone_full_city':False,'base_requirement':manifest['required_base'],'candidate_commit':soak['code_commit']})
    print('PERFORMANCE OVERLAY',out.stat().st_size,'bytes',len(files),'files, CRC/SHA verified')


if __name__=='__main__':main()
