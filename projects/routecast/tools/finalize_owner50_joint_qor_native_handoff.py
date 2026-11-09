"""Close fresh cold/content admission proofs without fabricating lifecycle cost."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/owner50_joint_qor_native_handoff_2026-10-07';cold=ROOT/'experiments/mux_joint_qor_cost_cold_reference_2026-10-07'
def read(p):return json.loads(p.read_text())
r=read(out/'receipt.json');v=read(out/'verification.json');c=read(cold/'receipt.json');cv=read(cold/'verification.json');rep=read(cold/'old_content_reproducibility.json')
assert v['receipt_sha256']==sha(out/'receipt.json') and cv['receipt_sha256']==sha(cold/'receipt.json');assert len(r['rows'])==len(v['rows'])==len(c['rows'])==12
assert all(x['identical_selected_snapshot'] for x in rep['rows']);assert all(x['complete'] and x['error'] is None for x in c['rows'])
assert sum(x['connections'] for x in r['rows'])==13324
bindings={}
for directory,names in [(out,['protocol.json','receipt.json','verification.json']),(cold,['protocol.json','receipt.json','verification.json','old_content_reproducibility.json'])]:
 for name in names:f=directory/name;bindings[str(f)]=sha(f)
for f,h in r['bindings'].items():assert sha(f)==h;bindings[f]=h
for x in r['rows']:
 f=out/f"w{x['width']}_m{x['index']}/accepted_state.json";assert sha(f)==x['snapshot_sha256'];bindings[str(f)]=sha(f)
accepted=[(x['width'],x['index']) for x in r['rows'] if x['decision']['selected']=='candidate'];assert accepted==[(8,2),(8,3)]
summary=dict(finalizer_sha256=sha(Path(__file__)),bindings=bindings,cases=12,accepted_snapshot_connections=13324,candidate_admissions=accepted,reference_fallbacks=10,cold_case_wall_seconds=sum(x['case_wall_s'] for x in c['rows']),cold_case_wall_scope='Single serial fresh full12 cold routing+originalcanonical FULLSTA+physical audit+ledger setup/import; excludes frontend/originalroute/RRconversion/oldtimingreports and separate verifier process. Not stable paired timing.',fresh_cold_snapshots_identical_to_archived=True,live_candidate_lifecycle_status='NOT_MEASURED',candidate_content_scope='Archived freshly proven 50ps development native candidates; all12 explicit joint admission, selected-state import and independent XML/Fraction/NET-tree/capacity ledger proof. This replay is not fresh prediction/native candidate work or complete live accepted lifecycle, and does not establish sequential moves or durable/concurrent publication.',next_required='Native quality gate currently chooses CPD only; move joint CPD/wire selection into measured live path and expose its same-target cold wire metric. Then prospectively measure full12 including original floor preparation, prediction/model/physical checks, native cold reference, validation/import and fallback, with matched baseline and repeated scheduling.')
(out/'final_evidence.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:summary[k] for k in ['cases','accepted_snapshot_connections','candidate_admissions','reference_fallbacks','cold_case_wall_seconds','live_candidate_lifecycle_status']}))
