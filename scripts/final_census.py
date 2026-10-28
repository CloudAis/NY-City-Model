"""Recount locked real source/geometry and keep lifecycle unknowns explicit."""
import json,sqlite3,math,csv,gzip,hashlib
from collections import Counter,defaultdict
from shapely.geometry import shape
from nyc.download import ROOT,atomic_json,sha,now


def main():
    out=ROOT/'reports/stage10';out.mkdir(parents=True,exist_ok=True)
    inputs=['data/processed/city/buildings.sqlite','data/processed/building-stage4/city/associations.sqlite','assets/buildings-city/manifest.json','data/manifests/stage4/generated-files.jsonl','assets/landmarks/manifest.json','assets/facades/manifest.json','data/manifests/sources.json']
    lock={'schema_version':10,'at_utc':now(),'source_capture':'2026-10-27-city','review_date':'2026-10-28','review_timezone':'Asia/Singapore','target_reality_date':None,'target_date_note':'user has not specified a single historical/current model epoch; review date is NOT observation date','files':[{'path':p,'bytes':(ROOT/p).stat().st_size,'sha256':sha(ROOT/p)}for p in inputs]}
    atomic_json(ROOT/'data/manifests/stage10/input-lock.json',lock)
    db=sqlite3.connect('file:'+str(ROOT/inputs[0])+'?mode=ro&immutable=1',uri=True)
    counts=defaultdict(Counter);selected={r['record']['id']:r for r in json.loads((ROOT/'data/processed/building-stage4/review-selection.json').read_text())['records']};chosen=Counter();invalid=[];lifecodes=Counter();total=0
    with gzip.open(out/'lifecycle-all-source.csv.gz','wt',newline='')as f:
        writer=csv.writer(f);writer.writerow(['id','bin','borough','source_feature_code','source_construction_year','source_last_edit','source_observation_date','current_status','source_construction_flag','recent_source_year_candidate','confirmed_new','confirmed_demolished','confirmed_altered','reason'])
        for (payload,)in db.execute("select payload from buildings where capture like '2026-10-27-city:%'"):
            r=json.loads(payload);b=r['borough'];c=counts[b];c['source_records']+=1;total+=1;g=shape(r['geometry']);valid=not g.is_empty and g.is_valid and g.geom_type in ['Polygon','MultiPolygon'];ph=bool(r['placeholder']);code=int(r.get('feature_code')or 0);lifecodes[code]+=1
            c['numerically_valid_geometries']+=int(valid);c['placeholders_excluded']+=int(ph);c['nonplaceholder_valid_outlines']+=int(valid and not ph)
            ps=list(g.geoms)if g.geom_type=='MultiPolygon'else[g];c['polygon_parts']+=len(ps);c['interior_rings']+=sum(len(p.interiors)for p in ps if p.geom_type=='Polygon')
            raw=r.get('height_raw_ft');numeric=isinstance(raw,(float,int))and not isinstance(raw,bool)and math.isfinite(raw)and 0<raw<=2500 and r.get('height_status')=='valid';c['valid_source_height_number_unit_unresolved']+=int(numeric);c['height_number_unknown_or_anomalous']+=int(not numeric)
            c['observation_date_unknown']+=int(not r.get('observation_date'));c['current_status_unknown']+=1;c['source_construction_flag_date_unresolved']+=int(code==5100)
            year=r.get('construction_year');historical=isinstance(year,(int,float))and 0<year<1900;recent=isinstance(year,(int,float))and 2024<=year<=2026
            c['historical_source_year_candidates']+=int(historical);c['recent_source_year_candidates']+=int(recent)
            if not valid:invalid.append({'id':r['id'],'raw':r['raw_record'],'reason':'invalid/empty/nonpolygon'})
            label='historical_source_year_NOT_verified_current_status'if historical else'missing_height'if not numeric and not ph else'official_placeholder'if ph else'construction_source_flag_date_unknown'if code==5100 else None
            if label and chosen[b+':'+label]<6 and r['id']not in selected:
                selected[r['id']]={'selection_category':label,'record':r};chosen[b+':'+label]+=1
            writer.writerow([r['id'],r.get('bin'),b,code,year,r.get('last_edited_at'),r.get('observation_date'),'unknown',code==5100,recent,'','','','editing or source year is not dated physical observation; permit candidates reviewed separately'])
            if total%100000==0:print('CENSUS',total,flush=True)
    assoc=sqlite3.connect('file:'+str(ROOT/inputs[1])+'?mode=ro&immutable=1',uri=True)
    for b,n,canon,roof,facade,matched in assoc.execute("select borough,count(*),sum(json_extract(metadata,'$.canonical_height_m')is not null),sum(json_extract(metadata,'$.roof_status')!='unknown'),sum(json_extract(metadata,'$.facade_status')!='unknown'),sum(json_extract(metadata,'$.historical_model_match')is not null) from objects group by borough"):
        counts[b]['processed_source_entities']=n;counts[b]['canonical_height_values']=canon;counts[b]['roof_nonunknown_records']=roof;counts[b]['facade_nonunknown_records']=facade;counts[b]['current_model_matches']=matched
    manifest=json.loads((ROOT/'assets/buildings-city/manifest.json').read_text())
    for b in manifest['boroughs']:
        index=json.loads((ROOT/'assets/buildings-city'/b['index']).read_text());ids=[id for t in index for id in t['feature_ids']]
        if len(ids)!=len(set(ids)):raise ValueError('duplicate published source identity')
        counts[b['id']]['published_outline_entities']=len(ids);counts[b['id']]['strict_glb_tiles']=len(index)
        if len(ids)!=counts[b['id']]['nonplaceholder_valid_outlines']:raise ValueError('source/publication count mismatch')
    lm=json.loads((ROOT/'assets/landmarks/manifest.json').read_text());fac=json.loads((ROOT/'assets/facades/manifest.json').read_text());oldfac=json.loads((ROOT/'reports/stage6/quality.json').read_text())
    for b,c in counts.items():
        c['verified_complete_building_bodies']=0;c['independently_verified_height']=0;c['reliable_roofs']=0;c['complete_current_facades']=0
    report={'schema_version':10,'at_utc':now(),'lock':'data/manifests/stage10/input-lock.json','source_version':'2026-10-27-city','denominator_definition':'distinct retained DOITT source records, NOT independently enumerated real physical buildings','borough_assignment':'source BASE_BBL partition; not independently boundary-assigned','total_source_entities':total,'boroughs':dict(counts),'totals':{k:sum(c[k]for c in counts.values())for k in sorted(set(k for c in counts.values()for k in c))},'invalid_geometries':invalid,'feature_code_counts':dict(lifecodes),'source_placeholder_rule':'official1003 placeholder retained in data but not rendered; not an optimization deletion','geometry_parts_are_not_building_count':True,'landmarks':{'dossiers':lm['requested_dossiers'],'partial_representations':lm['published_representations'],'complete_fine_models':lm['fully_detailed_landmarks_completed'],'physical_world_placements_verified':0},'facades':{'areas':fac['area_count'],'source_building_denominator':fac['unique_source_buildings'],'candidate_edge_denominator':oldfac['facade_candidate_edges'],'physical_facade_denominator':None,'current_complete_buildings':0,'current_verified_facades':0,'historical_partial_fronts':oldfac['historical_fragments'],'historical_complete_facades':0},'reality_accuracy_m':None,'independent_survey_controls':0,'target_reality_date':None,'lifecycle':'lifecycle-all-source.csv.gz; no current demolition/new/alteration status inferred from edit date','displayed_vs_published':'all published resources checked by ID; actual visible samples are counted separately in browser report, not all records are loaded simultaneously','overall_acceptance':'partial evidence build; complete real city building bodies/exteriors NOT accepted'}
    report['unverified_open_envelopes']=manifest['counts']['hypothesis_eligible']
    atomic_json(out/'census.json',report);atomic_json(out/'review-selection.json',{'at_utc':now(),'source_version':report['source_version'],'records':list(selected.values()),'additional_strata':dict(chosen),'selection_is_not_independent_measurement':True})
    with(out/'borough-coverage.csv').open('w',newline='')as f:
        keys=sorted(set(k for c in counts.values()for k in c));w=csv.DictWriter(f,fieldnames=['borough',*keys]);w.writeheader();w.writerows({'borough':b,**dict(c)}for b,c in counts.items())
    print('COMPLETE',total,'source records,',len(selected),'review objects;',len(invalid),'invalid',flush=True)
    if invalid:raise SystemExit(1)


if __name__=='__main__':main()
