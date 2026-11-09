"""Independent demand-array/active-set parity and failure-atomicity fixtures."""
import json,random
from array import array
from pathlib import Path
from native_capacity_rc_search import NativeCapacityRC
from native_capacity_rc_diff_demand import NativeCapacityRCDiffDemand
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/diff_demand_contract_2026-10-07';out.mkdir();old=NativeCapacityRC.__new__(NativeCapacityRC);new=NativeCapacityRCDiffDemand.__new__(NativeCapacityRCDiffDemand)
for obj in (old,new):obj.n=64;obj.other=array('Q',[0])*64;obj.previous=set()
new.publication_calls=new.publication_writes=0;rng=random.Random(1)
for i in range(2000):
 data={node:rng.choice([0,0,1,2,(1<<64)-1]) for node in rng.sample(range(64),rng.randrange(65))};old.set_other(data);new.set_other(data);assert old.other.tobytes()==new.other.tobytes() and old.previous==new.previous;assert list(new.other)==[data.get(node,0) for node in range(64)]
class Broken:
 def items(self):yield 0,1;raise RuntimeError('fixture interrupted iterator')
bad=[{True:0},{-1:1},{64:0},{0:True},{0:-1},{0:1<<64},{0:1.0},Broken()]
for data in bad:
 before=(new.other.tobytes(),new.previous.copy(),new.publication_calls,new.publication_writes)
 for obj in (old,new):
  try:obj.set_other(data)
  except (ValueError,RuntimeError):pass
  else:raise AssertionError('invalid update accepted')
 assert before==(new.other.tobytes(),new.previous,new.publication_calls,new.publication_writes) and old.other.tobytes()==new.other.tobytes() and old.previous==new.previous
writes=new.publication_writes;new.set_other({n:new.other[n] for n in new.previous});assert new.publication_writes==writes;new.set_other({});assert not new.previous and not any(new.other)
(out/'verification.json').write_text(json.dumps(dict(checker_sha256=sha(Path(__file__)),sources={str(ROOT/'tools'/n):sha(ROOT/'tools'/n) for n in ['native_capacity_rc_search.py','native_capacity_rc_diff_demand.py']},random_full_replacements=2000,bad_inputs=len(bad),unchanged_map_zero_writes=True,clear_all=True,scope='Exact fullmap array/previous parity, validationzeroentries/bool/uint64/iteratorfailure before mutation. Serial owner, no concurrent or arbitrary foreign array mutation guarantee. Actualnative query/pipeline parity required separately.'),indent=2)+'\n');print('Diff-demand contract passed')
