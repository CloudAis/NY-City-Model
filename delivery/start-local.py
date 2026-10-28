#!/usr/bin/env python3
"""Run the assembled offline app using Python standard library only."""
import argparse,http.server,functools,json,os
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8080);a=p.parse_args();root=Path(__file__).resolve().parent/'app'
    required=['index.html','inspection.html','preview-single.html','datasets/release/summary.json','datasets/buildings-city/manifest.json',*[f'datasets/buildings-city/{b}/strict.json'for b in ['manhattan','brooklyn','queens','bronx','staten-island']]]
    missing=[f for f in required if not(root/f).is_file()]
    if missing:raise SystemExit('运行包尚未组装完整，缺少：'+', '.join(missing)+'。请先运行 assemble.py。')
    handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root));server=http.server.ThreadingHTTPServer(('127.0.0.1',a.port),handler)
    print(f'本地离线入口：http://127.0.0.1:{server.server_port}/index.html',flush=True);print('仅监听127.0.0.1；Ctrl+C停止。完整现状精细建筑尚未完成，详见页面统计。',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()
