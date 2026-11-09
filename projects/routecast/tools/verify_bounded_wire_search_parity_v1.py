"""Authenticate all-query equivalence and inherit native evidence by full path identity."""
import json,math
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/global_guard_wire_contraction_bounded_v1_2026-10-08';B=R/'experiments/global_guard_wire_contraction_v1_2026-10-08'
vp=D/'verification.json';v=json.loads(vp.read_text());assert v['all1929_events_and_complete_original_xml_fraction_frame_pass'] and v['all_dynamic_model_guards_pass'] and all(sha(f)==h for f,h in v['bindings'].items())
nativepath=B/'native_quality_verification.json';native=json.loads(nativepath.read_text());assert native['full_chain_pass'] and native['joint_quality_pass'] and all(sha(f)==h for f,h in native['bindings'].items())
old=json.loads((B/'receipt.json').read_text());new=json.loads((D/'receipt.json').read_text());assert old['state']==new['state'] and len(old['events'])==len(new['events'])==1929 and old['initial_wire']==new['initial_wire'] and old['final_wire']==new['final_wire']==11474
for a,b in zip(old['events'],new['events']):
 for key in ('connection_id','query','old_delay_seconds'):assert a[key]==b[key]
 if a['status']=='RETAIN_ORIGINAL_CERTIFIED_BUDGET_INFEASIBLE':assert b['status']==a['status'];continue
 for key in ('global_upper_seconds','model_cpd_before_ns','max_occurrences','min_edge_slack_seconds','budget_integer_ceiling'):assert a[key]==b[key]
 assert math.isfinite(b['search_seconds']) and b['search_seconds']>=0
 if a['status']=='COMMIT':
  assert b['status']=='COMMIT'
  for key in ('new_path','new_delay_seconds','model_cpd_after_ns','old_net_wire','new_net_wire'):assert a[key]==b[key]
  for key in ('physical_edge_ids','cost','delay'):assert a['search'][key]==b['search'][key]
 else:assert a['status']=='RETAIN_FOUND' and b['status']=='RETAIN_NO_STRICT_IMPROVEMENT'
profilepath=R/'experiments/complete_wire_search_cost_replay_v2_2026-10-08/verification.json';profile=json.loads(profilepath.read_text());assert all(sha(f)==h for f,h in profile['bindings'].items());baseline=next(x for x in profile['passes'] if x['name']==B.name)
keys=('labels_created','labels_expanded','examined_edges');work={k:sum(e.get('search',{}).get(k,0) for e in new['events']) for k in keys};originalwork={k:sum(e.get('search',{}).get(k,0) for e in old['events']) for k in keys}
assert all(originalwork[k]==baseline[k] for k in keys)
bindings={**v['bindings'],**native['bindings'],**profile['bindings']}
for path in (vp,nativepath,profilepath,D/'receipt.json',B/'receipt.json',Path(__file__)):bindings[str(path)]=sha(path)
assert all(sha(f)==h for f,h in bindings.items())
out=dict(bindings=bindings,all1929_event_transition_and_final_physical_state_identities_pass=True,accepted_replacements=113,budget_violation_ids=v['budget_violation_ids'],bounded_work=work,unbounded_work=originalwork,search_function_calls=1927,zero_label_returns=sum(e.get('search',{}).get('labels_created')==0 for e in new['events']),observed_bounded_search_seconds=sum(e.get('search_seconds',0) for e in new['events']),historical_unbounded_search_seconds=baseline['search_seconds'],native_evidence_inherited_by_exact_complete_state_equality=True,native_cpd_ns=native['cpd_ns'],native_wirelength=native['wirelength'],first_native_fixups=native['initial_fixups'],canonical_fixups=native['canonical_fixups'],scope='All1929 transitions/accepted paths and final state exactly equal to authenticated native/canonical candidate. No new native run or original HDL equivalence claimed. Deterministic work counts decrease; search timers are sequential single observations, not paired or complete workflow speedup. Producer total elapsed was not saved and is not reconstructed. Original two budget failures remain; bounded exhaustion is not general RR unreachability or independently certified optimality.')
(D/'parity_verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'},flush=True)
