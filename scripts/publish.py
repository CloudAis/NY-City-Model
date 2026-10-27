import argparse,json
from pathlib import Path
from nyc.tiles import publish
p=argparse.ArgumentParser();p.add_argument('datasets',nargs='+');a=p.parse_args();print(json.dumps(publish(a.datasets),indent=2))
