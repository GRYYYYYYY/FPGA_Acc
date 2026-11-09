"""Complete candidate and all trial-budget/decision parity, separate run clocks."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];names=['mux32_limit_retry_tree_2026-10-07','mux32_integer_budget_tree_2026-10-07'];bindings={};receipts=[]
for name in names:
 base=ROOT/'experiments'/name;rp=base/'receipt.json';cp=base/'candidate.json';vp=base/'verification.json';pp=base/'protocol.json'
 r=json.loads(rp.read_text());v=json.loads(vp.read_text());p=json.loads(pp.read_text())
 assert v['receipt_sha256']==sha(rp) and r['candidate_sha256']==sha(cp) and r['protocol_sha256']==sha(pp)
 assert all(sha(f)==h for f,h in {**p['sources'],**p['inputs']}.items())
 bindings.update({str(f):sha(f) for f in (rp,cp,vp,pp)});receipts.append(r)
assert receipts[0]['candidate_sha256']==receipts[1]['candidate_sha256']
assert receipts[0]['trace']==receipts[1]['trace']
for key in ('initial_cpd_ns','final_cpd_ns','target_cpd_ns','initial_wirelength','final_wirelength','accepted_repairs','attempts','parent_conflicts','overflow_units'):
 assert receipts[0][key]==receipts[1][key]
result=dict(source_sha256=sha(Path(__file__)),bindings=bindings,complete_candidate_byte_identical=True,all_trial_budgets_labels_decisions_identical=True,net_attempts=receipts[1]['attempts'],reference_seconds=receipts[0]['producer_seconds'],reuse_seconds=receipts[1]['producer_seconds'],scope='Separate single serial observations; OS caches not reset. All actual budget/event traces and complete candidate bytes match audited reference. Not stable speedup or complete feedback netgain; native/canonical evidence reused for identical candidate; no new native execution.')
base=ROOT/'experiments'/names[1];(base/'parity_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
