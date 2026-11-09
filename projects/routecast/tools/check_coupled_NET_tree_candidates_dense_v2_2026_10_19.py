"""Independent simple-path/tree/Cartesian oracle for finite coupled banks."""
import pathlib,json,random,itertools,hashlib
from collections import Counter
from coupled_NET_tree_candidates_v1 import tree_candidate,select
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/coupled_NET_tree_candidates_dense_core_v2_2026-10-19'
def oracle_tree(edges,source,paths,floors,budgets):
 byid={e[0]:e[1:] for e in edges};parent={};nodes={source};total=0
 for sink,path in paths.items():
  current=source;seen={source};value=0
  for eid in path:
   a,b,w=byid[eid]
   if a!=current or b in seen:return None
   seen.add(b);nodes.add(b)
   if b in parent and parent[b]!=(a,eid):return None
   parent[b]=(a,eid);current=b;value+=w
  if current!=sink or value<floors[sink] or value>budgets[sink]:return None
  total+=value-floors[sink]
 return nodes,total

def brute(banks,capacities,fixed):
 nets=sorted(banks);best=None;assignments=0
 for choice in itertools.product(*(range(len(banks[n])) for n in nets)):
  assignments+=1;occupancy={v:set() for v in capacities};total=0
  for net,ci in zip(nets,choice):
   nodes,cost=banks[net][ci];total+=cost
   for v in nodes:occupancy[v].add(net)
  if all(len(occupancy[v])+fixed.get(v,0)<=capacities[v] for v in capacities):
   if best is None or total<best:best=total
 return best,assignments

def paths(edges,source,sink):
 out=[]
 def visit(u,seen,route,cost):
  if u==sink:out.append((tuple(route),cost));return
  for eid,a,b,w in edges:
   if a==u and b not in seen:visit(b,seen|{b},route+[eid],cost+w)
 visit(source,{source},[],0);return sorted(out)

def main():
 O.mkdir(exist_ok=False);rng=random.Random(191020);counts=Counter();enumerated=0
 for trial in range(300):
  kinds={0:'SOURCE',1:'SOURCE',2:'CHANX',3:'CHANY',4:'CHANX',5:'SINK',6:'SINK'};edges=[]
  for a in range(5):
   for b in range(2,7):
    if a!=b and rng.random()<.55:edges.append((len(edges),a,b,rng.randrange(4)))
  for a,b in [(0,2),(1,2),(2,5),(2,6)]:
   if not any(u==a and v==b for _,u,v,_ in edges):edges.append((len(edges),a,b,rng.randrange(4)))
  caps={v:(rng.choice([1,2]) if v in [2,3,4] else 3) for v in kinds};fixed={rng.choice([2,3,4]):rng.randrange(2)};banks={};expected={}
  for net in range(rng.choice([2,3])):
   source=net%2;sinks=[5,6] if rng.random()<.5 else [rng.choice([5,6])];routes={s:paths(edges,source,s) for s in sinks};floors={s:min((c for _,c in routes[s]),default=0) for s in sinks};budgets={s:floors[s]+20 for s in sinks};bank=[];ref=[]
   for combo in itertools.product(*(routes[s] for s in sinks)):
    selected={s:p[0] for s,p in zip(sinks,combo)};truth=oracle_tree(edges,source,selected,floors,budgets)
    try:c=tree_candidate(edges,source,selected,floors,budgets,caps,kinds)
    except ValueError:assert truth is None;counts['rejected_tree_assignments']+=1;continue
    assert truth is not None and c['nodes']==truth[0] and c['excess']==truth[1];bank.append(c);ref.append(truth);counts['admitted_trees']+=1
    if len(bank)==6:break
   banks[net]=bank;expected[net]=ref
  best,assignments=brute(expected,caps,fixed);enumerated+=assignments;actual=select(banks,caps,fixed,max_states=100000)
  assert actual['excess']==best and actual['status']==('INFEASIBLE_WITHIN_CANDIDATES' if best is None else 'OPTIMAL_WITHIN_CANDIDATES');counts[actual['status']]+=1
  if actual['selection'] is not None:
   chosen={n:[expected[n][i]] for n,i in actual['selection'].items()};assert brute(chosen,caps,fixed)[0]==best
  limited=select(banks,caps,fixed,max_states=1)
  if limited['status']=='UNKNOWN_STATE_LIMIT':counts['state_limit_unknown']+=1
 # Shared prefix must consume one node per NET, not one node per sink.
 e=[(0,0,2,1),(1,2,3,1),(2,2,4,1)];k={0:'SOURCE',2:'CHANX',3:'SINK',4:'SINK'};cap={v:1 for v in k}
 c=tree_candidate(e,0,{3:[0,1],4:[0,2]},{3:2,4:2},{3:2,4:2},cap,k);assert select({0:[c]},cap)['status']=='OPTIMAL_WITHIN_CANDIDATES'
 # No shared mandatory channel per NET, yet 3NETs choosing between 2channels is infeasible.
 e=[];k={0:'SOURCE',1:'SOURCE',2:'SOURCE',3:'CHANX',4:'CHANY',5:'SINK',6:'SINK',7:'SINK'};cap={v:1 for v in k};bank={}
 for net in range(3):
  bank[net]=[]
  for chan in [3,4]:
   a=len(e);e.extend([(a,net,chan,0),(a+1,chan,net+5,0)])
   bank[net].append(tree_candidate(e,net,{net+5:[a,a+1]},{net+5:0},{net+5:0},cap,k))
 assert all(not (set.intersection(*(set(c['nodes']) for c in b))&{3,4}) for b in bank.values());assert select(bank,cap)['status']=='INFEASIBLE_WITHIN_CANDIDATES'
 # Search cutoff after the first incumbent must still report UNKNOWN.
 assert select({0:bank[0],1:bank[1]},cap,max_states=3)['status']=='UNKNOWN_STATE_LIMIT'
 # Corrupt physical paths, budgets, capacities, and merged parents must reject.
 rejected=0
 def reject(fn):
  nonlocal rejected
  try:fn()
  except ValueError:rejected+=1;return
  raise AssertionError('accepted corruption')
 for route in [[999],[0],[1,0],[0,0]]:reject(lambda route=route:tree_candidate(e,0,{5:route},{5:0},{5:0},cap,k))
 reject(lambda:tree_candidate(e,0,{5:[0,1]},{5:1},{5:2},cap,k))
 reject(lambda:tree_candidate(e,0,{5:[0,1]},{5:0},{5:0},cap|{3:0},k))
 reject(lambda:select(bank,cap,{3:2}));reject(lambda:select(bank,cap,max_states=0))
 out=dict(status='FINITE_COUPLED_NET_BANK_SOLVER_MATCHES_INDEPENDENT_CARTESIAN_ORACLE',random_graphs=300,counts=dict(counts),oracle_assignments=enumerated,invalid_input_rejections=rejected,shared_prefix_unique_NET_occupancy_pass=True,no_mandatory_overlap_but_infeasible_fixture_pass=True,incumbent_at_state_limit_remains_unknown=True,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [pathlib.Path(__file__).resolve(),R/'tools/coupled_NET_tree_candidates_v1.py']},scope='Finite admitted complete trees on small directed graphs including cycles and zero costs; no MMC scale, full-graph candidate completeness or quality claim.')
 (O/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
