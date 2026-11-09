"""Independent exact-lattice check with repeated and distinct fractional costs."""
import random,json
from fractions import Fraction as F
from math import lcm
from pathlib import Path
from integer_rc_context import IntegerRC as Old
from integer_rc_context_memo import IntegerRC as New
from pre_route_endpoints import sha
rng=random.Random(20261007)
class RC:
 def __init__(self):
  self.nodes=[(F(rng.randrange(7),rng.randrange(1,18)),F(rng.randrange(7),rng.randrange(1,18))) for _ in range(rng.randrange(1,18))];pool=[F(rng.randrange(19),rng.randrange(1,18)) for _ in range(rng.randrange(1,9))];self.values=[rng.choice(pool) for _ in range(rng.randrange(1,70))];self.fields=dict(node_ids=list(range(len(self.nodes))),edge_ids=list(range(len(self.values))))
 def node(self,n):return self.nodes[n]
 def increment(self,i):return self.values[i]
 def path(self,source,sink,edges):
  r,c=self.node(source);return r*c/2+sum((self.values[i] for i in edges),F(0))
for _ in range(1000):
 rc=RC();a=Old(rc);b=New(rc);scale=1
 for r,c in rc.nodes:scale=lcm(scale,(r*c/2).denominator)
 for value in rc.values:scale=lcm(scale,value.denominator)
 assert a.scale==b.scale==scale and a.increments==b.increments==[int(v*scale) for v in rc.values]
 for n,(r,c) in enumerate(rc.nodes):assert a.initial(n)==b.initial(n)==int(r*c/2*scale)
 edges=[rng.randrange(len(rc.values)) for _ in range(6)];assert a.path(0,0,edges)==b.path(0,0,edges)==int(rc.path(0,0,edges)*scale)
root=Path(__file__).resolve().parents[1];out=root/'experiments/memo_integer_context_contract_2026-10-07';out.mkdir();(out/'verification.json').write_text(json.dumps(dict(fixtures=1000,old_sha256=sha(root/'tools/integer_rc_context.py'),new_sha256=sha(root/'tools/integer_rc_context_memo.py'),checker_sha256=sha(Path(__file__)),scope='Independent exactLCM/increment/nodeinitial/path lattice, zero/repeated/distinct rational costs. Synthetic arithmetic contract, not physicalgraph/nativequery or end-to-end performance.'),indent=2)+'\n');print('1000 exact memo integer lattice fixtures passed')
