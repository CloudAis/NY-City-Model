import unittest,tempfile,threading,json,hashlib,http.server,sys,urllib.parse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from nyc.download import Downloader,canonical_request
PAYLOAD=json.dumps({'proof':'local downloader fixture only','data':'x'*10000}).encode()
class Server(http.server.BaseHTTPRequestHandler):
 calls=0;ranges=[]
 def log_message(self,*a):pass
 def do_GET(self):
  type(self).calls+=1
  if self.path=='/bad':
   self.send_response(200);self.end_headers();self.wfile.write(b'<html>Login page is not a model</html>');return
  if self.path=='/unavailable':self.send_error(503);return
  offset=int(self.headers.get('Range','bytes=0-').split('=')[-1].split('-')[0]);type(self).ranges.append(offset)
  self.send_response(206 if offset else 200);self.send_header('Content-Type','application/json');self.send_header('ETag','"fixture-v1"');self.send_header('Content-Length',str(len(PAYLOAD)-offset))
  if offset:self.send_header('Content-Range',f'bytes {offset}-{len(PAYLOAD)-1}/{len(PAYLOAD)}')
  self.end_headers()
  if not offset and self.path=='/range'and type(self).calls==1:self.wfile.write(PAYLOAD[:4500]);self.wfile.flush();self.close_connection=True
  else:self.wfile.write(PAYLOAD[offset:])
class DownloadTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Server);cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start();cls.base='http://127.0.0.1:'+str(cls.server.server_port)
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
 def setUp(self):Server.calls=0;Server.ranges=[]
 def test_actual_http_range_resumes_and_preserves_exact_bytes(self):
  with tempfile.TemporaryDirectory()as td:
   d=Downloader(td,timeout=2,retries=2,interval=0);p=d.get(self.base+'/range','data/raw/fixture.json');self.assertEqual(p.read_bytes(),PAYLOAD);self.assertTrue(any(x>0 for x in Server.ranges));receipt=json.loads(p.with_name(p.name+'.receipt.json').read_text());self.assertEqual(receipt['resumed_from_bytes'],4500);before=p.stat().st_mtime_ns;d.get(self.base+'/range','data/raw/fixture.json');self.assertEqual(p.stat().st_mtime_ns,before)
 def test_html_is_not_saved_as_zip_and_retry_is_bounded(self):
  with tempfile.TemporaryDirectory()as td:
   d=Downloader(td,retries=1,interval=0,timeout=2)
   with self.assertRaises(RuntimeError):d.get(self.base+'/bad','data/raw/model.zip','zip')
   self.assertFalse((Path(td)/'data/raw/model.zip').exists());self.assertEqual(Server.calls,2)
 def test_503_retries_stop(self):
  with tempfile.TemporaryDirectory()as td:
   with self.assertRaises(RuntimeError):Downloader(td,retries=1,interval=0,timeout=2).get(self.base+'/unavailable','data/raw/x.json')
   self.assertEqual(Server.calls,2)
 def test_equivalent_get_and_post_parameters_share_logical_identity(self):
  self.assertEqual(canonical_request('https://example.test/query?f=json&objectIds=1%2C2'),canonical_request('https://example.test/query',b'objectIds=1%2C2&f=json'))
