"""Compare available immutable prospective outputs, preserving pending status."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
old=ROOT/'experiments/mux_net_slack_online_loop_2026-10-06'
new=ROOT/'experiments/mux_net_slack_incremental_online_loop_2026-10-06'
p=json.loads((new/'protocol.json').read_text())
assert all(sha(f)==h for f,h in p['sources'].items())
assert p['cases']==json.loads((old/'protocol.json').read_text())['cases']
assert json.loads((old/'audit_summary.json').read_text())['receipt_sha256']==sha(old/'receipt.json')
rows=[]
for c in p['cases']:
 w,i=c['width'],c['index'];af=old/f'w{w}_m{i}/result.json';bf=new/f'w{w}_m{i}/result.json'
 seed=ROOT/f'experiments/mux_critical_release_budgets_2026-10-06/w{w}_m{i}.json'
 if json.loads(seed.read_text())['status']!='CRITICAL_RELEASE_VECTOR_CONSTRUCTED':
  rows.append(dict(width=w,index=i,status='INITIAL_SKIP_BY_FROZEN_SEED'));continue
 if not bf.exists():rows.append(dict(width=w,index=i,status='PENDING'));continue
 assert sha(af)==sha(bf) and af.read_bytes()==bf.read_bytes()
 d=json.loads(bf.read_text())
 rows.append(dict(width=w,index=i,status=d['result']['status'],result_sha256=sha(bf),allocations=len(d['allocations']),attempts=len(d['attempts'])))
(new/'exact_result_equivalence.json').write_text(json.dumps(dict(protocol_sha256=sha(new/'protocol.json'),baseline_receipt_sha256=sha(old/'receipt.json'),baseline_audit_sha256=sha(old/'audit_summary.json'),source_sha256=sha(Path(__file__)),rows=rows,pending=sum(r['status']=='PENDING' for r in rows),scope='Available prospective files are byte-identical, including actual repairs/history/queues/floors/budgets. Frozen initial skips identified, pending explicitly retained. Native content proofs/timers not reused by this comparison. No lifecycle speedup or complete-cohort assertion while pending.'),indent=2)+'\n')
print(json.dumps(rows))
