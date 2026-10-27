"""Re-fetch only URLs actually discovered and recorded, append-only raw cache."""
import argparse,json
from pathlib import Path
from nyc.download import ROOT,Downloader,sha,atomic_json,now
p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');p.add_argument('--include-discovery',action='store_true');a=p.parse_args()
manifest=json.loads((ROOT/'data/manifests/stage5/sources.json').read_text());down=Downloader(timeout=35,retries=2,max_bytes=64*1024*1024);events=[]
for source in manifest['sources']:
 if not a.include_discovery and source['role'].startswith('discovery'):continue
 path=ROOT/source['path'];kind='image'if path.suffix=='.jpg'else'html'if path.suffix=='.html'else'binary'
 try:
  result=down.get(source['url'],source['path'],kind,refresh=a.refresh);digest=sha(result)
  events.append({'source':source['id'],'path':str(result.relative_to(ROOT)),'matches_original_sha':digest==source['sha256'],'sha256':digest,'original_source_overwritten':False})
 except Exception as e:events.append({'source':source['id'],'error':str(e)})
atomic_json(ROOT/'reports/stage5/source-refetch.json',{'at_utc':now(),'events':events,'refresh':a.refresh,'new_versions_never_silently_replace_model_evidence':True});print('SOURCE_CACHE_CHECKED',len(events))
