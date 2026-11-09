"""Three independent full-model audits in a shared immutable XML context."""
import json,sys,runpy,time
from pathlib import Path
from pre_route_endpoints import sha
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/native_resume_prototype'))
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
O=Path(sys.argv[1]).resolve();terminal=json.loads((O/'model_terminal.json').read_text());assert terminal['exit_status']==0
P=R/'experiments/multiplicative_model_source_lineage_v1_2026-10-10/verification.json';proof=json.loads(P.read_text());assert proof['driver_reverse_edits_exact_original'] and proof['auditor_reverse_edits_exact_original'] and all(sha(p)==h for p,h in proof['bindings'].items())
model=O/'model';bindings={**proof['bindings'],str(P):sha(P),**closure([Path(__file__)])};stages=[];begin=time.perf_counter()
for script,args,name in [('verify_resident_demand_frame_direct_lattice_v7.py',[str(model),'initial'],'initial_physical_verification.json'),('verify_resident_demand_frame_direct_lattice_v7.py',[str(model),'sketch'],'sketch_physical_verification.json'),('verify_criticality_multiplicative_guard_events_v1.py',[str(model),'mmc'],'verification.json')]:
 target=model/name;assert not target.exists();sys.argv=[str(R/'tools'/script),*args,str(target)];tick=time.perf_counter();runpy.run_path(str(R/'tools'/script),run_name='__main__');stages.append(dict(audit=name,seconds=time.perf_counter()-tick))
 p=json.loads(target.read_text());assert p['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'] and all(sha(q)==h for q,h in p['bindings'].items());bindings.update(p['bindings']);bindings[str(target)]=sha(target)
assert p['complete_frozen_perpin_raw_plus_max_user_unique_node_objective_pass'] and p['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass']
assert all(sha(q)==h for q,h in bindings.items())
(O/'independent_audits_verification.json').write_text(json.dumps(dict(bindings=bindings,all_three_full_audits_pass=True,stages=stages,seconds=time.perf_counter()-begin,scope='Full model physical and event/objective audits. Does not prove hotspot quality/native QoR or complete workflow speed.'),indent=2)+'\n');print('FULL CRITICALITY AUDITS PASS',flush=True)
