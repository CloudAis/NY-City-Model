"""Do not confuse independent administrative records with independently surveyed buildings."""
import json,csv
from collections import Counter,defaultdict
from nyc.download import ROOT,atomic_json,sha,now


def main():
    out=ROOT/'reports/stage10';records=json.loads((out/'independent-administrative-records.json').read_text());groups=defaultdict(list)
    for r in records:
        a=r['administrative_record'];t=a.get('job_type','').upper();group='new_building_application'if t in ['NB','NEW BUILDING']else'demolition_application'if t in ['DM','FULL DEMOLITION']else'alteration_application'if t in ['A1','A2','A3']or'ALTERATION'in t or'ALT-CO'in t else'other_administrative_record'
        groups[group].append(r)
    candidates=[];summary={}
    for k,rows in groups.items():
        ids=sorted(set(id for r in rows for id in r['source_building_ids']));summary[k]={'rows':len(rows),'distinct_source_objects':len(ids),'overlapping_categories':True}
        for r in rows:
            candidates.append({'category':k,'source_building_ids':r['source_building_ids'],'dataset':r['dataset'],'source_row_id':r['source_row_id'],'bin':r['bin'],'original_dates_and_status':r['administrative_record'],'current_physical_status':'unknown','confirmed_physical_change':False})
    atomic_json(out/'lifecycle-candidates.json',{'at_utc':now(),'scope':'334 selected source objects only; not full-city building change census','candidates':candidates,'summary':summary,'physical_new_demolished_altered_confirmed_from_these_records':0,'meaning':'applications, certificates and status dates remain separate; no application or permit inferred to be physical completion/demolition; proposed/existing height units unresolved'})
    lm=[]
    for p in sorted((ROOT/'landmarks').glob('*/dossier.json')):
        d=json.loads(p.read_text());dimensions=json.loads((p.parent/'dimensions.json').read_text());params=dimensions.get('parameters',[]);slug=d['slug'];model=p.parent/d['model']if d.get('model')else None
        aspects={k:{'status':'not_verified','reality_error_m':None,'source_or_gap':'no completed model/current independently calibrated views'}for k in ['base','main_body','setbacks','crown','highest_point','facades','orientation','era']}
        if slug=='one-world-trade-center':
            aspects.update({'base':{'status':'source_conflict_partial','source_or_gap':'205 vs200ft design references; foundation not globally registered'},'main_body':{'status':'partial_source_bound_model','source_or_gap':'eight-facet massing, roof416.9664m; not complete as-built volume'},'setbacks':{'status':'partial_outline_only','source_or_gap':'podium transition only; entry details absent'},'crown':{'status':'unknown','source_or_gap':'no antenna diameter/construction invented'},'highest_point':{'status':'source_parameter_axis_only','source_or_gap':'541.3248m factual published extent; antenna model only axis'},'facades':{'status':'unknown','source_or_gap':'neutral materials,no complete curtain wall'},'orientation':{'status':'source_footprint_derived','source_or_gap':'stable ID direction retained; no independent orientation survey'},'era':{'status':'mixed_reference_dates_flagged','source_or_gap':'2012/2014 design plus undated pages, not asserted2026as-built'}})
        elif slug=='432-park-avenue':
            aspects.update({'base':{'status':'replacement_rejected','source_or_gap':'source polygon includes podium/adjacent identities; no unsafe replacement'},'main_body':{'status':'partial_grid_lines','source_or_gap':'425.5008m height,28.4988m width; no volumetric concrete/glazing'},'setbacks':{'status':'unknown','source_or_gap':'mechanical-floor elevations unresolved'},'crown':{'status':'unknown','source_or_gap':'roof/mechanical equipment unresolved'},'highest_point':{'status':'published_parameter_only','source_or_gap':'no independently measured highest point'},'facades':{'status':'not_completed','source_or_gap':'4.7244m grid lines; windows not emitted'},'orientation':{'status':'source_footprint_derived','source_or_gap':'not independently verified'},'era':{'status':'reference_dates_retained','source_or_gap':'not a current exterior survey'}})
        lm.append({'slug':slug,'name':d['name'],'stable_building_id':d.get('stable_building_id'),'dossier':str(p.relative_to(ROOT)),'statuses':d.get('statuses'),'model_exists':bool(model and model.is_file()),'model_sha256':sha(model)if model and model.is_file()else None,'source_parameters':params,'aspects':aspects,'independent_current_reality_verification':False,'complete_fine_building':False})
    atomic_json(out/'landmark-checklist.json',{'at_utc':now(),'dossiers':len(lm),'complete_fine_buildings':0,'scope':'per-dossier evidence/model gap audit; not false all-direction visual verification for unmodelled buildings','landmarks':lm})
    sources=json.loads((ROOT/'data/manifests/stage10/independent-admin-sources.json').read_text());files=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted((ROOT/'data/raw/stage10').rglob('*'))if p.is_file()]
    atomic_json(ROOT/'data/manifests/stage10/evidence-lock.json',{'at_utc':now(),'files':files,'official_resources':sources,'license':'NYCOpenDataTerms retained in original metadata; identity/work history only','download_date_is_not_observation_date':True})
    print('EVIDENCE',summary,'LANDMARK_DOSSIERS',len(lm),'LOCKED_NEW_FILES',len(files))


if __name__=='__main__':main()
