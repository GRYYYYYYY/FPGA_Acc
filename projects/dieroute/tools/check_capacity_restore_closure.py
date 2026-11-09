"""Exhaustively compare small allocations against independent occupancy counts."""
import itertools,json
from capacity_restore_closure import restore_closure

def legal(mapping,cap):
 return all(sum(node in nodes for nodes in mapping.values())<=value for node,value in cap.items())
def main():
 subsets=[frozenset(n for n in range(3) if mask&(1<<n)) for mask in range(8)]
 cases=0
 for capacities in itertools.product([1,2],repeat=3):
  cap=dict(enumerate(capacities));allocations=[dict(enumerate(v)) for v in itertools.product(subsets,repeat=2) if legal(dict(enumerate(v)),cap)]
  for base,cand in itertools.product(allocations,repeat=2):
   for seeds in [set(),{0},{1},{0,1}]:
    restored,waves=restore_closure(base,cand,cap,seeds)
    assert seeds<=restored<=set(base)
    mixed={n:base[n] if n in restored else cand[n] for n in base}
    assert legal(mixed,cap)
    assert len(waves)<=len(base)+1
    assert all(b['restored_nets']>a['restored_nets'] for a,b in zip(waves,waves[1:]))
    assert restore_closure(base,cand,cap,seeds)==(restored,waves)
    cases+=1
 for args in [({0:{0}},{1:{0}},{0:1},{0}),({0:{0}},{0:{0}},{0:1},{1}),({0:{0},1:{0}},{0:set(),1:set()},{0:1},{0})]:
  try:restore_closure(*args)
  except ValueError:pass
  else:raise AssertionError('Invalid input accepted')
 print(json.dumps({'status':'exhaustive_small_allocation_checks_pass','cases':cases,'scope':'Capacity,termination,seed retention,determinism and invalid-input rejection only; no native QoR or minimality claim.'}))
if __name__=='__main__':main()
