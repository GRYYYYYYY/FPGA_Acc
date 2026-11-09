"""Exhaustive independent feasible-subset check for unit-capacity restoration."""
import itertools,json
from capacity_restore_closure import restore_closure

def main():
 nets=range(3);cap={v:1 for v in range(3)}
 allocations=[{n:{v for v,owner in enumerate(owners) if owner==n} for n in nets} for owners in itertools.product([-1,0,1,2],repeat=3)]
 subsets=[{n for n in nets if mask&(1<<n)} for mask in range(8)];cases=0
 for base,cand in itertools.product(allocations,repeat=2):
  feasible=[]
  for restored in subsets:
   mixed={n:base[n] if n in restored else cand[n] for n in nets}
   if all(sum(v in nodes for nodes in mixed.values())<=1 for v in cap):feasible.append(restored)
  for seeds in subsets:
   closure,_=restore_closure(base,cand,cap,seeds)
   allowed=[s for s in feasible if seeds<=s];assert allowed
   assert closure in allowed and all(closure<=s for s in allowed)
   assert closure==set.intersection(*allowed)
   cases+=1
 print(json.dumps({'status':'unit_capacity_least_closure_exhaustive_check_pass','cases':cases,'allocations':len(allocations),'scope':'3nets3nodes all unit capacity, all legal baseline/candidate allocations and seed subsets. Closure independently compared with every feasible binary whole-net mixture. Not native quality or arbitrary-capacity minimum proof.'}))
if __name__=='__main__':main()
