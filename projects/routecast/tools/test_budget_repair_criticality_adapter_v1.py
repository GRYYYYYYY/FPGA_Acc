"""Actual compiled Tree compatibility and bounded-repair exhaustive contract."""
import json,random,copy,hashlib
from pathlib import Path
from fractions import Fraction as F
from compiled_criticality_tree_v1 import Graph as OriginalGraph,BINARY
from budget_repair_criticality_tree_v1 import Graph
from retained_criticality_tree_seed_v1 import seed
from test_weighted_budget_pareto_search_v1 import build,enumerate_paths
R=Path(__file__).resolve().parents[1];D=R/'experiments/budget_repair_criticality_adapter_contract_v1_2026-10-19'
def main():
 D.mkdir(exist_ok=False);rng=random.Random(678901);normal=repair=repaired=no_path=unknown=0
 for trial in range(200):
  n=5;edges=[(u,v,rng.randrange(5)) for u in range(n) for v in range(n) if u!=v and rng.random()<.35];frozen=trial%2==0
  if frozen:edges=[x for x in edges if x[:2]!=(0,1)]+[(0,1,1)]
  offsets,dest,raw=build(n,edges);fields=dict(row_offsets=offsets,dest_ranks=dest,capacities=[1]*n);g=Graph(fields,raw,[0]*n);old=OriginalGraph(fields,raw,[0]*n);t=g.tree(0);o=old.tree(0)
  if frozen:
   edge=next(e for e in range(offsets[0],offsets[1]) if dest[e]==1);seed(t,[(1,[edge],1)]);seed(o,[(1,[edge],1)])
  prices={i:rng.randrange(15) for i in range(n)};c=[F(0),F(1,4),F(1,2),F(3,4),F(1)][trial%5];budget=rng.randrange(1,10);before=(t.parents.copy(),t.arrival.copy());expected=enumerate_paths(offsets,dest,raw,[1]*n,t.arrival,n-1,c,prices,budget);result=o.expand(n-1,c,prices,budget);actual=t.expand(n-1,c,prices,budget)
  if result['status']!='RETAIN_RAW_BUDGET':
   normal+=1;assert actual==result and t.parents==o.parents and t.arrival==o.arrival and not g.repair_events
  else:
   repair+=1;assert o.parents==before[0] and o.arrival==before[1]
   if expected:repaired+=1;assert actual['committed'] and actual['objective_numerator']==min(x[0] for x in expected) and actual['raw']<=budget
   else:no_path+=1;assert actual['status']=='NO_BUDGET_PATH_FOR_FIXED_TREE' and (t.parents,t.arrival)==before
   limited=g.tree(0);limited.parents=before[0].copy();limited.arrival=before[1].copy();g.repair_label_limit=1;small=limited.expand(n-1,c,prices,budget)
   assert not small['committed'] and (limited.parents,limited.arrival)==before
   if small['status']=='UNKNOWN_LABEL_LIMIT':unknown+=1
   else:assert small['status']=='NO_BUDGET_PATH_FOR_FIXED_TREE' and not expected
  g.close();old.close()
 offsets,dest,raw=build(4,[(0,1,1),(1,3,1),(0,2,3),(2,3,2)]);f=dict(row_offsets=offsets,dest_ranks=dest,capacities=[1]*4);g=Graph(f,raw,[0]*4);o=OriginalGraph(f,raw,[0]*4);t=g.tree(0);assert o.tree(0).expand(3,F(1,2),{1:100},2)['status']=='RETAIN_RAW_BUDGET';assert t.expand(3,F(1,2),{1:100},2)['raw']==2;g.close();o.close()
 assert repair>0 and repaired>0 and unknown>0
 files=[Path(__file__).resolve(),R/'tools/budget_repair_criticality_tree_v1.py',R/'tools/compiled_criticality_tree_v1.py',R/'tools/weighted_budget_pareto_search_v1.py',BINARY];(D/'verification.json').write_text(json.dumps(dict(status='ACTUAL_COMPILED_PRIMARY_NORMAL_EQUIVALENCE_AND_BOUNDED_REPAIR_CONTRACT_PASS',random_graphs=200,unchanged_normal_compiled_cases=normal,postbudget_cases=repair,repaired_feasible_cases=repaired,fixed_tree_no_path=no_path,forced_UNKNOWN_cases=unknown,original_rejection_does_not_mutate_tree=True,shared_seed_assignment_compatibility=True,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='Adapter contract against actual compiled library; no fullNET injected-fallback test or real forecast quality admission yet.'),indent=2)+'\n');print(normal,repair,repaired,no_path,unknown)
if __name__=='__main__':main()
