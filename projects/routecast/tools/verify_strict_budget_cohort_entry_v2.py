"""Authenticate all12 actual skip receipts and complete original budget blockers."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/strict_budget_cohort_entry_v2_2026-10-08';B=R/'experiments/branch_budget_admission_census_v1_2026-10-08'
r=json.loads((D/'receipt.json').read_text());assert len(r['rows'])==12 and r['candidate_launches']==0
assert all(sha(f)==h for f,h in r['bindings'].items());bindings=dict(r['bindings']);total=0
for x in r['rows']:
 name=f'w{x["width"]}_m{x["index"]}';p=D/name/'protocol.json';receipt=D/name/'receipt.json'
 a=json.loads(p.read_text());b=json.loads(receipt.read_text());ad=json.loads((B/(name+'_admission.json')).read_text())
 assert b['protocol_sha256']==sha(p) and a['preflight']['decision']==x['decision']=='SKIP_CERTIFIED_MODEL_INFEASIBLE'
 assert all(sha(f)==h for f,h in a['preflight']['bindings'].items())
 blockers={y['connection_id'] for y in a['preflight']['blockers']}
 assert blockers=={y['connection_id'] for y in ad['rows'] if not y['relaxed_path_budget_feasible']}
 assert x['candidate_launched']==b['candidate_launched']==False and x['candidate_exit_code'] is None
 assert b['candidate_quality_accepted'] is False and b['full_original_input_workflow_seconds'] is None
 assert not (D/name/'candidate.log').exists() and not (D/(name+'_candidate')).exists()
 bindings.update(a['preflight']['bindings']);bindings[str(p)]=sha(p);bindings[str(receipt)]=sha(receipt);total+=len(blockers)
for p in (D/'receipt.json',Path(__file__)):bindings[str(p)]=sha(p)
report=dict(bindings=bindings,all12_actual_entries_skipped=True,candidate_logs_and_workdirs=0,complete_blocker_count=total,observed_entry_component_seconds=r['entry_component_seconds'],real_feasible_continue_verified=False,scope='All12 authenticated entry records preserve complete certified original-budget blockers and create no candidate logs/workdirs. Prior floor production cost excluded. Not quality acceptance, physical-route speedup, positive feasible workflow or unseen-family result.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='bindings'})
