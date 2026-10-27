import argparse,json
from nyc.normalize import normalize
p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(normalize(a.manifest,a.output),indent=2))
