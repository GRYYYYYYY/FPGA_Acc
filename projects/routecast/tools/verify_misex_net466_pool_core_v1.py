"""Independent Cartesian core exhaustion and capacity-feasible deletion witnesses."""
import sys,json,itertools
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net466_pool_core_v1_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());bindings={**r['bindings'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());parent=R/'experiments/misex_net466_tree_pool_v4_2026-10-07';pool={int(net):options for net,options in json.loads((parent/'pool_attempt0.json').read_text()).items()};event=json.loads((parent/'event.json').read_text());_,_,_,f,_,_=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');slots={edge:i for i,edge in enumerate(f['edge_ids'])};owners=defaultdict(set)
for rec in event['before_records']:
 if rec['net_id'] not in r['release']:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[edge]] for edge in rec['answer']['physical_edge_ids'])
base=Counter(n for own in owners.values() for n in own);core=r['core_nets'];assert len(set(core))==len(core) and set(core)<=set(pool);combinations=0
for choices in itertools.product(*(pool[net] for net in core)):
 counts=Counter(base)
 for option in choices:counts.update(set(option['nodes']))
 assert any(c>f['capacities'][n] for n,c in counts.items());combinations+=1
assert r['irreducible_in_pool'] and {row['removed_net'] for row in r['core_deletion_witnesses']}==set(core)
for row in r['core_deletion_witnesses']:
 result=row['result'];assert result['status']=='FOUND_POOL_BATCH';assert set(row['nets'])==set(core)-{row['removed_net']};selected={int(net):i for net,i in result['chosen_option_indices'].items()};assert set(selected)==set(row['nets']);counts=Counter(base)
 for net,index in selected.items():counts.update(set(pool[net][index]['nodes']))
 assert all(c<=f['capacities'][n] for n,c in counts.items())
assert all(sha(k)==h for k,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,core_nets=core,core_cartesian_combinations_verified=combinations,core_deletion_capacity_witnesses_verified=len(core),irreducible_finite_pool_core=True,scope='Exact finite source tree-variant core under fixed kept. Diagnostic omissions are not accepted routing; no all-path/native infeasibility or workflow gain.'),indent=2)+'\n');print('PASS pool core',core,combinations,len(core))
