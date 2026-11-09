"""Fresh unchanged model with per-phase/fanout public-search timers."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
import run_resident_actual_old_linear_undo_model_v13 as model
from hybrid_search_timing_v1 import Search, snapshot

R = Path(__file__).resolve().parents[1]
D = R / 'experiments/ultraembedded_mmc_actual_old_linear_expat_workflow_v15_2026-10-10'
O = R / 'experiments/mmc_full_hybrid_search_mix_profile_v1_2026-10-10'
proof = json.loads((D / 'verification.json').read_text())
assert proof['all_cases_both_complete_arms_authenticated']
bindings = closure([Path(__file__)])
for p,h in proof['bindings'].items():
    assert sha(p)==h
    bindings[p]=h
bindings[str(D/'verification.json')]=sha(D/'verification.json')
ep = D/'seed/demand/mmc/endpoints.json'
O.mkdir()
model.Search = Search
result = model.predict(ep, O/'mmc')
control = D/'seed/model/mmc'
for name in ['initial.json','floors.json','round0.json','round1.json','sketch.json']:
    assert sha(O/'mmc'/name)==sha(control/name), name
left = json.loads((control/'receipt.json').read_text())
right = json.loads((O/'mmc/receipt.json').read_text())
for a,b in zip(left['rounds'],right['rounds']):
    assert {k:v for k,v in a.items() if k not in ['seconds','state_file']} == {k:v for k,v in b.items() if k not in ['seconds','state_file']}
assert len(left['rounds'])==len(right['rounds'])==2
mix = snapshot()
assert {x['phase'] for x in mix}=={0,1,2}
assert sum(x['calls'] for x in mix)==55300+55300+41588
assert all(sha(p)==h for p,h in bindings.items())
out = dict(bindings=bindings, complete_states_and_events_equal_audited_control=True,
           result=result, search_mix=mix,
           scope='Fresh complete unchanged development prediction with timer instrumentation. All five state files and full two-round event content equal audited control. No new independent physical audit, stable performance, heldout or complete native workflow claim. Timers nested, wrapper overhead present.')
(O/'verification.json').write_text(json.dumps(out, indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='bindings'}, indent=2),flush=True)
