"""Check frozen nested-prefix timing receipt and independently verified quality."""
import hashlib,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=R/'experiments/adder_coldfirst_complete_cost_v1_2026-10-08'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=json.loads((D/'receipt.json').read_text());p=json.loads((D/'protocol.json').read_text())
assert sha(D/'protocol.json')==r['protocol_sha256']
assert r['bindings']==p['bindings']
assert all(sha(f)==h for f,h in r['bindings'].items())
assert [s['script'] for s in r['stages']]==p['stages'] and len(r['stages'])==10
assert all(s['exit_code']==0 and s['seconds']>0 and (D/(s['script']+'.log')).is_file() for s in r['stages'])
c=r['direct_cold_prefix_seconds'];w=r['coldfirst_repaired_workflow_seconds']
assert sum(s['seconds'] for s in r['stages'][:2])<=c<w
assert sum(s['seconds'] for s in r['stages'])<=w
assert math.isclose(r['observed_ratio'],w/c,rel_tol=1e-12)
Q=R/'experiments/adder_matched_baseline_quality_v2_2026-10-08/verification.json'
q=json.loads(Q.read_text())
assert q['all4_canonical_zero_full_sta_pass'] and len(q['rows'])==4
assert all(x['joint_printed_nonregression'] and not x['new_failed_connection_ids'] for x in q['rows'])
assert q['total_seed_budget_failures']==96 and q['total_cold_budget_failures']==119
out=dict(receipt_sha256=sha(D/'receipt.json'),quality_sha256=sha(Q),verifier_sha256=sha(__file__),source_hashes_pass=True,stage_order_and_clock_arithmetic_pass=True,direct_cold_prefix_seconds=c,coldfirst_repaired_workflow_seconds=w,observed_ratio=w/c,additional_workflow_seconds=w-c,total_repaired_connections=23,remaining_budget_failures=96,scope='Actual nested-prefix measurement; provided input generation and top verification excluded. No independent paired timing, all-budget admission, userclock, HDL, unseen-family or hardware proof.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
