"""Fresh full MMC development prediction, then complete independent audits."""
import json
import subprocess
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure

R = Path(__file__).resolve().parents[1]
P = R / 'experiments/soft_demand_workspace_limited_contract_v6_2026-10-10/verification.json'
protocol = json.loads(P.read_text())
assert protocol['bounded_queries']==9600 and protocol['settled_node_caps_and_requested_path_prefix_equal']
assert all(sha(k) == h for k,h in protocol['bindings'].items())
ep = R / 'experiments/ultraembedded_mmc_actual_old_linear_expat_workflow_v15_2026-10-10/seed/demand/mmc/endpoints.json'
O = R / 'experiments/mmc_limited_model_v1_2026-10-10'
model = O / 'mmc'
bindings = closure([Path(__file__), R / 'tools/run_resident_limited_model_v16.py', R / 'tools/run_shared_limited_audits_v6.py'])
bindings.update({str(P): sha(P), str(ep): sha(ep)})
O.mkdir()
(O / 'protocol.json').write_text(json.dumps(dict(bindings=bindings, candidate=protocol,
    scope='Fresh prediction from frozen development endpoints; no archived model or native labels used for decisions. Model plus all full audits timed locally; export/native/full workflow excluded.'), indent=2)+'\n')
start = time.perf_counter(); rows = []
for script, args, name in [
    ('run_resident_limited_model_v16.py', [str(ep), str(model)], 'model'),
    ('run_shared_limited_audits_v6.py', [str(model), 'mmc'], 'audits')]:
    tick = time.perf_counter()
    with (O / (name+'.log')).open('w') as log:
        result = subprocess.run([sys.executable, str(R/'tools'/script), *args], cwd=R,
                                stdout=log, stderr=subprocess.STDOUT, timeout=1200)
    rows.append(dict(stage=name, seconds=time.perf_counter()-tick, exit_code=result.returncode))
    (O / 'rows.json').write_text(json.dumps(rows, indent=2)+'\n')
    assert result.returncode == 0, rows[-1]
proof = json.loads((model/'shared_audit_receipt.json').read_text())
assert proof['all_three_complete_audits_pass'] and proof['complete_audit_bodies_AST_preserved']
events = json.loads((model/'verification.json').read_text())
assert events['completed'] == 115572
assert events['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass']
for p,h in proof['bindings'].items():
    assert sha(p)==h
    bindings[p]=h
assert all(sha(p)==h for p,h in bindings.items())
out = dict(bindings=bindings, complete_candidate_physical_and_events_pass=True,
           rows=rows, continuous_local_model_and_audit_seconds=time.perf_counter()-start,
           overflow_units=events['overflow_units'], events=events['events'],
           scope='Full development model and independent frame/event audit only. No control equivalence, prediction-quality, native routing, full workflow time gain, heldout or hardware claim.')
(O/'verification.json').write_text(json.dumps(out, indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='bindings'}, indent=2), flush=True)
