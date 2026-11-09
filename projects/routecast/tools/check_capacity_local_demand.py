import json,random
from array import array
from pathlib import Path
from capacity_local_demand import CapacityAbsoluteDemand,CapacityLocalDemand
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/capacity_local_demand_contract_2026-10-07';out.mkdir(exist_ok=True);n=32;native=CapacityAbsoluteDemand.__new__(CapacityAbsoluteDemand);native.n=n;native.other=array('Q',[0])*n;native.previous=set();native.demand_epoch=native.delta_calls=native.delta_writes=native.publication_calls=native.publication_writes=0;local=CapacityLocalDemand(native);rng=random.Random(1);occupancy={};owner=set()
for k in range(2000):
 old=dict(occupancy)
 for node in rng.sample(range(n),rng.randrange(6)):occupancy[node]=rng.randrange(4)
 occupancy={node:value for node,value in occupancy.items() if value};owner=set(rng.sample(list(occupancy),rng.randrange(len(occupancy)+1)));dirty={node for node in old.keys()|occupancy.keys() if old.get(node,0)!=occupancy.get(node,0)};local.transition(occupancy,owner,dirty);expected={node:value-int(node in owner) for node,value in occupancy.items()};assert list(native.other)==[expected.get(node,0) for node in range(n)] and native.previous=={node for node,value in expected.items() if value}
 if k%53==0:
  native.set_other({})
  try:local.transition(occupancy,owner,dirty)
  except ValueError:pass
  else:raise AssertionError('stale local state accepted')
  local=CapacityLocalDemand(native);local.transition(occupancy,owner,())
class Broken:
 def __iter__(self):yield (0,1);raise RuntimeError('interrupted')
for updates in [[(True,0)],[(0,True)],[(0,1),(0,2)],[(0,1<<64)],Broken()]:
 state=(native.other.tobytes(),native.previous.copy(),native.demand_epoch,native.delta_calls,native.delta_writes)
 try:native.apply_other(native.demand_epoch,updates)
 except (ValueError,RuntimeError):pass
 else:raise AssertionError('invalid delta accepted')
 assert state==(native.other.tobytes(),native.previous,native.demand_epoch,native.delta_calls,native.delta_writes)
state=native.other.tobytes()
try:native.apply_other(native.demand_epoch-1,[(0,1)])
except ValueError:pass
else:raise AssertionError('stale epoch accepted')
assert state==native.other.tobytes()
(out/'verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),implementation_sha256=sha(ROOT/'tools/capacity_local_demand.py'),random_transitions=2000,external_reset_stale_rejection=True,invalid_delta_failure_atomicity=True,scope='Caller supplies complete occupancy dirties; missingdirty not detected byepoch. Serial validator/iterator failure nonmutating; actual fullquerytrace/digest equivalence required.'),indent=2)+'\n');print('Capacity local demand contracts passed')
