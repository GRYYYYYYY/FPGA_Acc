"""Full declared cost stage closure plus all4 matched quality evidence authentication."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_dual_constraint_complete_cost_v3_2026-10-08';Q=E/'adder_wire_guard_matched_quality_v3_2026-10-08/verification.json'
p=json.loads((D/'protocol.json').read_text());r=json.loads((D/'receipt.json').read_text());q=json.loads(Q.read_text());assert r['protocol_sha256']==sha(D/'protocol.json');bindings={}
for doc in (r,q):
 assert all(sha(f)==h for f,h in doc['bindings'].items());bindings.update(doc['bindings'])
for arm in ('seed','cold'):
 stages=r['arms'][arm]['stages'];assert [x['script'] for x in stages]==p['arms'][arm] and all(x['exit_code']==0 for x in stages)
 assert sum(x['seconds'] for x in stages)<=r['arms'][arm]['seconds']
 for x in stages:
  log=D/f'{arm}_{x["script"]}.log';bindings[str(log)]=sha(log)
for f in (D/'protocol.json',D/'receipt.json',Q,Path(__file__)):bindings[str(f)]=sha(f)
seed=r['arms']['seed']['seconds'];cold=r['arms']['cold']['seconds']
report=dict(bindings=bindings,seed_seconds=seed,cold_seconds=cold,observed_ratio=seed/cold,time_gain=seed<cold,quality_rows=q['rows'],scope='Fresh complete declared-input two arms with shared serialization, all independent checks and native/canonical stages timed. One sequential observation; no original input generation/baseline oldnative production or repeated paired gain. Budget failures and per-CID regressions retained.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(seed,cold,seed/cold)
