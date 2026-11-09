"""Recover original negative probe from immutable guard stderr, no native rerun."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/mmc_partial_seed_original_rejection_v1_2026-10-18';pp=D/'protocol.json';p=json.loads(pp.read_text());log=D/'native.log';text=log.read_text();assert 'what():  incomplete seed delay map' in text and not (D/'output.route').exists() and 'VPR succeeded' not in text;bindings={**p['bindings'],**closure([Path(__file__)]),str(pp):sha(pp),str(log):sha(log)};assert all(sha(p)==h for p,h in bindings.items())
with (D/'harness_v1_failure.json').open('x') as f:json.dump(dict(status='overstrict_buffered_stdout_expectation',reason='Native guard stderr is present; abort can leave preceding NET-aware imported stdout unflushed. V1 harness required that buffered text and did not persist native exit code before assertion.',native_rerun=False),f,indent=2)
with (D/'guard_observation_verification_v2.json').open('x') as f:json.dump(dict(status='original_partial_guard_observed_no_completion',bindings=bindings,explicit_original_delay_map_guard_observed=True,no_native_route_output=True,native_exit_code=None,native_exit_code_scope='Not persisted by original harness; do not infer exact signal/status.',native_rerun=False,scope='Observed old wrapper guard failure from immutable stderr, not physical unrouteability or a partial-NET completion proof. Missing buffered stdout is not treated as absence of import.'),f,indent=2)
print('RECOVERED original guard observation; no native rerun; exit code left unknown',flush=True)
