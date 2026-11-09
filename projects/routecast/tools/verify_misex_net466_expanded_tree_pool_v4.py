"""Independent origin/context/node accounting and finite core capacity enumeration."""
import sys,json,time
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from immutable_xml_prediction_audit import ImmutableXMLAudit
out=R/'experiments/misex_net466_expanded_tree_pool_v4_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());p=json.loads((out/'protocol.json').read_text());seed=json.loads((out/'seed.json').read_text());parent=R/'experiments/misex_net466_expanded_negotiation_v1_2026-10-07';pv=json.loads((parent/'branch_verification_dedup.json').read_text());assert pv['all_xml_rc_tree_local_capacity_complete_scope_and_history_checks_pass'];assert seed==json.loads((parent/'seed.json').read_text());graph,digest,nodes,f,rc,queries=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');xml=ImmutableXMLAudit(graph,digest);fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};slots={e:i for i,e in enumerate(f['edge_ids'])};pool={int(n):ops for n,ops in json.loads((out/'pool.json').read_text()).items()};groups={int(n):qs for n,qs in p['groups'].items()};assert set(pool)==set(groups);seedowners=defaultdict(set)
def own(records):return {x['source'] for x in records}|{f['dest_ranks'][slots[e]] for x in records for e in x['answer']['physical_edge_ids']}
for rec in seed:seedowners[rec['net_id']].update(own([rec]))
base=Counter(n for s in seedowners.values() for n in s);previous=R/'experiments/misex_net466_expanded_tree_pool_v3_2026-10-07';inherited=json.loads((previous/'verification.json').read_text());oldrp=previous/'receipt.json';assert sha(oldrp)==inherited['bindings'][str(oldrp)];bindings[str(oldrp)]=sha(oldrp)
for net,ops in pool.items():
 for op in ops:
  origin=Path(op['origin']);state=json.loads(origin.read_text());assert state['failure'] is None and op['records']==state['records']
  if origin.parent==out:
   assert sha(origin)==r['files'][str(origin)];parents={};used=set()
   for kept in seed:
    if kept['net_id']!=net:continue
    u=kept['source']
    for edge in kept['answer']['physical_edge_ids']:
     arc=xml.graph.edges[edge];assert arc.source==u;incoming=(u,edge);u=arc.sink;assert u not in parents or parents[u]==incoming;parents[u]=incoming
   for rec in op['records']:
    query=next(q for q in groups[net] if q['connection_id']==rec['connection_id']);assert all(rec[k]==query[k] for k in ['net_id','source','sink']);floor=floors[rec['source'],rec['sink']];assert rec['floor_integer']==floor and rec['budget_integer']==max(rc.scale//10**9,(3*floor+1)//2);assert rc.path(rec['source'],rec['sink'],rec['answer']['physical_edge_ids'])==rec['answer']['delay']<=rec['budget_integer'];u=rec['source'];seen={u};used.add(u)
    for edge in rec['answer']['physical_edge_ids']:
     arc=xml.graph.edges[edge];assert arc.source==u and arc.sink not in seen;v=arc.sink;incoming=(u,edge);assert v not in parents or parents[v]==incoming;parents[v]=incoming;seen.add(v);used.add(v);u=v
    assert u==rec['sink']
   assert all(base[n]+int(n not in seedowners[net])<=f['capacities'][n] for n in used);masks=R/'experiments/misex_net466_net462_reserved_channels_v1_2026-10-07';mr=json.loads((masks/'receipt.json').read_text());mv=json.loads((masks/'verification.json').read_text());assert state['mask']==mv['compatible_mask_witness'][str(net)];assert not used.intersection({n for i,n in enumerate(mr['cut_nodes']) if not state['mask']>>i&1})
  else:assert sha(origin)==inherited['bindings'][str(origin)];bindings[str(origin)]=sha(origin)
  assert len(op['records'])==len(groups[net]) and {x['connection_id'] for x in op['records']}=={q['connection_id'] for q in groups[net]};assert op['nodes']==sorted(own(op['records'])-seedowners[net])
assert sum(Path(op['origin']).parent==out for ops in pool.values() for op in ops)==sum(x['added_variant'] for x in r['generated']);core=r['core_nets'];assert set(core)<=set(pool);deadline=time.perf_counter()+120;visits=0
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
 assert r['result']['status']=='POOL_EXHAUSTED';assert solve(sorted(core)) is None;corevisits=visits;oldcore=json.loads(oldrp.read_text())['core_nets'];oldwitness=solve(sorted(oldcore));proof=dict(old_core_nets=oldcore,old_core_compatible_choice=oldwitness,core_nets=core,independent_core_search_nodes=corevisits,finite_core_exhaustion_verified=True)
else:
 chosen={int(n):i for n,i in r['result']['chosen_option_indices'].items()};assert set(chosen)==set(pool);records=seed+[x for n,i in chosen.items() for x in pool[n][i]['records']];assert candidate['records']==sorted(records,key=lambda x:x['connection_id']);owners=defaultdict(set)
 for rec in records:owners[rec['net_id']].update(own([rec]))
 ledger=Counter(n for s in owners.values() for n in s);assert all(c<=f['capacities'][n] for n,c in ledger.items());assert ledger==Counter({int(n):c for n,c in candidate['ledger'].items()});event=json.loads((out/'event.json').read_text());expected={x['connection_id'] for x in event['before_records']}|set(event['selection']['requested_connection_ids']);assert len(records)==len({x['connection_id'] for x in records})==2172 and {x['connection_id'] for x in records}==expected;assert candidate['pending_connection_ids']==sorted({q['connection_id'] for q in queries}-expected);proof=dict(full_candidate_scope_and_capacity_pass=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,proof=proof,all_inherited_physical_origins_and_same_net_protected_seed_accounting_pass=True,scope='Inherited independently audited full XML/RC/tree paths plus exact actual origin identity; independent cross-round capacity enumeration. Finite pool exhaustion not all-path/native infeasibility or workflow gain.'),indent=2)+'\n');print('PASS expanded tree pool',proof,flush=True)
