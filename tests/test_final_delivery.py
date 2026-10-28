"""Real owner metadata patching preserves neighbours and supports exact rollback."""
import unittest,json,tempfile,zipfile,hashlib,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('local_update',ROOT/'delivery/update-local.py');update=importlib.util.module_from_spec(spec);spec.loader.exec_module(update)


class FinalDeliveryTests(unittest.TestCase):
    def test_real_owner_scoped_updates_and_reverse_order_rollback(self):
        file=next(p for p in (ROOT/'assets/buildings-city/manhattan').glob('*.json')if p.name not in ['tiles.json','strict.json','hypothesis.json']and isinstance(json.loads(p.read_text()),dict)and'objects'in json.loads(p.read_text()))
        original=file.read_bytes();data=json.loads(original);self.assertGreater(len(data['objects']),1)
        name='app/datasets/buildings-city/manhattan/'+file.name;identity=data['objects'][0]['id']
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);p=root/name;p.parent.mkdir(parents=True);p.write_bytes(original)
            initial={'files':[{'path':name,'bytes':len(original),'sha256':update.sha(p),'license_id':'nyc_open_data_or_project_generated_audit'}],'runtime_uncompressed_bytes':len(original)};update.write(root/'delivery-manifest.json',initial)
            for scope in ['building','tile','borough']:
                changed=json.loads(original);changed['final_acceptance_history']={'scope':scope,'evidence':'real source metadata only; geometry unmodified'};raw=json.dumps(changed).encode();archive=root/(scope+'.zip');before=update.sha(p)
                m={'id':scope,'scope':scope,'source_version':'2026-10-27-city','provenance':'reports/stage10/review-summary.json','stable_ids':[identity],'files':[{'path':name,'old_sha256':before,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}]}
                with zipfile.ZipFile(archive,'w')as z:z.writestr('patch.json',json.dumps(m));z.writestr(name,raw)
                update.apply(root,archive);self.assertEqual(update.ids(p),update.ids(file));self.assertEqual(update.sha(p),m['files'][0]['sha256']);update.rollback(root,scope);self.assertEqual(p.read_bytes(),original);self.assertEqual(json.loads((root/'delivery-manifest.json').read_text()),initial)
            # Simulate the actual journal-before-replace interruption boundary.
            m['id']='interrupted-before-replace';archive=root/'interrupted.zip'
            with zipfile.ZipFile(archive,'w')as z:z.writestr('patch.json',json.dumps(m));z.writestr(name,raw)
            update.apply(root,archive);history=root/'.updates'/m['id'];j=json.loads((history/'journal.json').read_text());j['state']='applying';update.write(history/'journal.json',j);p.write_bytes(original)
            update.rollback(root,m['id']);self.assertEqual(p.read_bytes(),original);self.assertEqual(json.loads((root/'delivery-manifest.json').read_text()),initial)

    def test_incomplete_owner_patch_rejected_before_live_mutation(self):
        files=list((ROOT/'assets/buildings-city/manhattan').glob('*_000.json'));file=next(p for p in files if len(json.loads(p.read_text()).get('objects',[]))>1)
        original=file.read_bytes();data=json.loads(original);data['objects']=data['objects'][:1];raw=json.dumps(data).encode();name='app/datasets/buildings-city/manhattan/'+file.name
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);p=root/name;p.parent.mkdir(parents=True);p.write_bytes(original);update.write(root/'delivery-manifest.json',{'files':[{'path':name,'bytes':len(original),'sha256':update.sha(p)}]})
            m={'id':'reject-incomplete','scope':'building','source_version':'same-source','provenance':'unit-check','stable_ids':[data['objects'][0]['id']],'files':[{'path':name,'old_sha256':update.sha(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}]}
            archive=root/'bad.zip'
            with zipfile.ZipFile(archive,'w')as z:z.writestr('patch.json',json.dumps(m));z.writestr(name,raw)
            with self.assertRaisesRegex(ValueError,'stable IDs removed'):update.apply(root,archive)
            self.assertEqual(p.read_bytes(),original);self.assertFalse((root/'.updates/reject-incomplete').exists())


if __name__=='__main__':unittest.main()
