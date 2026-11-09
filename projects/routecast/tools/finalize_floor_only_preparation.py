"""Bind preparation semantics and full actual-consumer parity, scoped costs."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];old=ROOT/'experiments/mux_critical_release_cost_replay_2026-10-07';new=ROOT/'experiments/mux_critical_release_floor_only_2026-10-07';consumer=ROOT/'experiments/mux_owner50_floor_only_consumer_2026-10-07'
def read(p):return json.loads(p.read_text())
bindings={}
for d,names in [(old,['protocol.json','receipt.json','verification.json','wall_time.json','byte_parity.json']),(new,['protocol.json','receipt.json','verification.json','wall_time.json','consumed_field_parity.json']),(consumer,['protocol.json','receipt.json','verification.json'])]:
 for n in names:f=d/n;bindings[str(f)]=sha(f)
 v=read(d/'verification.json');assert v['receipt_sha256']==sha(d/'receipt.json')
 if d!=consumer:
  r=read(d/'receipt.json');assert len(r['rows'])==12
  for w in (8,16,32):
   for i in range(4):f=d/f'w{w}_m{i}.json';bindings[str(f)]=sha(f)
 else:
  for row in read(d/'receipt.json')['rows']:
   if row['status']=='PRIOR_ALLOCATION_SKIP':continue
   for name in ('result.json','cache_stats.json'):f=d/f"w{row['width']}_m{row['index']}"/name;bindings[str(f)]=sha(f)
 cv=read(d/'protocol.json');assert all(sha(f)==h for f,h in cv['sources'].items())
a,b=read(old/'wall_time.json'),read(new/'wall_time.json');assert a['exit_code']==b['exit_code']==0
assert len(read(old/'byte_parity.json')['rows'])==len(read(new/'consumed_field_parity.json')['rows'])==12
v=read(consumer/'verification.json');assert len(v['rows'])==12 and v['floor_verification_sha256']==sha(new/'verification.json')
out=ROOT/'experiments/floor_only_preparation_closure_2026-10-07';out.mkdir();(out/'final_evidence.json').write_text(json.dumps(dict(finalizer_sha256=sha(Path(__file__)),bindings=bindings,old_preparation_seconds=a['seconds'],floor_only_preparation_seconds=b['seconds'],observed_preparation_seconds_saved=a['seconds']-b['seconds'],cases=12,scope='Fresh legacy preparation all12 byte-identical to archived source; floor-only all fields equal except explicitly unused budgets/model_budget/interpolation. Independent fullDAG/release/shortest-certificate proofs pass for both. Fresh full12 actual50ps consumer whole nested result parity except bound prep-file hash and cache_stats bytes identical. Timings are single serial whole-process observations, not repeated/paired stable speedup. Upstream allfanin floors, old STA/RR/endpoint conversion additional; no fresh native gate/publication/full accepted lifecycle time.'),indent=2)+'\n');print('Closed floor-only preparation and actual consumer parity',a['seconds'],b['seconds'],flush=True)
