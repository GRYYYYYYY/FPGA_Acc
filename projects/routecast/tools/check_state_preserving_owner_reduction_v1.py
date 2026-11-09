import json,random,itertools
from pathlib import Path
from state_preserving_owner_reduction_v1 import reduce_witness
from pre_route_endpoints import sha

def main():
 R=Path(__file__).resolve().parents[1];D=R/'experiments/state_preserving_owner_reduction_contract_v1_2026-10-19';D.mkdir(exist_ok=True);assert not (D/'verification.json').exists();rng=random.Random(742903);cases=0
 for _ in range(300):
  active={(n,rng.randrange(3)) for n in range(7)};cuts=[]
  for net in range(3):
   own=[n for n,t in active if t==net]
   if own:
    for _ in range(3):cuts.append(dict(NET=net,nodes=rng.sample(own,rng.randint(1,len(own)))))
  active&={(n,c['NET']) for c in cuts for n in c['nodes']};owners={n:rng.randrange(3) for n in range(7)};ownership={net:{n for n,t in owners.items() if t==net} for net in range(3)}
  out=reduce_witness(active,cuts,ownership);chosen=set(map(tuple,out['active']));assert chosen<=active and len({n for n,t in chosen})==len(chosen)
  def cover(s):return all(any((n,c['NET']) in s for n in c['nodes']) for c in cuts)
  assert cover(chosen)
  assert all(not cover(chosen-{p}) for p in chosen)
  # Every subset of the retained set except itself must fail coverage.
  assert all(not cover(set(sub)) for k in range(len(chosen)) for sub in itertools.combinations(chosen,k))
  cases+=1
 # Priority must retain existing ownership in an unconstrained two-option cut.
 out=reduce_witness([(1,0),(2,0)],[dict(NET=0,nodes=[1,2])],{0:{2},1:{1}});assert out['active']==[(2,0)]
 files=[Path(__file__).resolve(),R/'tools/state_preserving_owner_reduction_v1.py'];(D/'verification.json').write_text(json.dumps(dict(status='STATE_PRESERVING_SUBSET_REDUCTION_COVERAGE_AND_IRREDUCIBILITY_VERIFIED',cases=cases,existing_owner_fixture_pass=True,bindings={str(p):sha(p) for p in files},scope='Exhaustive retained-subset minimality on fixtures, no global actor optimum or routing proof.'),indent=2)+'\n');print('PASS',cases)
if __name__=='__main__':main()
