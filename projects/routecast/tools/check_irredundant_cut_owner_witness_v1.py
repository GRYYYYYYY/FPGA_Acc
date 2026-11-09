"""Exhaustive feasible owner allocations retain all original cut obligations."""
import json,random,itertools
from pathlib import Path
from irredundant_cut_owner_witness_v1 import reduce_witness
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/irredundant_cut_owner_witness_contract_v1_2026-10-19'
def main():
 D.mkdir(exist_ok=False);rng=random.Random(740119);tested=removed=0
 for case in range(120):
  nets=rng.randint(1,4);nodes=list(range(rng.randint(1,5)));cuts=[dict(NET=rng.randrange(nets),nodes=rng.sample(nodes,rng.randint(1,len(nodes)))) for _ in range(rng.randint(1,7))];eligible={n:sorted({c['NET'] for c in cuts if n in c['nodes']}) for n in nodes}
  for values in itertools.product(*([None]+eligible[n] for n in nodes)):
   owners=dict(zip(nodes,values))
   if not all(any(owners[n]==c['NET'] for n in c['nodes']) for c in cuts):continue
   active={(n,net) for n,net in owners.items() if net is not None};answer=reduce_witness(active,cuts);final=set(map(tuple,answer['active']));assert final<=active and len({n for n,net in final})==len(final);assert all(any((n,c['NET']) in final for n in c['nodes']) for c in cuts)
   for pair in final:assert not all(any((n,c['NET']) in final-{pair} for n in c['nodes']) for c in cuts)
   for w in answer['irreducibility_witnesses']:
    assert w['unique_owner_cut_indices'];assert all(cuts[i]['NET']==w['NET'] and {n for n in cuts[i]['nodes'] if (n,w['NET']) in final}=={w['node']} for i in w['unique_owner_cut_indices'])
   tested+=1;removed+=len(active-final)
 bindings={str(p):sha(p) for p in (Path(__file__).resolve(),R/'tools/irredundant_cut_owner_witness_v1.py')};(D/'verification.json').write_text(json.dumps(dict(status='IRREDUNDANT_OWNER_DELETION_PRESERVES_CAPACITY_AND_ALL_CID_CUTS',bindings=bindings,feasible_owner_models_checked=tested,surplus_owners_removed=removed,scope='Finite exhaustive allocation checks plus deletion invariant; no physical graph/tree completeness.'),indent=2)+'\n');print(dict(feasible_owner_models=tested,surplus_owners_removed=removed),flush=True)
if __name__=='__main__':main()
