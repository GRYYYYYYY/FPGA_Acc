"""Independent Cartesian resource-objective oracle, no search-code reuse."""
import pathlib,json,random,itertools,hashlib
from collections import defaultdict
from coupled_NET_tree_resource_select_v2 import select
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/coupled_NET_tree_resource_select_core_v2_2026-10-19'
def main():
 O.mkdir(exist_ok=False);rng=random.Random(191022);assignments=0;counts=defaultdict(int)
 for trial in range(400):
  nodes=range(7);capacities={v:rng.choice([1,2,3]) for v in nodes};spans={v:rng.randrange(5) for v in nodes};fixed={v:rng.randrange(capacities[v]+1) for v in nodes};banks={net:[dict(nodes=frozenset(v for v in nodes if rng.random()<.35),excess=rng.randrange(30)) for _ in range(rng.randrange(5))] for net in range(rng.randrange(1,5))};nets=sorted(banks);best=None;feasible=[]
  for mask in itertools.product(*(range(len(banks[n])) for n in nets)):
   assignments+=1;owners={v:set() for v in nodes};resource=0;rc=0
   for n,i in zip(nets,mask):
    c=banks[n][i];rc+=c['excess']
    for v in c['nodes']:owners[v].add(n);resource+=spans[v]
   if all(len(owners[v])+fixed[v]<=capacities[v] for v in nodes):
    value=(resource,rc);feasible.append((value,mask));best=value if best is None else min(best,value)
  actual=select(banks,capacities,spans,fixed);assert actual['objective']==best and actual['status']==('OPTIMAL_WITHIN_CANDIDATES' if best is not None else 'INFEASIBLE_WITHIN_CANDIDATES');counts[actual['status']]+=1
  if actual['selection'] is not None:assert (actual['objective'],tuple(actual['selection'][n] for n in nets)) in feasible
 # RC-only optimum uses a larger tree; lex resource optimum must retain smaller tree.
 bank={0:[dict(nodes=frozenset([0,1]),excess=0),dict(nodes=frozenset([0]),excess=100)]};assert select(bank,{0:1,1:1},{0:5,1:5})['selection']=={0:1}
 # Same node is charged once per NET, twice across two NETs of capacity2.
 x=dict(nodes=frozenset([0]),excess=0);assert select({0:[x],1:[x]},{0:2},{0:7})['objective']==(14,0)
 # A strict resource bound is not a weighted sum: secondary can be arbitrarily large.
 bank[0][1]['excess']=10**30;assert select(bank,{0:1,1:1},{0:5,1:5})['selection']=={0:1}
 assert select({0:[x,x],1:[x,x]},{0:2},{0:7},max_states=3)['status']=='UNKNOWN_STATE_LIMIT'
 rejected=0
 for value in [-1,True,1.5]:
  try:select({0:[x]},{0:2},{0:value})
  except ValueError:rejected+=1
  else:raise AssertionError('invalid span admitted')
 out=dict(status='LEX_UNIQUE_NET_RESOURCE_AND_RC_SELECTION_EXACT_CARTESIAN_PASS',fixtures=400,oracle_combinations=assignments,status_counts=dict(counts),invalid_spans_rejected=rejected,RC_resource_conflict_fixture_pass=True,per_NET_sharing_and_cross_NET_distinct_counting_pass=True,state_limit_remains_unknown=True,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [pathlib.Path(__file__).resolve(),R/'tools/coupled_NET_tree_resource_select_v2.py']},scope='Finite admitted resource columns; complete physical tree/RC admission remains separate. No large-graph performance, routing quality or full-graph optimum claim.')
 (O/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
