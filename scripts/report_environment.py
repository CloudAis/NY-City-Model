"""Auditable stage7/8 manifests from actual local files; no automatic acceptance claims."""
import json
from pathlib import Path
from nyc.download import ROOT,sha,atomic_json,now


def main():
    raw=[]
    for receipt in sorted((ROOT/'data/raw/stage7').rglob('*.receipt.json')):
        payload=Path(str(receipt).removesuffix('.receipt.json'));r=json.loads(receipt.read_text())
        if not payload.is_file():raise ValueError('missing receipt payload '+str(payload))
        digest=sha(payload)
        expected=r.get('sha256')
        if expected and expected!=digest:raise ValueError('raw SHA mismatch '+str(payload))
        reference=payload.suffix=='.html'
        raw.append({'path':str(payload.relative_to(ROOT)),'bytes':payload.stat().st_size,'sha256':digest,'receipt':str(receipt.relative_to(ROOT)),
            'resource_url':r.get('request_url'),'final_url':r.get('final_url'),'download_started_at':r.get('download_started_at'),'download_completed_at':r.get('download_completed_at'),
            'rights_class':'reference_only_local_original' if reference else 'local_distributable_official_open_data_with_source_notices',
            'rights_note':'DOT/MTA page redistribution not presumed; only facts,quotes and links included in runtime' if reference else 'NYC Open Data Terms / NYS source notices; dataset metadata retained; no commercial imagery',
            'observation_date':None,'date_note':'download timestamps are not survey dates; collection-level observation evidence is recorded separately'})
    vectors=json.loads((ROOT/'data/manifests/stage7/vector-sources.json').read_text())
    scripts=['scripts/acquire_environment.py','scripts/acquire_park_terrain.py','scripts/build_environment.py','scripts/nyc/environment_mesh.py','scripts/research_bridges.py','scripts/build_city_search.py']
    atomic_json(ROOT/'data/manifests/stage7/sources.json',{'schema_version':7,'created_at_utc':now(),'raw_files':raw,'collections':vectors,'terrain':'data/manifests/stage7/park-dem.json','prior_inputs':['data/manifests/sources.json','data/manifests/stage3/sources.json','data/manifests/stage4/sources.json'],
        'horizontal':'Socrata lon,lat degrees -> formal EPSG32118 metre -> per-tile ENU/ECEF; source projected context32118',
        'vertical':'canonical world Z unknown; small ellipsoid draw-order heights are display only. DEM band metre/NAVD88, source realization unresolved; no geoid applied',
        'source_dates':'2015–2016 trees; 2017 DEM. Planimetric capture rules/individual source dates retained, unknown observation dates stay unknown. Last edit/publication/download are distinct.',
        'processing_sha256':{p:sha(ROOT/p)for p in scripts},'full_city_environment_complete':False})
    published=[]
    for folder in ['assets/environment','assets/inspection/search']:
        for p in sorted((ROOT/folder).rglob('*')):
            if p.is_file():published.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)})
    atomic_json(ROOT/'data/manifests/stage7/published-files.json',{'at_utc':now(),'files':published,'raw_not_included':True})
    coverage=json.loads((ROOT/'reports/stage7/coverage.json').read_text())
    union={}
    for p in json.loads((ROOT/'assets/environment/manifest.json').read_text())['observations']:
        c=json.loads((ROOT/'assets/environment'/p['context']).read_text())
        for name,rows in c['features'].items():union.setdefault(name,set()).update(r['id']for r in rows)
    coverage['published_25window_unique_source_ids']={k:len(v)for k,v in union.items()}
    search=json.loads((ROOT/'assets/inspection/search/manifest.json').read_text())
    atomic_json(ROOT/'reports/stage7/quality.json',{'at_utc':now(),'coverage':coverage,'raw_payload_files':len(raw),'published_files':len(published),'published_bytes':sum(p['bytes']for p in published),'static_search_records':search['source_records'],'named_addressed_or_alias_records':search['named_records'],
        'completed_physical_bridge_models':0,'verified_global_vertical_alignment':False,'verified_current_facade_streets':0,
        'estimated_or_display_content':['ellipsoid reference draw-order offsets','NAVD88 water displayH=0 only for rivers/sea; not tide','DEM display decimation','1m collision safety buffer is operational, not measured','fixed neutral light'],
        'not_generated':['random buildings/trees/traffic','invented lanes/furniture','ground rail for ambiguous underground2400','unverified deck heights/interiors','default building heights'],
        'unresolved':['five bridge width/deck absoluteZ/approach profiles','global DEM source realization/geoid registration','road/sidewalk/deck vertical continuity','new current measured street-furniture data','hardware mobile/physical GPU validation'],
        'acceptance':'reference layers and restricted local inspection implemented; physical environment alignment not accepted'})
    atomic_json(ROOT/'reports/stage7/failures.json',{'at_utc':now(),'unresolved_source_gaps':['global vertical datum/frame conflict','bridge deck profiles/widths unknown','current street furniture not acquired','full city environmental coverage not downloaded'],
        'browser_injected_failure':'one GLB HTTP404 deliberately tested; see reports/stage8/browser.json','earlier_browser_failures':'first key timing, lostpointercapture measurement suppression fixed; original failure artifacts retained. Observation predicate tightened after screenshot review.',
        'unobserved':'no independent surveying, bridge under-space physical verification, real mobile device, hardware GPU or other browser'})
    print('MANIFEST',len(raw),'raw files;',len(published),'published files')


if __name__=='__main__':main()
