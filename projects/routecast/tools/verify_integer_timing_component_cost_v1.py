"""Phase attribution with complete event fidelity; not paired/end-to-end timing."""
import json,math
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];P=R/'experiments/global_guard_wire_contraction_profile_v1_2026-10-08';D=R/'experiments/global_guard_wire_contraction_integer_timing_v1_2026-10-08'
originalpath=R/'experiments/global_guard_wire_contraction_native_v1_2026-10-08/receipt.json';original=json.loads(originalpath.read_text());originalproof=originalpath.with_name('parity_verification_v2.json');op=json.loads(originalproof.read_text());assert op['all1929_event_transition_and_final_physical_state_identities_pass'] and all(sha(f)==h for f,h in op['bindings'].items())
proofpath=D/'parity_verification.json';proof=json.loads(proofpath.read_text());assert proof['all1929_event_transition_and_final_physical_state_identities_pass'] and all(sha(f)==h for f,h in proof['bindings'].items())
frame=json.loads((D/'verification.json').read_text());assert frame['all114_integer_timing_full_weights_arrivals_suffixes_equal_independent_fraction']
bindings={**op['bindings'],**proof['bindings'],str(originalproof):sha(originalproof),str(proofpath):sha(proofpath),str(Path(__file__)):sha(Path(__file__))};observations=[]
def semantic_events(x):return [{k:v for k,v in e.items() if k!='search_seconds'} for e in x['events']]
for label,directory in (('fraction_timing',P),('integer_timing',D)):
 path=directory/'receipt.json';r=json.loads(path.read_text());assert all(sha(f)==h for f,h in r['bindings'].items());bindings.update(r['bindings']);bindings[str(path)]=sha(path)
 assert len(r['events'])==1929 and semantic_events(r)==semantic_events(original) and r['state']==original['state']
 assert r['phase_calls']=={'full_dag_timing':114,'single_query_bound':1927}
 phases=r['phases_seconds'];assert set(phases)=={'full_dag_timing','single_query_bound','state_preparation','progress_output'}
 assert all(math.isfinite(x) and x>=0 for x in phases.values())
 search=sum(e.get('search_seconds',0) for e in r['events']);assert search==r['search_seconds']
 explained=sum(phases.values())+r['setup_nonphase_seconds']+search;residual=r['elapsed_seconds']-explained;assert residual>=-1e-9
 observations.append(dict(implementation=label,phase_seconds=phases,search_seconds=search,setup_nonphase_seconds=r['setup_nonphase_seconds'],residual_seconds=residual,producer_component_elapsed_seconds=r['elapsed_seconds']))
assert all(sha(f)==h for f,h in bindings.items())
out=dict(bindings=bindings,all1929_semantic_events_and_final_state_equal=True,all114_complete_timing_vectors_equal_independent_fraction=True,observations=observations,paired_speedup_proved=False,end_to_end_gain_proved=False,scope='Two sequential single component observations; phase timers include initial model construction and all113 full updates, all1927 bounds, progress output and input setup. Search includes native input preparation; no double charging. Excludes upstream endpoint/budget/owner repair, previous wire passes, final VPR/canonical and independent audits; complete workflow gain unproved. Original two budget failures remain.')
(D/'component_cost_verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='bindings'},indent=2),flush=True)
