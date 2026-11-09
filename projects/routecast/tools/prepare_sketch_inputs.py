"""One-way extraction from archived audit; strips all path/occupancy labels."""
import argparse
import hashlib
import json
from pathlib import Path


def prepare(source):
    records=source['connections']
    return {'schema':'ROUTECAST_ENDPOINTS_V1','graph_sha256':source['graph_sha256'],
            'provenance':'post-route-derived SOURCE/SINK classes; provisional development only',
            'connections':[{key:r[key] for key in ('connection_id','net_id','source','sink')} for r in records]}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('audit',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    result=prepare(json.loads(a.audit.read_text()))
    result['origin_audit_sha256']=hashlib.sha256(a.audit.read_bytes()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
