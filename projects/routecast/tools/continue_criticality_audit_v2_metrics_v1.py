"""Admit corrected full event audit alongside existing physical audits, then metrics."""
import json,sys,time,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
O=R/'experiments/mmc_full_criticality_feedback_trial_v1_2026-10-10'
target=O/'model/verification_v2.json'
while not target.exists():
 if not Path('/proc/2318612/cmdline').exists():raise RuntimeError('original event audit process missing without verification')
 time.sleep(5)
a=R/'tools/verify_criticality_present_guard_events_v1.py';b=R/'tools/verify_criticality_present_guard_events_v2.py'
assert a.read_text().replace("{'OPTIMAL_WITHIN_CANDIDATES','UNKNOWN_STATE_LIMIT'}","{'OPTIMAL_WITHIN_SUPPLIED_CANDIDATES','UNKNOWN_STATE_LIMIT'}")==b.read_text()
bindings=closure([Path(__file__),b]);stages=[]
for name in ('initial_physical_verification.json','sketch_physical_verification.json','verification_v2.json'):
 p=O/'model'/name;v=json.loads(p.read_text())
 assert v['completed']==115572 and v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
 assert all(sha(q)==h for q,h in v['bindings'].items())
 bindings.update(v['bindings']);bindings[str(p)]=sha(p);stages.append(dict(audit=name))
assert v['complete_frozen_perpin_raw_plus_max_user_unique_node_objective_pass'] and v['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass']
assert all(sha(q)==h for q,h in bindings.items())
p=O/'independent_audits_verification.json';assert not p.exists()
p.write_text(json.dumps(dict(bindings=bindings,all_three_full_audits_pass=True,stages=stages,correction='Only exact producer search status token corrected; all original event checks retained',scope='Full physical and event audits; no native QoR, heldout or workflow gain proof'),indent=2)+'\n')
print('FULL AUDITS V2 ADMITTED',flush=True)
with (O/'metrics_after_audit_v2.log').open('w') as f:
 code=subprocess.call([sys.executable,str(R/'tools/evaluate_mmc_criticality_hotspots_v1.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT)
(O/'metrics_after_audit_v2_terminal.json').write_text(json.dumps(dict(exit_status=code),indent=2)+'\n')
raise SystemExit(code)
