"""Independent Cartesian-product oracle on small multidimensional domains."""
import json,random,itertools,hashlib
from collections import Counter
from pathlib import Path
from terminal_resource_assignment_v1 import solve
R=Path(__file__).resolve().parents[1]
out=R/'experiments/terminal_resource_assignment_core_v1_2026-10-18';out.mkdir()
rng=random.Random(20261018)
for trial in range(500):
 caps={p:rng.randrange(3) for p in range(rng.randrange(1,6))}
 options={r:{o:{p for p in caps if rng.randrange(2)} for o in range(rng.randrange(4))} for r in range(rng.randrange(6))}
 original=repr((options,caps));actual=solve(options,caps);oracle=False
 for values in itertools.product(*(list(options[r]) for r in options)):
  used=Counter(p for r,o in zip(options,values) for p in options[r][o])
  if all(n<=caps[p] for p,n in used.items()):oracle=True;break
 assert actual['feasible']==oracle and repr((options,caps))==original
 if oracle:
  assignment=actual['assignment'];assert set(assignment)==set(options)
  used=Counter(p for r,o in assignment.items() for p in options[r][o])
  assert all(n<=caps[p] for p,n in used.items())
for caps,options in [({0:-1},{0:{0:{0}}}),({0:1},{0:{0:{1}}})]:
 try:solve(options,caps)
 except ValueError:pass
 else:raise AssertionError('invalid input admitted')
paths=[Path(__file__),R/'tools/terminal_resource_assignment_v1.py']
with (out/'verification.json').open('x') as stream:
 json.dump(dict(status='pass',random_graphs=500,invalid_fixtures=2,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}),stream,indent=2)
print('500 RESOURCE ASSIGNMENT ORACLES PASS',flush=True)
