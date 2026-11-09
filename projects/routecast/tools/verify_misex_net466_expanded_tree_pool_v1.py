"""Independent origin/context/node accounting and finite core capacity enumeration."""
import sys,json,time
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net466_expanded_tree_pool_v1_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());p=json.loads((out/'protocol.json').read_text());seed=json.loads((out/'seed.json').read_text());parent=R/'experiments/misex_net466_expanded_negotiation_v1_2026-10-07';pv=json.loads((parent/'branch_verification_dedup.json').read_text());assert pv['all_xml_rc_tree_local_capacity_complete_scope_and_history_checks_pass'];assert seed==json.loads((parent/'seed.json').read_text());_,_,nodes,f,rc,queries=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');slots={e:i for i,e in enumerate(f['edge_ids'])};pool={int(n):ops for n,ops in json.loads((out/'pool.json').read_text()).items()};groups={int(n):qs for n,qs in p['groups'].items()};assert set(pool)==set(groups);seedowners=defaultdict(set)
def own(records):return {x['source'] for x in records}|{f['dest_ranks'][slots[e]] for x in records for e in x['answer']['physical_edge_ids']}
for rec in seed:seedowners[rec['net_id']].update(own([rec]))
base=Counter(n for s in seedowners.values() for n in s)
for net,ops in pool.items():
 for op in ops:
  assert bindings[op['origin']]==pv['bindings'][op['origin']];state=json.loads(Path(op['origin']).read_text());assert state['failure'] is None and op['records']==state['records'];assert len(op['records'])==len(groups[net]) and {x['connection_id'] for x in op['records']}=={q['connection_id'] for q in groups[net]};assert op['nodes']==sorted(own(op['records'])-seedowners[net])
core=r['core_nets'];assert set(core)<=set(pool);deadline=time.perf_counter()+120;visits=0
def solve(nets):
 global visits
 visits=0
 def dfs(i,counts):
  global visits
  visits+=1
  if visits>1000000 or time.perf_counter()>=deadline:raise TimeoutError('Independent enumeration limit; no exhaustion proof')
  if i==len(nets):return {}
  net=nets[i]
  for j,op in enumerate(pool[net]):
   new=counts.copy();new.update(op['nodes'])
   if all(new[n]<=f['capacities'][n] for n in op['nodes']):
    answer=dfs(i+1,new)
    if answer is not None:return {net:j,**answer}
  return None
 return dfs(0,Counter(base))
candidate=json.loads((out/'candidate.json').read_text())
if candidate is None:
 assert r['result']['status']=='POOL_EXHAUSTED';assert solve(sorted(core)) is None;proof=dict(core_nets=core,independent_core_search_nodes=visits,finite_core_exhaustion_verified=True)
else:
 chosen={int(n):i for n,i in r['result']['chosen_option_indices'].items()};assert set(chosen)==set(pool);records=seed+[x for n,i in chosen.items() for x in pool[n][i]['records']];assert candidate['records']==sorted(records,key=lambda x:x['connection_id']);owners=defaultdict(set)
 for rec in records:owners[rec['net_id']].update(own([rec]))
 ledger=Counter(n for s in owners.values() for n in s);assert all(c<=f['capacities'][n] for n,c in ledger.items());assert ledger==Counter({int(n):c for n,c in candidate['ledger'].items()});event=json.loads((out/'event.json').read_text());expected={x['connection_id'] for x in event['before_records']}|set(event['selection']['requested_connection_ids']);assert len(records)==len({x['connection_id'] for x in records})==2172 and {x['connection_id'] for x in records}==expected;assert candidate['pending_connection_ids']==sorted({q['connection_id'] for q in queries}-expected);proof=dict(full_candidate_scope_and_capacity_pass=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,proof=proof,all_inherited_physical_origins_and_same_net_protected_seed_accounting_pass=True,scope='Inherited independently audited full XML/RC/tree paths plus exact actual origin identity; independent cross-round capacity enumeration. Finite pool exhaustion not all-path/native infeasibility or workflow gain.'),indent=2)+'\n');print('PASS expanded tree pool',proof,flush=True)
