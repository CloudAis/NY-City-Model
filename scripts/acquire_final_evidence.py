"""Official DOB administrative evidence for locked review BINs, not a physical survey."""
import json,urllib.parse
from collections import defaultdict
from nyc.download import ROOT,Downloader,atomic_json,sha,now

SOURCES={
 'ic3t-wcy2':('bin__',['job__','doc__','job_type','job_status','job_status_descrp','latest_action_date','pre__filing_date','approved','fully_permitted','signoff_date','existing_height','proposed_height','existingno_of_stories','proposed_no_of_stories','landmarked']),
 'w9ak-ipjd':('bin',['job_filing_number','job_type','filing_status','filing_date','current_status_date','first_permit_date','approved_date','signoff_date','existing_height','proposed_height','full_demolition_work_type_','job_description']),
 'pkdm-hqz6':('bin',['job_filing_name','job_type','submitted_date','c_of_o_status','c_of_o_filing_type','c_of_o_issuance_date','application_number','c_of_o_number'])}


def main():
    selection=json.loads((ROOT/'reports/stage10/review-selection.json').read_text())['records'];mapping=defaultdict(list)
    for e in selection:
        r=e['record'];bin=str(r.get('bin')or'')
        if len(bin)==7 and bin.isdigit()and not bin.endswith('000000'):mapping[bin].append(r['id'])
    d=Downloader(timeout=25,retries=2,max_bytes=16*1024**2);allrows=[];manifests=[]
    discovery=json.loads((ROOT/'data/raw/stage10/dob-discovery.json').read_text())
    for dataset,(key,fields)in SOURCES.items():
        published=next(r for r in discovery['results']if r['resource']['id']==dataset)
        meta_path=ROOT/f'data/raw/stage10/{dataset}-metadata.json';meta=json.loads(meta_path.read_text());actual={c['fieldName']:c['dataTypeName']for c in meta['columns']}
        if any(f not in actual for f in [key,*fields]):raise ValueError('actual source fields changed')
        started=now();rows=[];pages=[];bins=sorted(mapping)
        for batch in range(0,len(bins),50):
            where=key+' in('+','.join("'"+b+"'"for b in bins[batch:batch+50])+')';base='https://data.cityofnewyork.us/resource/'+dataset+'.json?'
            count_path=d.get(base+urllib.parse.urlencode({'$where':where,'$select':'count(*) as count'}),f'data/raw/stage10/dob/{dataset}/count-{batch:03}.json')
            expected=int(json.loads(count_path.read_text())[0]['count'])
            if expected>12000:raise ValueError('review BIN subset exceeds bounded row budget')
            got=[]
            for offset in range(0,expected,500):
                params={'$where':where,'$select':':id as socrata_row_id,'+','.join([key,*fields]),'$order':':id ASC','$limit':500,'$offset':offset}
                path=d.get(base+urllib.parse.urlencode(params),f'data/raw/stage10/dob/{dataset}/batch-{batch:03}-{offset:05}.json');part=json.loads(path.read_text())
                if not isinstance(part,list):raise ValueError('row array expected')
                got+=part;pages.append({'path':str(path.relative_to(ROOT)),'sha256':sha(path),'records':len(part)})
            if len(got)!=expected or len({r['socrata_row_id']for r in got})!=expected:raise ValueError('incomplete/duplicate pagination')
            rows+=got;print('DOB_BATCH',dataset,batch,expected,flush=True)
        end=d.get('https://data.cityofnewyork.us/api/views/'+dataset+'.json',f'data/raw/stage10/dob/{dataset}/metadata-end.json',refresh=True);end_meta=json.loads(end.read_text())
        stable=meta.get('rowsUpdatedAt')==end_meta.get('rowsUpdatedAt')
        manifests.append({'dataset':dataset,'official_entry':published['link'],'metadata':str(meta_path.relative_to(ROOT)),'metadata_sha256':sha(meta_path),'field_types':{f:actual[f]for f in [key,*fields]},'pages':pages,'records':len(rows),'unique_rows':len({r['socrata_row_id']for r in rows}),'capture_started_at':started,'capture_ended_at':now(),'rows_updated_at':meta.get('rowsUpdatedAt'),'end_rows_updated_at':end_meta.get('rowsUpdatedAt'),'metadata_stable_during_capture':stable,'transaction_snapshot':False,'license':'NYC Open Data Terms; original metadata retained','source_scope':str(len(bins))+' review BINs only, not full-city permits','independence':'DOB administrative source was not used to generate footprint geometry; submission/status is not independent as-built surveying','height_units_resolved':False})
        for r in rows:
            bin=r[key];allrows.append({'dataset':dataset,'source_row_id':r['socrata_row_id'],'bin':bin,'source_building_ids':mapping.get(bin,[]),'administrative_record':r,'physical_current_status':'unresolved','physical_height_m':None,'not_as_built_measurement':True})
        if not stable:print('SOURCE_CHANGED',dataset,'retain capture and report consistency gap',flush=True)
    atomic_json(ROOT/'data/manifests/stage10/independent-admin-sources.json',manifests)
    atomic_json(ROOT/'reports/stage10/independent-administrative-records.json',allrows)
    covered={id for r in allrows for id in r['source_building_ids']}
    atomic_json(ROOT/'reports/stage10/independent-evidence.json',{'at_utc':now(),'reviewed_source_objects':len(selection),'review_objects_with_dob_records':len(covered),'dob_record_rows':len(allrows),'independent_surveyed_geometry_controls':0,'independent_as_built_height_checks':0,'can_compute_reality_error_m':False,'records':'independent-administrative-records.json','scope':'independent administrative identity/work-history evidence only; source BIN may map to multiple components/records','no_record_meaning':'absence is not proof of no construction or alteration','date_policy':'permit,filing,signoff/occupancy dates retained separately; none is automatically footprint observation date'})
    print('DOB_COMPLETE',len(allrows),'records for',len(covered),'review objects')


if __name__=='__main__':main()
