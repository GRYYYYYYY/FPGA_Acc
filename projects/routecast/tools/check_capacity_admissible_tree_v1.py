"""Independent exhaustive simple-suffix oracle for hard-mask weighted budget search."""
import random,json,hashlib,copy
from fractions import Fraction
from types import SimpleNamespace
from pathlib import Path
from capacity_admissible_tree_v1 import CapacityMask,Graph
R=Path(__file__).resolve().parents[1];D=R/'experiments/capacity_admissible_tree_contract_v1_2026-10-20'
def original(n,arcs,initial):
 offsets=[0];dest=[];inc=[]
 for u in range(n):
  for a,v,w in arcs:
   if a==u:dest.append(v);inc.append(w)
  offsets.append(len(dest))
 return SimpleNamespace(n=n,offsets=offsets,dest=dest,inc=inc,initial=initial,repair_bounds=None)
def oracle(tree,target,c,prices,budget,mask):
 best=None;p,q=c.numerator,c.denominator;owned=set(tree.arrival)
 def walk(u,delay,congestion,visited):
  nonlocal best
  if delay>budget:return
  if u==target:
   value=p*delay+(q-p)*congestion
   if best is None or value<best:best=value
   return
  for edge in range(tree.offsets[u],tree.offsets[u+1]):
   v=tree.dest[edge]
   if v in visited or v in owned or not mask[v]:continue
   walk(v,delay+tree.inc[edge],congestion+prices.get(v,0),visited|{v})
 for seed,delay in tree.arrival.items():walk(seed,delay,0,{seed})
 return best
def main():
 D.mkdir(exist_ok=False);rng=random.Random(20261020);checks=0;shared=0;reachable=0;blocked=0
 for trial in range(120):
  n=rng.randrange(3,8);arcs=[(u,v,rng.randrange(5)) for u in range(n) for v in range(n) if u!=v and rng.random()<.33];base=original(n,arcs,[rng.randrange(3) for _ in range(n)]);caps=[rng.randrange(1,4) for _ in range(n)];ledger={i:rng.randrange(5) for i in range(n)};ledger[0]=max(1,ledger[0]);snapshot=dict(ledger);mask=CapacityMask(caps,ledger,{0});ledger[0]+=100;assert mask[0]==1;ledger=snapshot
  for c in [Fraction(0),Fraction(1,2),Fraction(1)]:
   graph=Graph(base,mask);tree=graph.tree(0);prices={i:rng.randrange(8) for i in range(n)}
   for target in [rng.randrange(1,n),rng.randrange(1,n)]:
    budget=rng.randrange(2,17);before=(dict(tree.arrival),dict(tree.parents));expected=oracle(tree,target,c,prices,budget,mask);result=tree.expand(target,c,prices,budget);checks+=1;shared+=len(before[0])>1
    if expected is None:
     assert result['status']=='NO_BUDGET_PATH_FOR_FIXED_TREE' and not result['committed'];assert before==(tree.arrival,tree.parents);blocked+=1
    else:
     reachable+=1;assert result['committed'] and result['objective_numerator']==expected and result['raw']<=budget;assert all(mask[i] for i in tree.arrival)
     # Exact overflow invariant for the entire candidate support, owner counted once.
     new=dict(snapshot)
     for i in {0}-set(tree.arrival):new[i]-=1
     for i in set(tree.arrival)-{0}:new[i]=new.get(i,0)+1
     assert sum(max(0,v-caps[i]) for i,v in new.items())<=sum(max(0,v-caps[i]) for i,v in snapshot.items())
     u=0;value=base.initial[0]
     for edge in result['path_slots']:assert base.offsets[u]<=edge<base.offsets[u+1];u=base.dest[edge];value+=base.inc[edge]
     assert u==target and value==result['raw']
 mask=CapacityMask([1,1,1],{0:3,1:1},{0});assert mask[0] and not mask[1] and mask[2]
 try:CapacityMask([1,1],{0:0},{0})
 except ValueError:pass
 else:raise AssertionError('nonowner seed accepted')
 base=original(3,[(0,1,1),(1,2,1)],[0,0,0]);graph=Graph(base,CapacityMask([1]*3,{0:1},{0}),max_labels=1);tree=graph.tree(0);before=copy.deepcopy((tree.arrival,tree.parents));answer=tree.expand(2,Fraction(1,2),{},10);assert answer['status']=='UNKNOWN_LABEL_LIMIT' and before==(tree.arrival,tree.parents)
 bad=Graph(base,CapacityMask([1]*3,{0:1,1:1},{0})).tree(0);bad.arrival[1]=1
 try:bad.expand(2,Fraction(1),{},10)
 except ValueError:pass
 else:raise AssertionError('forbidden seed accepted')
 sources=[Path(__file__),R/'tools/capacity_admissible_tree_v1.py',R/'tools/weighted_budget_pareto_search_v1.py',R/'tools/reverse_raw_delay_bounds_v1.py'];bindings={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources};result=dict(status='EXHAUSTIVE_MASKED_BUDGET_OBJECTIVE_SHARED_TREE_AND_UNKNOWN_ATOMICITY_PASS',random_graphs=120,oracle_queries=checks,shared_tree_queries=shared,found=reachable,no_budget_path=blocked,unknown_preserves_tree=True,forbidden_seed_rejected=True,existing_overflow_retention_and_no_new_overflow_pass=True,bindings=bindings,scope='Primitive hard-mask bounded search qualified on independent exhaustive fixtures; no production forecast or general weighted optimality beyond fixed tree suffix. No raw-budget or overflow guard relaxation.')
 (D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
