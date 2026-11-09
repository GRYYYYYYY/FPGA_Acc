"""Complete candidate admission, initial-state control and unchanged transaction loops."""
import ast,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=Path(sys.argv[1]).resolve();baseline=Path(sys.argv[2]).resolve();model=D/'model'
bindings=closure([Path(__file__)])
def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
def auth(r):
 for field in ['bindings','files']:
  for p,h in r.get(field,{}).items():assert sha(p)==h;bindings[p]=h
protocol=load(D/'protocol.json');auth(protocol);assert protocol['native_labels_read_by_candidate'] is False and sha(protocol['endpoint'])==protocol['endpoint_sha256']
required=len(load(Path(protocol['endpoint']))['connections'])
for path in [model/'receipt.json',baseline/'receipt.json']:auth(load(path))
for folder in [model,baseline]:
 for frame in ['initial','sketch']:
  r=load(folder/(frame+'_physical_verification.json'));auth(r);assert r['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'] and r['completed']==required
 r=load(folder/'verification.json');auth(r);assert r['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass'] and r['completed']==required
for file in ['floors.json','initial.json']:assert load(model/file)==load(baseline/file),file
for old,new in [('run_resident_soft_demand_context_handoff_v8.py','run_resident_triangular_span_v9.py'),('verify_resident_events_round_schedule_cache_v6.py','verify_resident_events_triangular_span_v7.py')]:
 def loops(name):return [ast.dump(x) for x in ast.walk(ast.parse((R/'tools'/name).read_text())) if isinstance(x,(ast.For,ast.While))]
 assert loops(old)==loops(new),(old,new)
 for name in [old,new]:bindings[str(R/'tools'/name)]=sha(R/'tools'/name)
candidate=load(model/'sketch.json');control=load(baseline/'sketch.json');event=load(model/'verification.json')
assert all(sha(p)==h for p,h in bindings.items())
result=dict(bindings=bindings,complete_candidate_physical_and_events_pass=True,initial_floors_and_state_equal=True,complete_model_and_audit_transaction_loops_AST_preserved=True,required=required,candidate_overflow=candidate['overflow_units'],baseline_overflow=control['overflow_units'],events=event['events'],committed=event['committed'],retained=event['retained'],scope='Post-hoc development candidate admission; complete paths/RC/NET ledgers/prices/epochs/events validated. Changed price objective, no final-state equivalence expected. Not weighted-optimality, predictor-quality, native route/QoR, full workflow gain or heldout proof.')
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2))
