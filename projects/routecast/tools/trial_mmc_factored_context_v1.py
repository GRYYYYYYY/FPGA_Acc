"""Correctness-first MMC replay using the existing factored price context."""
import json,time,importlib.util
from pathlib import Path
from pre_route_endpoints import sha
from factored_multiplicative_context_v1 import Context
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_factored_context_trial_v1_2026-10-21';D.mkdir()
P=R/'experiments/mmc_native_cached_feedback_pilot_v1_2026-10-18/protocol.json';p=json.loads(P.read_text());assert all(sha(k)==v for k,v in p['bindings'].items())
source=Path(p['command'][1]);extra=[Path(__file__),P,R/'tools/factored_multiplicative_context_v1.py',R/'tools/cached_multiplicative_occupancy_context_v1.py',R/'tools/multiplicative_occupancy_context_v1.py',R/'tools/present_occupancy_context_v1.py']
bindings={**p['bindings'],**{str(f):sha(f) for f in extra}}
(D/'protocol.json').write_text(json.dumps({'bindings':bindings,'intervention':'Only predict global Context replaced by existing factored Context; same original function body, policies, frozen inputs, rounds, checks and complete outputs.','scope':'One exposed MMC correctness replay; clocks descriptive only, no randomized performance comparison, native or end-to-end gain. No graph caching or gate removal.','native_calls':0},indent=2)+'\n')
spec=importlib.util.spec_from_file_location('mmc_factored_trial_original',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.Context=Context
args=p['command'][2:];old=Path(args[1]);args[1]=str(D/'model');tick=time.perf_counter();module.predict(*args);elapsed=time.perf_counter()-tick
parity={}
for name in ['initial.json','floors.json','round0.json','round1.json','sketch.json','structural_cost_metrics.json']:
 parity[name]=sha(old/name)==sha(D/'model'/name);assert parity[name],name
before=json.loads((old/'receipt.json').read_text());after=json.loads((D/'model/receipt.json').read_text())
def semantic(rounds):return [{k:v for k,v in r.items() if k not in ['seconds','state_file']} for r in rounds]
assert semantic(before['rounds'])==semantic(after['rounds'])
assert all(sha(k)==v for k,v in bindings.items())
(D/'verification.json').write_text(json.dumps({'full_state_bytes_exact':parity,'all_round_events_and_counts_exact':True,'predict_wall_seconds':elapsed,'model_reported_times':{k:v for k,v in after.items() if k.endswith('seconds')},'bindings':{**bindings,str(D/'model/receipt.json'):sha(D/'model/receipt.json')},'scope':'Exact MMC correctness replay, no matched fresh baseline timing or end-to-end gain.'},indent=2)+'\n');print('FACTORED MMC EXACT PARITY PASS',elapsed,flush=True)
