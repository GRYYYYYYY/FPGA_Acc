"""Replay all constrained events from original native paths and certify clipped lower bounds."""
import json
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1];D=R/'experiments/critical_branch_constraint_ablation_v1_2026-10-08';rp=D/'receipt.json';r=json.loads(rp.read_text());assert all(sha(p)==h for p,h in r['bindings'].items())
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2)
meta=json.loads(Path(case['target']).read_text());_,_,nodes,f,rc,queries=load_endpoints(Path(case['target']));assert rc.scale==r['scale'];budget=json.loads(Path(case['budget']).read_text());byid={q['connection_id']:q for q in queries}
observed={}
for name,paths in physical_paths(R/'experiments/native_resume_branch_partial_v8_2026-10-08/resume/output.route').items():
 for path in paths:
  key=(name,path[0][0],path[-1][0]);assert key not in observed;observed[key]=path
state={q['connection_id']:observed[meta['net_names'][str(q['net_id'])],q['source'],q['sink']] for q in queries}
def frame():
 unions=defaultdict(set);parents=defaultdict(dict)
 for cid,path in state.items():
  q=byid[cid];assert path[0]==(q['source'],None) and path[-1][0]==q['sink'];assert len({n for n,s in path})==len(path)
  unions[q['net_id']].update(n for n,s in path)
  for (u,_),(v,s) in zip(path,path[1:]):
   key=(u,s);assert v not in parents[q['net_id']] or parents[q['net_id']][v]==key;parents[q['net_id']][v]=key
 ledger=Counter(n for union in unions.values() for n in union);assert all(v<=f['capacities'][n] for n,v in ledger.items());return unions,ledger
previous=json.loads((R/'experiments/budget_occupied_branch_repair_v1_2026-10-08/receipt.json').read_text());state={int(cid):tuple(tuple(x) for x in path) for cid,path in previous['state'].items()}
assert [(e['connection_id'],e['scenario']) for e in r['events']]==[(cid,scenario) for cid in (832,1781,1892) for scenario in ('FULL_CONSTRAINTS','RELAX_OTHER_OWNERS','RELAX_RETAINED_PARENTS','RELAX_BOTH')]
checks=0
for e in r['events']:
 cid=e['connection_id'];q=byid[cid];assert e['query']==q and e['old_path']==[list(x) for x in state[cid]]
 union,ledger=frame();outside=ledger.copy();outside.subtract(union[q['net_id']]);parents={}
 for other,path in state.items():
  if other!=cid and byid[other]['net_id']==q['net_id']:
   for (u,_),(v,s) in zip(path,path[1:]):parents[v]=(u,s)
 if e['scenario'] in ('RELAX_OTHER_OWNERS','RELAX_BOTH'):outside=Counter()
 if e['scenario'] in ('RELAX_RETAINED_PARENTS','RELAX_BOTH'):parents={}
 cp=Path(e['certificate']);assert sha(cp)==e['certificate_sha256'];c=json.loads(cp.read_text())
 assert c['outside_occupancy']=={str(n):v for n,v in outside.items() if v} and c['retained_parents']=={str(n):list(v) for n,v in parents.items()}
 raw=Fraction(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))/10**9*rc.scale;ceiling=raw.numerator//raw.denominator;assert ceiling==e['budget_integer_ceiling']
 clip=c['clip'];pot={int(n):v for n,v in c['potentials'].items()};assert pot.get(q['source'],clip)==min(rc.initial(q['source']),clip)
 for u,value in pot.items():
  assert 0<=value<clip and outside[u]<f['capacities'][u]
  for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][slot]
   if outside[v]>=f['capacities'][v] or (v in parents and parents[v]!=(u,f['switch_ids'][slot])):continue
   assert pot.get(v,clip)<=value+rc.increments[slot];checks+=1
 if e['status']=='FOUND_CONSTRAINED_MINIMUM':
  assert rc.path(q['source'],q['sink'],e['physical_edge_ids'])==e['delay_integer']==clip<=ceiling
  path=[tuple(x) for x in e['new_path']];u=q['source']
  for (v,s),eid in zip(path[1:],e['physical_edge_ids']):
   slots=[i for i in range(f['row_offsets'][u],f['row_offsets'][u+1]) if f['edge_ids'][i]==eid];assert len(slots)==1;i=slots[0]
   assert (f['dest_ranks'][i],f['switch_ids'][i])==(v,s) and outside[v]<f['capacities'][v] and (v not in parents or parents[v]==(u,s));u=v
  assert len(path)-1==len(e['physical_edge_ids']);assert path[-1][0]==q['sink'] # hypothesis only; do not publish a relaxed candidate
 else:assert e['status']=='RETAIN_NO_CONSTRAINED_BUDGET_PATH' and clip==ceiling+1 and pot.get(q['sink'],clip)==clip
assert r['state']=={str(cid):[list(x) for x in path] for cid,path in state.items()} and len(state)==r['complete_connections']==1929
assert all(sha(p)==h for p,h in r['bindings'].items())
report=dict(receipt_sha256=sha(rp),verifier_sha256=sha(Path(__file__)),complete_connections=1929,events=len(r['events']),found_minima=sum(x['status']=='FOUND_CONSTRAINED_MINIMUM' for x in r['events']),edge_inequalities=checks,all_twelve_constraint_ablation_certificates_pass=True,scope='Shared XML electrical loader; independent sequential original-path replay, all event parent/owner/budget/physical paths/potential lower bounds. Four scenario hypothetical constraints independently rebuilt; original 1929 state unchanged, no candidate publication or owner release, no joint/native feasibility claim.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
