"""Transport integrity tests using the actual published startup-script bytes, no city fixtures."""
import hashlib,json,subprocess,sys,tempfile,unittest,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent


class JoinTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);shutil.copy2(ROOT/'join-packages.py',self.root/'join-packages.py');self.row=next(r for r in json.loads((ROOT/'bundle-index.json').read_text())['files']if r['name']=='start-local.py');shutil.copy2(ROOT/'start-local.py',self.root/'start-local.py')
        p=self.root/'bundle-index.json';p.write_text(json.dumps({'files':[self.row]}));(self.root/'READY.json').write_text(json.dumps({'bundle_index_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'files':1}))
    def tearDown(self):self.temp.cleanup()
    def run_join(self):return subprocess.run([sys.executable,str(self.root/'join-packages.py'),'--output',str(self.root/'out')],capture_output=True,text=True)
    def test_actual_file_restored_byte_identically(self):
        r=self.run_join();self.assertEqual(r.returncode,0,r.stderr);self.assertEqual((self.root/'out/start-local.py').read_bytes(),(ROOT/'start-local.py').read_bytes())
    def test_missing_ready_stops_before_creating_output(self):
        (self.root/'READY.json').unlink();self.assertNotEqual(self.run_join().returncode,0);self.assertFalse((self.root/'out').exists())
    def test_existing_user_files_are_preserved(self):
        out=self.root/'out';out.mkdir();sentinel=out/'user-kept.txt';sentinel.write_bytes(b'preserve this existing file');self.assertNotEqual(self.run_join().returncode,0);self.assertEqual(sentinel.read_bytes(),b'preserve this existing file');self.assertEqual(len(list(out.iterdir())),1)
    def test_damaged_actual_bytes_are_rejected(self):
        p=self.root/'start-local.py';b=bytearray(p.read_bytes());b[0]^=1;p.write_bytes(b);r=self.run_join();self.assertNotEqual(r.returncode,0);self.assertNotIn('ALL_REAL_PACKAGE_BYTES_VERIFIED',r.stdout)


if __name__=='__main__':unittest.main(verbosity=2)
