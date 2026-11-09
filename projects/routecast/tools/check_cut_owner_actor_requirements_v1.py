"""Exhaust actor subsets against immutable nonactor ownership semantics."""
import json,random,itertools
from pathlib import Path
from cut_owner_actor_requirements_v1 import required_actors
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/cut_owner_actor_requirements_contract_v1_2026-10-19'
def main():
 D.mkdir(exist_ok=False);rng=random.Random(264091);checks=0
 for case in range(150):
  nets=range(rng.randint(2,5));nodes=range(rng.randint(1,7));ownership={net:set() for net in nets if rng.randrange(3)}
  for node in nodes:
   choices=[None]+list(ownership);owner=rng.choice(choices)
   if owner is not None:ownership[owner].add(node)
  allocation={node:rng.choice(list(nets)) for node in nodes if rng.randrange(2)};coverage={net for net in nets if rng.randrange(2)};answer=required_actors(allocation,ownership,coverage);required=set(answer['required_actor_NETs']);domain=sorted(set(ownership)|set(allocation.values()))
  for bits in range(1<<len(domain)):
   actors={net for i,net in enumerate(domain) if bits>>i&1};possible=True
   for node,net in allocation.items():
    if net not in actors and node not in ownership.get(net,set()):possible=False
    if any(owner!=net and owner not in actors and node in ns for owner,ns in ownership.items()):possible=False
   assert possible==(required<=actors);checks+=1
  assert answer['actors_missing_all_CID_domain_proofs']==sorted(required-coverage)
 p=R/'tools/cut_owner_actor_requirements_v1.py';bindings={str(q):sha(q) for q in (Path(__file__).resolve(),p)};(D/'verification.json').write_text(json.dumps(dict(status='FIXED_OWNER_ASSIGNMENT_ACTOR_REQUIREMENTS_EQUAL_EXHAUSTIVE_NONACTOR_IMMUTABILITY',cases=150,actor_subsets_checked=checks,bindings=bindings,scope='Necessary actor set for a fixed resource assignment, not minimum across other assignments or physical route sufficiency.'),indent=2)+'\n');print(dict(cases=150,actor_subsets=checks),flush=True)
if __name__=='__main__':main()
