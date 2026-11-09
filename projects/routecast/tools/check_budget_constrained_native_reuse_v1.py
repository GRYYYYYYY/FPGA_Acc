"""Simple-path exhaustive oracle for bounded Pareto retained-tree expansion."""
import copy,json,random,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from compiled_criticality_tree_v1 import Graph,BINARY
from budget_constrained_native_reuse_expand_v1 import expand
from budget_constrained_native_reuse_initializer_v1 import initialize
from check_native_channel_reuse_initializer_v2 import csr,record
from source_binding_v2 import closure
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/budget_constrained_native_reuse_contract_v1_2026-10-19'
def main():
 D.mkdir(exist_ok=False);rng=random.Random(2026101911);counts={};path_cases=0
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
  a=expand(t,7,budget,f,kinds,novel,penalty,range(len(inc)));counts[a['status']]=counts.get(a['status'],0)+1
  if feasible:
   assert a['committed'];best=min(x[0] for x in feasible);assert a['objective_numerator']==best and any(x[0]==best and x[1]==a['raw'] for x in feasible);assert all(t.parents[n]==parent for n,parent in snapshot[0].items());path_cases+=len(feasible)
  else:assert not a['committed'] and a['status']=='NO_BUDGET_PATH_FOR_FIXED_TREE' and snapshot==(t.parents,t.arrival)
  limited=g.tree(0);limited.parents=snapshot[0].copy();limited.arrival=snapshot[1].copy();a=expand(limited,7,10000,f,kinds,novel,penalty,range(len(inc)),max_labels=1);assert a['status']=='UNKNOWN_LABEL_LIMIT' and not a['committed'] and snapshot==(limited.parents,limited.arrival);g.close()
 f,w,s=csr(5,{(0,2):1,(1,2):3,(1,3):1,(2,4):2,(3,4):1});g=Graph(f,w,[0]*5);old=[record(0,0,4,[s[0,2],s[2,4]],w)];q=[dict(connection_id=0,net_id=0,source=1,sink=4)];fb={0:record(0,1,4,[s[1,3],s[3,4]],w)['answer']};snapshot=copy.deepcopy(old);a=initialize(g,f,['SOURCE','SOURCE','CHANX','CHANX','SINK'],q,old,{0:2},range(len(w)),lambda:copy.deepcopy(fb));assert not a['whole_NET_fallback'] and a['answers']==fb and old==snapshot;g.close()
 (D/'verification.json').write_text(json.dumps(dict(status='BUDGET_CONSTRAINED_REUSE_EQUALS_EXHAUSTIVE_FROZEN_TREE_SIMPLE_PATH_ORACLE',random_graphs=150,feasible_paths_enumerated=path_cases,status_counts=counts,forced_unknown_without_tree_mutation_cases=150,unconstrained_overbudget_fixture_solved_within_budget_without_fallback=True,bindings={**closure([Path(__file__)]),str(BINARY):sha(BINARY)},scope='Exact per-expansion raw-budget and lex novelty objective when FOUND or exhausted; label exhaustion UNKNOWN. No wholeNET global optimum, no forecast quality/native success.'),indent=2)+'\n');print('PASS',counts,'paths',path_cases)
if __name__=='__main__':main()
