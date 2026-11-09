"""Random DAG all-path choices versus independent full-combination reference."""
import random,json,copy
from pathlib import Path
from fractions import Fraction
from criticality_whole_net_choice_reference_v1 import choose as reference
from criticality_whole_net_choice_undo_v1 import choose
from pre_route_endpoints import sha
rng=random.Random(383141);cases=0
for trial in range(240):
 n=rng.randrange(4,8);adj={};edge=0
 for u in range(n-1):
  for v in range(u+1,n):
   if v==u+1 or rng.random()<.55:adj.setdefault(u,[]).append((edge,v,rng.randrange(7),0));edge+=1
 sinks=[n-2,n-1];candidates={s:[] for s in sinks}
 def walk(u,path):
  if u in candidates:candidates[u].append(path)
  for e,v,_,_ in adj.get(u,[]):walk(v,path+[e])
 walk(0,[])
 # Last chain node paths yield mutually compatible old tree.
 chain=[];old={}
 for u in range(n-1):
  chain.append(next(e for e,v,_,_ in adj[u] if v==u+1))
  if u+1 in sinks:old[u+1]=chain.copy()
 budgets={s:100 for s in sinks};pins=[(s,rng.choice([Fraction(0),Fraction(1),Fraction(1,3),Fraction(7,8)])) for s in sinks]
 if trial%2==0:pins.append((sinks[0],Fraction(2,7)))
 prices={u:rng.randrange(40) for u in range(n)};frozen=copy.deepcopy((adj,old,candidates,pins,prices))
 expected=reference(adj,0,budgets,old,candidates,pins,prices,initial_raw=2,max_states=100000)
 result=choose(adj,0,budgets,old,candidates,pins,prices,initial_raw=2,max_states=100000)
 assert result['chosen_score']==expected['chosen_score'] and result['search_status']=='OPTIMAL_WITHIN_SUPPLIED_CANDIDATES'
 assert (adj,old,candidates,pins,prices)==frozen
 limited=choose(adj,0,budgets,old,candidates,pins,prices,initial_raw=2,max_states=1)
 assert limited['status']=='RETAIN' and limited['paths']==old and limited['search_status']=='UNKNOWN_STATE_LIMIT';cases+=1
out=Path('experiments/criticality_whole_net_choice_undo_contract_v1_2026-10-10');out.mkdir()
files=[Path(__file__).resolve()]+[Path('tools')/x for x in ['criticality_whole_net_choice_undo_v1.py','criticality_whole_net_choice_reference_v1.py','budget_NET_gate_reference_v1.py']]
(out/'verification.json').write_text(json.dumps(dict(bindings={str(p.resolve()):sha(p) for p in files},random_dags=cases,all_exhausted_scores_equal_independent_combination_reference=True,state_cap_retains_old_and_no_input_mutation=True,scope='Small random DAG contract; state count definition differs full-product reference, no capped-state equivalence or MMC speed claims.'),indent=2)+'\n');print('CRITICALITY UNDO CONTRACT PASS',cases)
