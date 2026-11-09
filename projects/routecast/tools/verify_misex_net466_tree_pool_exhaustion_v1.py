"""Independent Cartesian coverage of frozen complete-NET tree variants."""
import sys,json,itertools
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net466_tree_pool_v1_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());assert json.loads((out/'candidate.json').read_text()) is None
parent=R/'experiments/misex_net466_extra_owner_joint_v17_2026-10-07';pr=json.loads((parent/'receipt.json').read_text());e=json.loads((out/'event.json').read_text());_,_,_,f,_,_=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');slot={edge:i for i,edge in enumerate(f['edge_ids'])};rows=[]
def own(records):return {rec['source'] for rec in records}|{f['dest_ranks'][slot[edge]] for rec in records for edge in rec['answer']['physical_edge_ids']}
for attempt in r['attempts']:
 assert attempt['status']=='POOL_EXHAUSTED';a=pr['attempts'][attempt['index']];assert attempt['release']==a['release'];release=set(a['release']);required=defaultdict(set);kept=defaultdict(list)
 for rec in e['before_records']:
  if rec['net_id'] in release:required[rec['net_id']].add(rec['connection_id'])
  else:kept[rec['net_id']].append(rec)
 for q in e['selection']['queries']:required[q['net_id']].add(q['connection_id'])
 pool=defaultdict(dict)
 for net in required:
  candidates=[[rec for rec in e['before_records'] if rec['net_id']==net]]
  for b in a['branches']:
   p=parent/f"attempt{a['index']}_branch{b['index']}"/f'net{net}.json'
   if p.exists():
    state=json.loads(p.read_text())
    if state['failure'] is None:candidates.append([rec for rec in state['records'] if rec['net_id']==net])
  for records in candidates:
   if {rec['connection_id'] for rec in records}!=required[net]:continue
   key=tuple(sorted((rec['connection_id'],tuple(rec['answer']['physical_edge_ids'])) for rec in records));pool[net][key]=own(records)
 assert {str(net):len(pool[net]) for net in required}==attempt['variant_counts'];base=Counter(node for records in kept.values() for node in own(records));assert all(c<=f['capacities'][n] for n,c in base.items());nets=sorted(required);total=0
 for combination in itertools.product(*(list(pool[net].values()) for net in nets)):
  total+=1;counts=Counter();invalid=False
  for nodes in combination:
   for node in nodes:
    counts[node]+=1
    if counts[node]+base[node]>f['capacities'][node]:invalid=True;break
   if invalid:break
  assert invalid,'A feasible Cartesian combination contradicts producer exhaustion'
 rows.append(dict(attempt=a['index'],cartesian_combinations_verified=total));print('PASS finite pool',a['index'],total,flush=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'pool_exhaustion_verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Every Cartesian choice among frozen complete tree variants violates union capacity. Not all possible paths, native/global infeasibility or workflow gain.'),indent=2)+'\n')
