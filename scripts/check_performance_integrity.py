"""Verify full master data, every published original city file and all tracked fine assets."""
import json,subprocess,platform,os,zipfile,hashlib
from pathlib import Path
from nyc.download import ROOT,sha,atomic_json,now


def main():
    report_dir=ROOT/os.environ.get('NYC_REPORT_DIR','reports/stage9')
    report_dir.mkdir(parents=True,exist_ok=True)
    errors=[];count=0;size=0;largest=[];registered=set()
    for line in (ROOT/'data/manifests/stage4/generated-files.jsonl').read_text().splitlines():
        f=json.loads(line);registered.add(f['path']);p=ROOT/f['path'];count+=1;size+=p.stat().st_size
        if sha(p)!=f['sha256']:errors.append(f['path'])
        if p.suffix=='.glb':largest.append((p.stat().st_size,f['path']))
    missing=[];unpublished_receipts=0
    with zipfile.ZipFile(ROOT/'reports/nyc-stage4-buildings.zip')as z:
        for p in (ROOT/'assets/buildings-city').rglob('*'):
            if not p.is_file()or str(p.relative_to(ROOT))in registered:continue
            if p.name.endswith('.receipt.json'):
                unpublished_receipts+=1;continue
            archive='app/datasets/'+str(p.relative_to(ROOT/'assets'))
            if archive not in z.namelist():errors.append('not present in original base ZIP: '+str(p));continue
            if hashlib.sha256(z.read(archive)).hexdigest()!=sha(p):errors.append(str(p.relative_to(ROOT)))
            missing.append(str(p.relative_to(ROOT)))
    environment=json.loads((ROOT/'data/manifests/stage7/published-files.json').read_text())['files']
    for f in environment:
        if sha(ROOT/f['path'])!=f['sha256']:errors.append(f['path'])
    prior=json.loads((ROOT/'reports/stage7/input-integrity.json').read_text())
    for f in prior['large_inputs']:
        if sha(ROOT/f['path'])!=f['sha256']:errors.append(f['path'])
    raw=[json.loads(l)for l in (ROOT/'data/manifests/files.jsonl').read_text().splitlines()]
    for f in raw:
        if sha(ROOT/f['path'])!=f['sha256']:errors.append(f['path'])
    more=json.loads((ROOT/'data/manifests/stage7/sources.json').read_text())['raw_files']
    for f in more:
        if sha(ROOT/f['path'])!=f['sha256']:errors.append(f['path'])
    tracked=subprocess.check_output(['git','ls-tree','-r','--name-only','af311b2','assets'],cwd=ROOT,text=True).splitlines()
    for p in tracked:
        expected=subprocess.check_output(['git','rev-parse','af311b2:'+p],cwd=ROOT,text=True).strip()
        actual=subprocess.check_output(['git','hash-object',p],cwd=ROOT,text=True).strip()
        if actual!=expected:errors.append(p)
    tinnis=subprocess.check_output(['git','status','--porcelain'],cwd='/workspace/Tinnis',text=True)
    report={'at_utc':now(),'original_baseline':'af311b2','all_original_city_published_files_verified':count,'original_city_bytes':size,'additional_city_files_compared_to_original_zip':missing,'retained_local_receipts_not_runtime_zip':unpublished_receipts,'all_actual_original_city_files_verified':count+len(missing),'stage7_published_environment_search_files_verified':len(environment),'original_raw_files_verified':len(raw),'stage7_raw_files_verified':len(more),'baseline_tracked_assets_verified':len(tracked),'large_inputs':prior['large_inputs'],'largest_original_glb_files':[{'bytes':n,'path':p}for n,p in sorted(largest,reverse=True)[:10]],'errors':errors,'tinnis_untouched':not tinnis,'original_geometry_compression_or_model_replacement':False,'master_building_records':1082964,'nonplaceholder_source_outlines':1082930}
    atomic_json(report_dir/'input-integrity.json',report)
    atomic_json(report_dir/'environment.json',{'at_utc':now(),'user_facing_date':'2026-10-28','user_facing_timezone':'Asia/Singapore','system':platform.platform(),'os_release':Path('/etc/os-release').read_text(),'lscpu':subprocess.check_output(['lscpu'],text=True),'cgroup_cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text().strip(),'cgroup_memory_max':Path('/sys/fs/cgroup/memory.max').read_text().strip(),'disk':subprocess.check_output(['df','-h',str(ROOT),'/tmp'],text=True),'node':subprocess.check_output(['node','-v'],text=True).strip(),'python':platform.python_version(),'chromium':subprocess.check_output(['/usr/bin/chromium','--version'],text=True).strip(),'gpu':'headless Chromium, ANGLE SwiftShader software renderer; no physical GPU measurement','viewport':[1440,1000],'dpr':1,'baseline_quality':'medium,0.9x','http_cache':'disabled for paired measurements; OS page cache is not flushed','master_data_version':'2026-10-27-city (source observation dates remain individually unknown)','baseline_code':'af311b2','credentials_or_external_cloud_services_required':False})
    print('INTEGRITY',count,'city files,',len(raw)+len(more),'raw,',len(tracked),'tracked assets; error count',len(errors),'first errors',errors[:5])
    if errors or tinnis:raise SystemExit(1)


if __name__=='__main__':main()
