"""Strict full-output differential including workspace reuse and wide prices."""
import json,sys,random
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from marginal_tree_growth_reference_v1 import grow
from marginal_tree_growth_cpp_v2 import Growth
from pre_route_endpoints import sha
binary=R/'experiments/marginal_branch_build_v1_2026-10-08/search.so'
rng=random.Random(100804);checked=0;budget_failures=0;unreachable=0
for graph in range(240):
 n=rng.randrange(4,18);adj={u:[] for u in range(n)};inc={};row=[0];dest=[];ids=[];vals=[]
 for u in range(n):
  for v in range(n):
   if u!=v and rng.random()<0.25:
    for parallel in range(1+(rng.random()<0.1)):
     e=len(dest);d=rng.randrange(10);adj[u].append((e,v));inc[e]=d;dest.append(v);ids.append(e);vals.append(d)
  row.append(len(dest))
 cap={u:int(rng.random()>0.12) for u in range(n)}
 f=dict(capacities=[cap[u] for u in range(n)],row_offsets=row,dest_ranks=dest,edge_ids=ids)
 search=Growth(f,vals,binary)
 for trial in range(12):
  source=rng.randrange(n);sinks=[rng.randrange(n) for _ in range(5)];initial=rng.randrange(5)
  prices={u:rng.randrange(7) for u in range(n)};weight=3 if trial<11 else 1<<63
  budgets={s:rng.randrange(5,80) for s in sinks}
  expected=grow(source,sinks,adj,inc,cap,prices,weight,initial,budgets)
  search.prepare(prices,weight);actual=search.grow(source,sinks,initial,budgets)
  assert actual==expected,(graph,trial,actual,expected)
  checked+=1;budget_failures+=actual['status']=='RETAIN_OLD_TREE_BUDGET';unreachable+=actual['status']=='RETAIN_OLD_TREE_UNREACHABLE'
 search.close()
 try:search.grow(0,[0],0,{0:0});raise AssertionError('closed workspace accepted')
 except RuntimeError:pass
out=R/'experiments/marginal_tree_growth_cpp_contract_v2_2026-10-08';out.mkdir()
files=[Path(__file__),R/'tools/marginal_tree_growth_reference_v1.py',R/'tools/marginal_tree_growth_cpp_v2.py',R/'tools/soft_demand_cpp/marginal_branch_v1.cpp',binary,R/'experiments/marginal_tree_growth_reference_contract_v1_2026-10-08/verification.json',R/'experiments/ethernet_marginal_tree_growth_prereg_v1_2026-10-08/protocol.json']
bindings={str(p):sha(p) for p in files}
(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,random_graphs=240,sequential_growth_calls=checked,budget_retains=budget_failures,unreachable_retains=unreachable,all_status_records_branches_parents_raw_owned_exact_reference_pass=True,wide_cost_zero_increment_parallel_edge_repeated_target_workspace_recovery_scope=True,scope='Small-graph exact differential only; full original RR physical/event audit and quality/runtime experiment remain required.'),indent=2)+'\n')
print('PASS C++ growth differential',checked,'budget',budget_failures,'unreachable',unreachable)
