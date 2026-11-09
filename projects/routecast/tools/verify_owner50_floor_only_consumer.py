"""Exact complete consumer-result parity, permitting only bound seed-file hash."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];old=ROOT/'experiments/mux_owner_wire_50ps_development_2026-10-07';new=ROOT/'experiments/mux_owner50_floor_only_consumer_2026-10-07';r=json.loads((new/'receipt.json').read_text());p=json.loads((new/'protocol.json').read_text());assert len(r['rows'])==12 and r['protocol_sha256']==sha(new/'protocol.json');assert all(sha(f)==h for f,h in p['sources'].items());baseline=json.loads((old/'receipt.json').read_text());rows=[]
for a,b in zip(baseline['rows'],r['rows']):
 assert {k:v for k,v in a.items() if k not in ('loop_seconds','result_sha256')}=={k:v for k,v in b.items() if k not in ('loop_seconds','result_sha256')};w,i=b['width'],b['index']
 if b['status']=='PRIOR_ALLOCATION_SKIP':rows.append(dict(width=w,index=i,status=b['status']));continue
 af=old/f'w{w}_m{i}/result.json';bf=new/f'w{w}_m{i}/result.json';x=json.loads(af.read_text());y=json.loads(bf.read_text());assert sha(bf)==b['result_sha256'];assert y.pop('initial_floor_seed_sha256')==sha(ROOT/f'experiments/mux_critical_release_floor_only_2026-10-07/w{w}_m{i}.json');assert x.pop('initial_floor_seed_sha256')==sha(ROOT/f'experiments/mux_critical_release_budgets_2026-10-06/w{w}_m{i}.json');assert x==y
 assert (af.parent/'cache_stats.json').read_bytes()==(bf.parent/'cache_stats.json').read_bytes()
 rows.append(dict(width=w,index=i,status=b['status'],old_result_sha256=sha(af),new_result_sha256=sha(bf),scope='Entire nested consumer result equal except authenticated preparation-file hash; cache stats bytes identical.'))
(new/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(new/'receipt.json'),verifier_sha256=sha(Path(__file__)),floor_verification_sha256=sha(ROOT/'experiments/mux_critical_release_floor_only_2026-10-07/verification.json'),rows=rows,scope='Full12 actual consumer rerun semantic result parity with original50ps cohort; only prep file hash changes. New native gate/lifecycle execution absent, no end-to-end acceleration.'),indent=2)+'\n');print('Full12 floor-only consumer exact parity')
