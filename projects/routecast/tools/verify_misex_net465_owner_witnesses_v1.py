"""Paid post-outcome failure domains, bounded single-extra checks; no joint claim."""
import sys,json,time
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from budget_owner_screen_v2 import screen,witness_in_domain
out=R/'experiments/misex_net465_failure_owner_domains_v1_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());bindings={**r['bindings'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());_,_,nodes,f,rc,_=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');event=json.loads((R/'experiments/misex_window_witness_guided_joint_v32_2026-10-07/event.json').read_text());slots={e:s for s,e in enumerate(f['edge_ids'])};allowners=defaultdict(set)
for rec in event['before_records']:allowners[rec['net_id']].add(rec['source']);allowners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
count=0
for row in r['rows']:
 q=row['query'];src,sink=q['source'],q['sink']
 for check in row['checks']:
  w=check['witness']
  if w is None:continue
  extra=check['extra_net'];assert extra not in row['release'];occupancy=Counter(node for net,ns in allowners.items() if net not in row['release'] and net not in (extra,q['net_id']) for node in ns);path=w['physical_edge_ids'];used={src}|{f['dest_ranks'][slots[e]] for e in path};assert not used.intersection(row['bans']);assert all(f['capacities'][node]>occupancy[node] for node in used);assert rc.path(src,sink,path)==w['minimum_integer']<=row['budget'];count+=1
assert all(sha(k)==h for k,h in bindings.items());(out/'positive_witness_verification.json').write_text(json.dumps(dict(positive_witnesses_verified=count,bindings=bindings,scope='Positive physical witnesses only; negative conditions and complete domain coverage not independently certified.'),indent=2)+'\n');print('PASS positive witnesses',count)
