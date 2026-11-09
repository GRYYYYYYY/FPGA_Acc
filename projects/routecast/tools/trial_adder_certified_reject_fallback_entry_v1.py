"""Real certificate-negative entry, fresh cold fallback, explicit budget failures."""
import json,time,subprocess,sys
from pathlib import Path
from pre_route_endpoints import sha
from required_node_budget_preflight_v1 import batch_preflight
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_certified_reject_fallback_entry_v1_2026-10-09';D.mkdir(exist_ok=False)
proof=E/'adder_required_node_potentials_v1_2026-10-09/verification.json';digest=sha(proof)
requests=[dict(step=i,endpoints=str(E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json' if i==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{i}_endpoints.json'),budgets=str(E/f'adder_tree_online_move_rc_budgets_2026-10-06/step_{i}_budgets.json')) for i in range(4)]
stages=['trial_adder_budget_reject_fallback_cold_v1.py','trial_adder_budget_reject_fallback_canonical_v1.py'];bindings=closure([Path(__file__),*[R/'tools'/n for n in stages]])
bindings[str(proof)]=digest
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,requests=requests,fallback_commands=stages,scope='Preflight negative decision then fresh cold/full audit/canonical; no repair search and no old-budget admission claim.'),indent=2)+'\n')
start=time.perf_counter();decisions=batch_preflight(proof,digest,requests);preflight_seconds=time.perf_counter()-start
assert len(decisions)==4 and all(d['decision']=='REJECT_CERTIFIED_MODEL_BUDGET_CAPACITY_CONFLICT' for d in decisions)
(D/'decisions.json').write_text(json.dumps(decisions,indent=2)+'\n');runs=[]
for script in stages:
 # Authenticate again before executing dependent external work.
 batch_preflight(proof,digest,requests)
 assert all(sha(p)==h for p,h in bindings.items())
 tick=time.perf_counter()
 with (D/(script+'.log')).open('x') as log:code=subprocess.run([sys.executable,str(R/'tools'/script)],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 runs.append(dict(script=script,exit_code=code,seconds=time.perf_counter()-tick));print(runs[-1],flush=True);assert code==0
elapsed=time.perf_counter()-start;roots=[E/'adder_budget_reject_fallback_cold_v1_2026-10-08',E/'adder_budget_reject_fallback_canonical_v1_2026-10-08'];docs=[]
for root in roots:
 doc=json.loads((root/'receipt.json').read_text());assert all(sha(p)==h for p,h in doc['bindings'].items());bindings[str(root/'receipt.json')]=sha(root/'receipt.json');docs.append(doc)
rows=[]
for i in range(4):
 a=docs[0]['rows'][i];b=docs[1]['rows'][i]
 assert a['exit_code']==0 and a['full_check'] and a['vpr_succeeded']
 assert b['original_zero_counter_gate_pass'] and b['semantic_consistency_gate_pass'] and b['all516_named_paths_equal']
 rows.append(dict(step=i,result='COLD_FALLBACK_NATIVE_VALID_MODEL_BUDGET_REJECTED',model_budget_failures=len(a['violation_ids']),cpd_ns=a['cpd_ns'],wirelength=a['wirelength']))
assert all(sha(p)==h for p,h in bindings.items());batch_preflight(proof,digest,requests)
report=dict(bindings=bindings,decisions=decisions,rows=rows,runs=runs,repair_commands_launched=0,fallback_commands_launched=2,preflight_seconds=preflight_seconds,workflow_seconds=elapsed,scope='Actual preflight+reauthentication+freshcold/native audit+canonical incl startup/output/checks. Final receipt verification excluded. Model budget rejection persists; no user timing or routing speedup claim.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(rows=rows,workflow_seconds=elapsed),indent=2))
