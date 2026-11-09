"""Independent per-node user-set cost and exhaustive tree combinations."""
import random,json,itertools
from fractions import Fraction
from pathlib import Path
from criticality_whole_net_choice_reference_v1 import choose,score
from pre_route_endpoints import sha
rng=random.Random(28173);cases=0;accepted=0
# Two sinks and a shared prefix versus individually expensive direct edges.
adj={0:[(0,1,1,0),(1,2,4,0),(2,3,4,0)],1:[(3,2,1,0),(4,3,1,0)]}
options={2:[[1],[0,3]],3:[[2],[0,4]]};old={2:[1],3:[2]};budgets={2:8,3:8}
for trial in range(320):
 pins=[(2,rng.choice([Fraction(0),Fraction(1),Fraction(1,4),Fraction(7,8)])),(3,rng.choice([Fraction(0),Fraction(1),Fraction(1,2)]))]
 if trial%3==0:pins.append((2,Fraction(3,8))) # duplicate physical sink, distinct pin timing
 price={u:rng.randrange(20) for u in [1,2,3]}
 costs={}
 for a,b in itertools.product(options[2],options[3]):
  paths={2:a,3:b};users={};raw={};parents={};valid=True
  for sink,path in paths.items():
   u=0;raw[sink]=0
   for e in path:
    arc=next(x for x in adj[u] if x[0]==e);v=arc[1]
    if v in parents and parents[v]!=(u,e):valid=False
    parents[v]=u,e;raw[sink]+=arc[2];u=v
  if not valid:continue
  for i,(sink,c) in enumerate(pins):
   u=0
   for e in paths[sink]:u=next(x[1] for x in adj[u] if x[0]==e);users.setdefault(u,[]).append(i)
  expected=sum((c*raw[s] for s,c in pins),Fraction(0))+sum(((1-max(pins[i][1] for i in ix))*price[u] for u,ix in users.items()),Fraction(0))
  assert score(adj,0,paths,pins,price)==expected
  costs[tuple(a),tuple(b)]=expected
 result=choose(adj,0,budgets,old,options,pins,price);cases+=1
 assert result['chosen_score']==min(costs.values())
 assert result['chosen_score']<=result['old_score']
 accepted+=result['status']=='ACCEPT_STRICT_IMPROVEMENT'
 limited=choose(adj,0,budgets,old,options,pins,price,max_states=1)
 assert limited['status']=='RETAIN' and limited['search_status']=='UNKNOWN_STATE_LIMIT' and limited['paths']==old
out=Path('experiments/criticality_whole_net_choice_contract_v1_2026-10-10');out.mkdir()
files=[Path(__file__).resolve(),Path(__file__).with_name('criticality_whole_net_choice_reference_v1.py').resolve(),Path(__file__).with_name('budget_NET_gate_reference_v1.py').resolve()]
(out/'verification.json').write_text(json.dumps(dict(bindings={str(p):sha(p) for p in files},cases=cases,accepted=accepted,independent_user_set_score_and_combination_optimum_pass=True,duplicate_sink_per_pin_weight_pass=True,state_limit_old_retention_pass=True,scope='Reference supplied-candidate enumeration. Not native dynamic timing, old unweighted union equivalence, arbitrary graph tree optimum, full MMC or speed evidence.'),indent=2)+'\n')
print('WHOLE NET CRITICALITY CHOICE PASS',cases,accepted)
