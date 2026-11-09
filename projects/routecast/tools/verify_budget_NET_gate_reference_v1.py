"""NET gate counterexamples and independent node-union/delay oracle."""
import copy, hashlib, json
from pathlib import Path
from budget_pareto_reference_v1 import search
from budget_NET_gate_reference_v1 import decide
adj={0:[(0,1,5,0),(1,2,1,10)],1:[(2,3,0,0)],2:[(3,3,0,0)],3:[(4,4,0,0),(5,5,5,0)]}
budgets={4:10,5:7}; old={4:[1,3,4],5:[1,3,5]}; capacities={v:1 for v in range(6)}
individual={s:search(adj,0,s,b)['edges'] for s,b in budgets.items()}
assert individual=={4:[0,2,4],5:[1,3,5]}
original=copy.deepcopy((adj,budgets,old,individual,capacities))
r=decide(adj,0,budgets,old,individual,capacities=capacities)
assert r['status']=='RETAIN' and r['reason']=='MULTIPLE_PARENTS' and r['paths']==old
assert (adj,budgets,old,individual,capacities)==original
checks={'individually_optimal_paths_conflict':True,'whole_NET_retention_unchanged':True}
for name, candidate, expected in [
 ('valid_shared_tree',old,'ADMIT'),
 ('missing_sink',{4:old[4]},'QUERY_SET'),
 ('wrong_endpoint',{4:[1,3],5:old[5]},'ENDPOINT'),
 ('over_budget',{4:[0,2,4],5:[0,2,5]},'BUDGET'),
 ('invalid_arc',{4:[99],5:old[5]},'ARC')]:
 r=decide(adj,0,budgets,old,candidate,capacities=capacities)
 assert (r['status'] if expected=='ADMIT' else r['reason'])==expected
 chosen=r['paths']; union={0}; delays={}
 # Independent original edge table, not gate audit logic.
 edges={e:(u,v,raw) for u,arcs in adj.items() for e,v,raw,_ in arcs}
 incoming={}
 for s,path in chosen.items():
  node=0; delay=0
  for e in path:
   u,v,raw=edges[e]; assert u==node
   assert v not in incoming or incoming[v]==e
   incoming[v]=e; union.add(v); delay+=raw; node=v
  assert node==s and delay<=budgets[s]; delays[s]=delay
 assert r['audit']['unique_NET_nodes']==sorted(union) and r['audit']['delays']==delays
 checks[name]=True
blocked=dict(capacities); blocked[1]=0
r=decide(adj,0,budgets,old,{4:[0,2,4],5:[0,2,5]},capacities=blocked)
assert r['status']=='RETAIN' # budget rejection occurs before candidate capacity check
blocked=dict(capacities); blocked[2]=0
try: decide(adj,0,budgets,old,individual,capacities=blocked)
except ValueError as e: assert str(e)=='CAPACITY'
else: raise AssertionError('invalid old tree admitted')
checks['invalid_old_tree_is_error']=True
root=Path(__file__).resolve().parents[1]; out=root/'experiments/budget_NET_gate_reference_v1_2026-10-09'; out.mkdir(exist_ok=False)
files=[Path(__file__),root/'tools/budget_NET_gate_reference_v1.py',root/'tools/budget_pareto_reference_v1.py']
receipt=dict(all_pass=True,checks=checks,individual_candidate_paths=individual,feasible_shared_witness=old,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='Small-graph pure admission reference; no production integration, joint-tree optimum or measured recovery/quality/time gains.')
(out/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
