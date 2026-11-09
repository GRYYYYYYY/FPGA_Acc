"""Independent new path, unchanged seed, whole-group palettes and finite exhaustion audit."""
import sys,json,time,itertools
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from immutable_xml_prediction_audit import ImmutableXMLAudit
out=R/'experiments/misex_net466_core_variant_expansion_v1_2026-10-07';parent=R/'experiments/misex_net466_tree_pool_v4_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());p=json.loads((out/'protocol.json').read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());assert p['bindings']==r['bindings'];ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';graph,digest,nodes,f,rc,queries=load_endpoints(ep);xml=ImmutableXMLAudit(graph,digest);qm={q['connection_id']:q for q in queries};floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads((R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json').read_text())};event=json.loads((out/'event.json').read_text());pr=json.loads((parent/'receipt.json').read_text());release=pr['attempts'][0]['release'];kept={x['connection_id']:x for x in event['before_records'] if x['net_id'] not in release};states={};seen={};checked=0

def audit_records(records):
 global checked
 ids=set();owners=defaultdict(set);parents=defaultdict(dict)
 for rec in records:
  cid=rec['connection_id'];assert cid not in ids;ids.add(cid);q=qm[cid];assert all(rec[k]==q[k] for k in ['net_id','source','sink']);floor=floors[q['source'],q['sink']];assert rec['floor_integer']==floor and rec['budget_integer']==max(rc.scale//10**9,(3*floor+1)//2);assert rc.path(q['source'],q['sink'],rec['answer']['physical_edge_ids'])==rec['answer']['delay']<=rec['budget_integer'];u=q['source'];visited={u};owners[q['net_id']].add(u)
  for edge in rec['answer']['physical_edge_ids']:
   arc=xml.graph.edges[edge];assert arc.source==u;v=arc.sink;assert v not in visited;visited.add(v);incoming=(u,edge);assert v not in parents[q['net_id']] or parents[q['net_id']][v]==incoming;parents[q['net_id']][v]=incoming;owners[q['net_id']].add(v);u=v
  assert u==q['sink'];checked+=1
 return owners

for a in r['attempts']:
 assert a['index']==len(states);plan=a['plan'];assert plan==p['schedule'][a['index']];state=json.loads(Path(a['state_file']).read_text());states[a['index']]=state;records={x['connection_id']:x for x in state['records']};assert len(records)==len(state['records']) and all(records[cid]==rec for cid,rec in kept.items());ownqueries=plan['queries'];expected={x['connection_id'] for x in event['before_records'] if x['net_id']==plan['net']}|{q['connection_id'] for q in event['selection']['queries'] if q['net_id']==plan['net']};assert {q['connection_id'] for q in ownqueries}==expected and len(ownqueries)==len(expected);assert all(q==qm[q['connection_id']] for q in ownqueries);assert state['failure']==a['failure'];ownids=set(records)-set(kept);assert ownids<=expected
 if a['failure'] is None:assert ownids==expected
 else:
  fail=a['failure']['query'];assert fail in ownqueries;assert ownids=={q['connection_id'] for q in ownqueries[:ownqueries.index(fail)]}
 owners=audit_records(state['records']);assert not owners[plan['net']].intersection(plan['banned_nodes']);ledger=Counter(n for own in owners.values() for n in own);assert ledger==Counter({int(n):c for n,c in state['ledger'].items()});assert all(c<=f['capacities'][n] for n,c in ledger.items());assert state['completed_connections']==len(records) and state['required_connections']==len(kept)+len(expected)
 seen[a['state_file']]=[x for x in state['records'] if x['net_id']==plan['net']]

proofs=[]
for scope in pr['attempts']:
 index=scope['index'];pool={int(n):ops for n,ops in json.loads((out/f'pool_attempt{index}.json').read_text()).items()};old={int(n):ops for n,ops in json.loads((parent/f'pool_attempt{index}.json').read_text()).items()};groups=defaultdict(set);fixed=[]
 for rec in event['before_records']:
  if rec['net_id'] in scope['release']:groups[rec['net_id']].add(rec['connection_id'])
  else:fixed.append(rec)
 for q in event['selection']['queries']:groups[q['net_id']].add(q['connection_id'])
 assert set(pool)==set(old)==set(groups)
 for net,ops in pool.items():
  assert ops[:len(old[net])]==old[net]
  for option in ops:
   records=option['records'];assert len(records)==len(groups[net]) and {x['connection_id'] for x in records}==groups[net] and all(x['net_id']==net for x in records);owners=audit_records(records);assert sorted(owners[net])==option['nodes']
  for option in ops[len(old[net]):]:assert sorted(option['records'],key=lambda x:x['connection_id'])==sorted(seen[option['origin']],key=lambda x:x['connection_id'])
 owners=audit_records(fixed);base=Counter(n for own in owners.values() for n in own);assert all(c<=f['capacities'][n] for n,c in base.items());nets=sorted(pool);visits=[0];deadline=time.perf_counter()+120
 def dfs(i,counts):
  visits[0]+=1;assert visits[0]<=1000000 and time.perf_counter()<deadline,'Verifier limit; no exhaustion certificate'
  if i==len(nets):return True
  for option in pool[nets[i]]:
   new=counts.copy();new.update(option['nodes'])
   if all(new[n]<=f['capacities'][n] for n in option['nodes']) and dfs(i+1,new):return True
  return False
 feasible=dfs(0,base);proofs.append(dict(pool=index,capacity_feasible=feasible,independent_search_nodes=visits[0],variant_counts={n:len(v) for n,v in pool.items()}));assert not feasible;print('PASS finite scope',index,visits[0],flush=True)
assert json.loads((out/'candidate.json').read_text()) is None and r['completed'] is None;assert all(sha(k)==h for k,h in bindings.items());(out/'generation_and_palette_verification.json').write_text(json.dumps(dict(bindings=bindings,generation_states_verified=len(states),records_physically_verified=checked,scope_proofs=proofs,all_original_budgets_seed_preservation_tree_and_caps_pass=True,scope='All generated partial/full states and complete compact palettes audited; independent finite-palette exhaustion only, no all-path/native impossibility or time gain.'),indent=2)+'\n');print('PASS expansion',len(states),checked)
