"""Bind candidate-owned original FULL/STA and exact physical route preservation."""
import json,re
from pathlib import Path
from fractions import Fraction as F
from pre_route_endpoints import sha
from native_route_ledger_import import physical_paths
from stream_native_route_audit import audit
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_owner_union_w8m2_candidate_canonical_2026-10-07';gate=ROOT/'experiments/mux_owner_union_w8m2_quality_gate_2026-10-07';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json') and p['parent_receipt_sha256']==sha(gate/'receipt.json');gr=json.loads((gate/'receipt.json').read_text());gv=json.loads((gate/'verification.json').read_text());assert gv['receipt_sha256']==sha(gate/'receipt.json');assert len(r['rows'])==1;row=r['rows'][0];reload=row['reload'];assert (row['width'],row['index'])==(8,2);assert all(sha(f)==h for f,h in reload['files'].items());assert sha(reload['command'][0])=='a90dc1b3380ebda705e85f176db0cc3d6be1b71ab9ee887db819febc8b62bafc';assert reload['exit_code']==0 and reload['mismatches']==reload['fixups']==0
native_pred=F(str(gv['rows'][0]['predicted_cpd_ns']));cpd=F(str(reload['cpd_ns']));assert abs(cpd-native_pred)<=F('0.00001');target=F(json.loads((ROOT/'experiments/mux_allfanin_budgets_2026-10-06/w8_m2.json').read_text())['target_cpd_ns']);assert cpd<=target
canonical=Path(next(f for f in reload['files'] if f.endswith('/design.route')));pred=gate/'w8_m2/predicted.route'
def named_paths(file):
 return {name:sorted(v) for name,v in physical_paths(file).items() if v}
assert named_paths(pred)==named_paths(canonical);graph=Path(reload['command'][reload['command'].index('--read_rr_graph')+1]);a=audit(graph,canonical);assert a['overflow_units']==0 and len(a['connections'])==466;log=Path(next(f for f in reload['files'] if f.endswith('/reload.log'))).read_text()
for marker in ['VPR succeeded','RouterOpts.check_route: FULL','Completed routing consistency check successfully.']:assert marker in log
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),gate_verification_sha256=sha(gate/'verification.json'),verifier_sha256=sha(Path(__file__)),candidate_route_sha256=sha(pred),canonical_route_sha256=sha(canonical),candidate_cpd_ns=str(cpd),model_target_ns=str(target),cold_reference_selected=gv['rows'][0]['selected']=='reference',first_replay_zero_fixup=row['first_replay_zero_fixup'],connections=466,scope='Candidate OWN packing synchronized then original VPR FULL/STA zero mismatches/fixups; exact NET-name physical paths preserved, original XML capacity audited. Candidate meets old printed target, gate selection archived independently. No matched lifecycle speedup/fullcohort or board claim.'),indent=2)+'\n');print('verified candidate canonical',float(cpd),'coldreference selected',gv['rows'][0]['selected'])
