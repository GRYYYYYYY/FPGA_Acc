"""Fresh cold generation included in subsequent repair workflow clock."""
import json,subprocess,time,sys
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
D=R/'experiments/adder_live_owner_coldfirst_cost_v1_2026-10-08';D.mkdir(exist_ok=False)
stages=['trial_adder_wire_guard_matched_cold_v5.py', 'trial_adder_wire_guard_matched_cold_canonical_v5.py', 'trial_adder_matched_baseline_branch_repair_v3.py', 'verify_adder_matched_baseline_branch_repair_v3.py', 'trial_adder_matched_baseline_multinet_repair_v3.py', 'verify_adder_matched_baseline_multinet_repair_v3.py', 'verify_adder_matched_baseline_wire_bounds_3.py', 'trial_adder_matched_baseline_reverse_group_repair_v2.py', 'verify_adder_matched_baseline_reverse_group_repair_v2.py', 'verify_adder_reverse_group_wire_bounds_2.py', 'trial_adder_twohop_group_repair_v2.py', 'verify_adder_twohop_group_repair_v2.py', 'verify_adder_twohop_wire_bounds_2.py', 'trial_adder_failed_constraint_probe_v2.py', 'verify_adder_failed_constraint_state_2.py', 'verify_adder_failed_constraint_wire_2.py', 'verify_adder_failed_constraint_probes_2.py', 'trial_adder_tight_budget_order_repair_v2.py', 'verify_adder_tight_budget_order_state_2.py', 'verify_adder_tight_budget_order_wire_2.py', 'trial_adder_failure_priority_retry_v2.py', 'verify_adder_failure_priority_state_2.py', 'verify_adder_failure_priority_wire_2.py', 'trial_adder_live_owner_expansion_v2.py', 'verify_adder_live_owner_state_2.py', 'verify_adder_live_owner_wire_2.py', 'serialize_adder_live_owner_2.py', 'trial_adder_live_owner_native_reload_v2.py', 'trial_adder_live_owner_canonical_reload_v2.py']
bindings=closure([Path(__file__),*[R/'tools'/n for n in stages]])
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,stages=stages,scope='Fresh four-step cold routes + full budget/canonical checks form timed initial prefix. Repair pipeline then consumes those routes; cold production not free. All subsequent search/independent proofs/serialization/native/canonical timed. Provided graphs/netlists/placements/budgets excluded; protocol/finalreceipt/topverification excluded.'),indent=2)+'\n');start=time.perf_counter();rows=[];cold=None
for i,name in enumerate(stages):
 tick=time.perf_counter()
 with (D/(name+'.log')).open('x') as log:code=subprocess.run([sys.executable,str(R/'tools'/name)],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 rows.append(dict(script=name,seconds=time.perf_counter()-tick,exit_code=code));print(rows[-1],flush=True);assert code==0
 if i==1:cold=time.perf_counter()-start
 (D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n')
elapsed=time.perf_counter()-start;assert all(sha(f)==h for f,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,stages=rows,direct_cold_prefix_seconds=cold,coldfirst_repaired_workflow_seconds=elapsed,observed_ratio=elapsed/cold,protocol_sha256=sha(D/'protocol.json'),scope='One actual nested-prefix workflow measurement, not independent paired arms. Includes all cold production and repair checks; no complete original-input or runtime gain claim.'),indent=2)+'\n');print(cold,elapsed,elapsed/cold)
