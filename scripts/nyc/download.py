"""Bounded, resumable HTTP cache. Published raw bytes are append-only."""
from pathlib import Path
import urllib.request,urllib.error,urllib.parse,json,time,hashlib,datetime,zipfile,os
from . import PIPELINE_VERSION
ROOT=Path(__file__).resolve().parents[2]
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as f:
  while chunk:=f.read(1024*1024):h.update(chunk)
 return h.hexdigest()
def atomic_json(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2));os.replace(tmp,path)
def validate(path,kind):
 raw=Path(path).read_bytes()
 if not raw:raise ValueError('empty response')
 if kind=='json':
  data=json.loads(raw)
  if isinstance(data,dict)and 'error'in data:raise ValueError('upstream API error: '+str(data['error']))
 elif kind=='zip':
  if not zipfile.is_zipfile(path):raise ValueError('not a ZIP archive')
 elif kind=='las':
  if raw[:4]!=b'LASF':raise ValueError('not LAS/LAZ')
 elif kind=='image':
  if not(raw.startswith(b'\xff\xd8\xff')or raw.startswith(b'\x89PNG\r\n\x1a\n')or raw[:4]in [b'II*\x00',b'MM\x00*']):raise ValueError('not a recognized image')
 elif kind=='html':
  if b'<html'not in raw.lower() and b'<!doctype html'not in raw.lower():raise ValueError('not HTML')
 elif kind not in ('text','binary'):raise ValueError('unsupported validator')
 return len(raw)
def canonical_request(url,data=None):
 p=urllib.parse.urlsplit(url);pairs=urllib.parse.parse_qsl(p.query,keep_blank_values=True)
 if data:pairs+=urllib.parse.parse_qsl(data.decode(),keep_blank_values=True)
 return (p.scheme,p.netloc,p.path,tuple(sorted(pairs)))
class Downloader:
 def __init__(self,root=ROOT,timeout=45,retries=3,interval=.35,max_bytes=512*1024*1024):
  self.root=Path(root);self.timeout=timeout;self.retries=retries;self.interval=interval;self.max_bytes=max_bytes;self.last=0
 def get(self,url,destination,kind='json',refresh=False,data=None):
  dest=Path(destination);dest=dest if dest.is_absolute()else self.root/dest
  receipt=dest.with_name(dest.name+'.receipt.json');cache=self.root/'data/intermediate/download-cache';cache.mkdir(parents=True,exist_ok=True)
  if dest.exists()and not refresh:
   if not receipt.exists():raise ValueError('raw cache has no receipt: '+str(dest))
   meta=json.loads(receipt.read_text());validate(dest,kind)
   if meta['sha256']!=sha(dest)or canonical_request(meta['request_url'],meta.get('request_body').encode()if meta.get('request_body')else None)!=canonical_request(url,data):raise ValueError('raw cache checksum/URL mismatch')
   return dest
  key=hashlib.sha256(url.encode()+(data or b'')).hexdigest();part=cache/(key+'.part');state=cache/(key+'.json');errors=[]
  for attempt in range(self.retries+1):
   try:
    time.sleep(max(0,self.interval-(time.monotonic()-self.last)));self.last=time.monotonic()
    prior=json.loads(state.read_text())if state.exists()else{};offset=part.stat().st_size if part.exists()else 0
    headers={'User-Agent':'NYC-Real-Scale-Research/0.1','Accept-Encoding':'identity'}
    if offset and prior.get('etag') and not data:headers.update({'Range':f'bytes={offset}-','If-Range':prior['etag']})
    else:offset=0
    if data:headers['Content-Type']='application/x-www-form-urlencoded'
    started=now()
    with urllib.request.urlopen(urllib.request.Request(url,data=data,headers=headers),timeout=self.timeout)as r:
     status=r.status;etag=r.headers.get('ETag');length=r.headers.get('Content-Length');total=int(length)+offset if length and status==206 else int(length)if length else None
     if status==206 and not r.headers.get('Content-Range','').startswith(f'bytes {offset}-'):raise ValueError('invalid Content-Range')
     if total and total>self.max_bytes:raise ValueError('download exceeds per-file budget')
     if status!=206:offset=0
     atomic_json(state,{'etag':etag,'url':url,'total':total})
     with part.open('ab'if offset else'wb')as f:
      while chunk:=r.read(256*1024):
       f.write(chunk)
       if f.tell()>self.max_bytes:raise ValueError('download exceeds per-file budget')
     if total is not None and part.stat().st_size!=total:raise IOError('truncated response')
     validate(part,kind);digest=sha(part)
     event={'at':now(),'url':url,'status':status,'bytes':part.stat().st_size,'sha256':digest,'resumed_from_bytes':offset,'refresh':refresh}
     success=self.root/'reports/http-success.jsonl';success.parent.mkdir(parents=True,exist_ok=True)
     with success.open('a')as log:log.write(json.dumps(event)+'\n')
     failed=self.root/'reports/failures'/f'{key}.json'
     if failed.exists():
      history=json.loads(failed.read_text());history.update({'resolved':True,'resolved_at':now()});atomic_json(failed,history)
     target=dest
     if dest.exists():
      if sha(dest)==digest:part.unlink();return dest
      target=dest.with_name(dest.stem+'-'+digest[:12]+dest.suffix)
     target.parent.mkdir(parents=True,exist_ok=True)
     if target.exists():
      if sha(target)!=digest:raise ValueError('immutable raw collision')
      part.unlink()
     else:os.replace(part,target)
     atomic_json(target.with_name(target.name+'.receipt.json'),{'request_url':url,'final_url':r.url,'download_started_at':started,'download_completed_at':now(),'http_method':'POST'if data else'GET','request_body_sha256':hashlib.sha256(data).hexdigest()if data else None,'request_body':data.decode()if data else None,'http_status':status,'content_type':r.headers.get('Content-Type'),'etag':etag,'last_modified_http':r.headers.get('Last-Modified'),'bytes':target.stat().st_size,'sha256':digest,'resumed_from_bytes':offset,'pipeline_version':PIPELINE_VERSION})
     return target
   except (urllib.error.URLError,TimeoutError,OSError,ValueError)as e:
    detail={'at':now(),'url':url,'attempt':attempt+1,'error':str(e)};errors.append(detail)
    log=self.root/'reports/download-attempts.jsonl';log.parent.mkdir(parents=True,exist_ok=True)
    with log.open('a')as f:f.write(json.dumps(detail)+'\n')
    if isinstance(e,urllib.error.HTTPError)and e.code==416:part.unlink(missing_ok=True);state.unlink(missing_ok=True)
    retryable=not isinstance(e,urllib.error.HTTPError)or e.code in [408,416,429,500,502,503,504]
    if attempt>=self.retries or not retryable:break
    time.sleep(min(16,2**attempt))
  atomic_json(self.root/'reports/failures'/f'{key}.json',{'url':url,'destination':str(dest),'attempts':errors,'resolved':False})
  raise RuntimeError('download failed: '+url+' '+str(errors[-1]['error']))
def query_url(base,params):return base+'?'+urllib.parse.urlencode(params)
