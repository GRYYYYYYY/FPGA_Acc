"""Evaluator-only multiset check against archived printed SOURCE/SINK endpoints."""
import argparse
from collections import Counter
import hashlib,json,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('endpoints',type=Path);p.add_argument('route',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
e=json.loads(a.endpoints.read_text());expected=Counter((r['net_id'],r['source'],r['sink']) for r in e['connections'])
observed=Counter();net=None;source=None
for line in a.route.read_text().splitlines():
    m=re.match(r'^\s*Net\s+(\d+)\s+\(',line)
    if m:net=int(m[1]);source=None
    m=re.match(r'^\s*Node:\s*(\d+)\s+(SOURCE|SINK)\b',line)
    if m:
        node=int(m[1])
        if m[2]=='SOURCE':
            if source is not None and source!=node:raise ValueError('multiple roots')
            source=node
        else:
            if net is None or source is None:raise ValueError('sink without root')
            observed[(net,source,node)]+=1
result={'scope':'evaluation-only endpoint multiplicity, not physical path or native legality validation','endpoint_sha256':hashlib.sha256(a.endpoints.read_bytes()).hexdigest(),'route_sha256':hashlib.sha256(a.route.read_bytes()).hexdigest(),'expected_connections':sum(expected.values()),'observed_connections':sum(observed.values()),'missing':sum((expected-observed).values()),'extra':sum((observed-expected).values()),'exact_multiset_match':expected==observed}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if expected!=observed:raise SystemExit(1)
