from fractions import Fraction
from pathlib import Path
import random,json
from shared_frozen_present_snapshot_v1 import Snapshot
from scaled_frozen_present_prices_v1 import Prices
from pre_route_endpoints import sha
rng=random.Random(19)
for i in range(200):
 n=50;b=[rng.randrange(20) for _ in range(n)];a=[rng.randrange(1,10) for _ in range(n)];o=[rng.randrange(8) for _ in range(n)];c=[rng.randrange(1,5) for _ in range(n)];pf=Fraction(rng.randrange(40),17);s=Snapshot(b,a,o,c,pf)
 for j in range(10):
  owner={u for u in range(n) if o[u] and rng.random()<.4};v=s.for_owner(owner);r=Prices(b,a,o,c,owner,pf)
  assert all(v.get(u)==r.get(u) for u in range(n))
  assert v.base is s._prices.base and v.occ is s._prices.occ
  w=s.for_owner(());assert w.owned==frozenset() and v.owned==frozenset(owner)
R=Path(__file__).resolve().parents[1];O=R/'experiments/shared_frozen_present_snapshot_contract_v1_2026-10-10';O.mkdir();files=[Path(__file__),R/'tools/shared_frozen_present_snapshot_v1.py',R/'tools/scaled_frozen_present_prices_v1.py']
(O/'verification.json').write_text(json.dumps({'bindings':{str(f.resolve()):sha(f) for f in files},'random_snapshots':200,'owner_views':2000,'price_cases':100000,'same_resource_tuples_shared':True,'owner_views_isolated':True,'scope':'Owner view parity and shared immutable tuples only; no full replay or performance claim.'},indent=2)+'\n');print('SHARED SNAPSHOT CONTRACT PASS')
