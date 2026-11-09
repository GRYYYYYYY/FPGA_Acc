"""Simple-path exhaustive oracle for bounded Pareto retained-tree expansion."""
import copy,json,random,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from compiled_criticality_tree_v1 import Graph,BINARY
from budget_astar_native_reuse_expand_v1 import expand
from reverse_raw_delay_bounds_v1 import ReverseBounds
from budget_astar_native_reuse_initializer_v1 import initialize
from check_native_channel_reuse_initializer_v2 import csr,record
from source_binding_v2 import closure
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/budget_astar_native_reuse_contract_v1_2026-10-19'
def main():
 D.mkdir(exist_ok=False);rng=random.Random(2026101911);counts={};path_cases=0;limited_counts={};inequalities=0
 for trial in range(150):
  n=8;edges={(0,1):rng.randrange(1,5),(1,6):rng.randrange(1,5)}
  for u in range(6):
   for v in range(1,n):
    if u!=v and rng.random()<.3:edges[u,v]=rng.randrange(0,6)
  f,inc,slots=csr(n,edges);g=Graph(f,inc,[0]*n);t=g.tree(0);t.parents[1]=(0,slots[0,1]);t.arrival[1]=inc[slots[0,1]];t.parents[6]=(1,slots[1,6]);t.arrival[6]=t.arrival[1]+inc[slots[1,6]];oldnodes={0,1,2,6};kinds=['SOURCE']+['CHANX']*5+['SINK']*2;penalty=n*max(inc,default=0)+1;novel={n:penalty for n in range(8) if kinds[n]=='CHANX' and n not in oldnodes};budget=rng.choice([0,2,6,12,30]);snapshot=(dict(t.parents),dict(t.arrival));own=set(t.arrival);feasible=[]
  def visit(u,raw,cost,seen,path):
   if raw>budget:return
   if u==7:feasible.append((cost,raw,path));return
   for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][slot]
    if v in seen or v in own or kinds[v]=='SOURCE' or kinds[v]=='SINK' and v!=7:continue
    visit(v,raw+inc[slot],cost+inc[slot]+novel.get(v,0),seen|{v},path+(slot,))
  for seed,arrival in t.arrival.items():
   if kinds[seed]!='SINK':visit(seed,arrival,arrival,{seed},())
  provider=ReverseBounds(f['row_offsets'],f['dest_ranks'],inc);h=provider.bound(7,budget);assert provider.bound(7,budget) is h and provider.hits==1
  floyd=[[0 if u==v else 10**6 for v in range(n)] for u in range(n)]
  for u in range(n):
   for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):v=f['dest_ranks'][slot];floyd[u][v]=min(floyd[u][v],inc[slot])
  for k in range(n):
   for u in range(n):
    for v in range(n):floyd[u][v]=min(floyd[u][v],floyd[u][k]+floyd[k][v])
  assert all(h.get(u)==min(floyd[u][7],budget+1) for u in range(n))
  for u in range(n):
   for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):assert h.get(u)<=inc[slot]+h.get(f['dest_ranks'][slot]);inequalities+=1
  a=expand(t,7,budget,f,kinds,novel,penalty,range(len(inc)));counts[a['status']]=counts.get(a['status'],0)+1
  if feasible:
   assert a['committed'];best=min(x[0] for x in feasible);assert a['objective_numerator']==best and any(x[0]==best and x[1]==a['raw'] for x in feasible);assert all(t.parents[n]==parent for n,parent in snapshot[0].items());path_cases+=len(feasible)
  else:assert not a['committed'] and a['status']=='NO_BUDGET_PATH_FOR_FIXED_TREE' and snapshot==(t.parents,t.arrival)
  limited=g.tree(0);limited.parents=snapshot[0].copy();limited.arrival=snapshot[1].copy();a=expand(limited,7,10000,f,kinds,novel,penalty,range(len(inc)),max_labels=1);assert not a['committed'] and a['status'] in ['UNKNOWN_LABEL_LIMIT','NO_BUDGET_PATH_FOR_FIXED_TREE'] and snapshot==(limited.parents,limited.arrival);limited_counts[a['status']]=limited_counts.get(a['status'],0)+1;g.close()
 f,w,s=csr(5,{(0,2):1,(1,2):3,(1,3):1,(2,4):2,(3,4):1});g=Graph(f,w,[0]*5);old=[record(0,0,4,[s[0,2],s[2,4]],w)];q=[dict(connection_id=0,net_id=0,source=1,sink=4)];fb={0:record(0,1,4,[s[1,3],s[3,4]],w)['answer']};snapshot=copy.deepcopy(old);a=initialize(g,f,['SOURCE','SOURCE','CHANX','CHANX','SINK'],q,old,{0:2},range(len(w)),lambda:copy.deepcopy(fb));assert not a['whole_NET_fallback'] and a['answers']==fb and old==snapshot;g.close()
 x=[1];provider=ReverseBounds([0,1,1],[1],x);a=provider.bound(1,20);original_context=provider.context;x[0]=9;assert provider.bound(1,20) is a and a.get(0)==1;other=ReverseBounds([0,1,1],[1],x);assert other.context!=original_context and other.bound(1,20).get(0)==9;assert provider.bound(1,21).cap==22
 (D/'verification.json').write_text(json.dumps(dict(status='ADMISSIBLE_REVERSE_BOUND_ASTAR_REUSE_EQUALS_FLOYD_AND_EXHAUSTIVE_FROZEN_TREE_ORACLE',random_graphs=150,feasible_paths_enumerated=path_cases,status_counts=counts,small_limit_status_counts=limited_counts,small_limit_never_mutates_tree=True,original_edge_bound_inequalities_checked=inequalities,immutable_snapshot_and_cache_isolation_verified=True,unconstrained_overbudget_fixture_solved_within_budget_without_fallback=True,bindings={**closure([Path(__file__)]),str(BINARY):sha(BINARY)},scope='Exact per-expansion raw-budget and lex novelty objective when FOUND or exhausted; label exhaustion UNKNOWN. No wholeNET global optimum, no forecast quality/native success.'),indent=2)+'\n');print('PASS',counts,'paths',path_cases,'small limit',limited_counts,'Bellman',inequalities)
if __name__=='__main__':main()
