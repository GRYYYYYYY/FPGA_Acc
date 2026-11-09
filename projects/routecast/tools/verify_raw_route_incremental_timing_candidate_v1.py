"""Authenticate every stage of the single-clock raw-route candidate pipeline."""
import json
from pathlib import Path
from pre_route_endpoints import sha

R = Path(__file__).resolve().parents[1]
E = R / 'experiments'
D = E / 'raw_route_incremental_timing_candidate_v1_2026-10-08'
bindings = {}

def read(path):
    obj = json.loads(path.read_text())
    for name,digest in obj.get('bindings',{}).items():
        assert sha(name)==digest, name
        assert name not in bindings or bindings[name]==digest
        bindings[name]=digest
    bindings[str(path)]=sha(path)
    return obj

def historical(name,filename='receipt.json'):
    return read(E/(name+'_2026-10-08')/filename)

def clean(event,exclude=()):
    return {k:v for k,v in event.items() if k not in ('search_seconds',*exclude)}

r=read(D/'receipt.json')
assert r['potential_native_calls']==102 and r['potential_fallback_calls']==0
reference=read(E/'profile_native_owner_potential_only_v1_2026-10-08/verification.json')
assert reference['all4_candidates_and102_stage_paths_certificate_contents_equal']
checkproof=read(E/'native_clipped_potential_check_v1_2026-10-08/verification.json')
assert len(checkproof['rows'])==5 and len(checkproof['rejected'])==4
p=read(D/'protocol.json')
assert r['protocol_sha256']==sha(D/'protocol.json')
b=historical('fresh_native_budget_repairs_v1')
proof=historical('fresh_native_budget_repairs_v1','verification.json')
assert proof['budget_safe_connections']==1927
assert proof['all1929_raw_and_final_original_xml_fraction_paths_pass']
assert proof['all8_discovered_budget_attempts_replay_pass']
stage=r['budget_stage']
for key in ('initial_rows','initial_budget_violation_ids','state','final_budget_violation_ids'):
    assert stage[key]==b[key],key
assert len(stage['events'])==len(b['events'])==8
for a,z in zip(stage['events'],b['events']):assert clean(a)==clean(z)
discovery=historical('fresh_critical_owner_discovery_v1')
dp=historical('fresh_critical_owner_discovery_v1','verification.json')
assert dp['all_blocking_node_owner_sets_reconstructed']
assert dp['independent_full_fraction_cpd_and_attaining_path_pass']
assert dp['all_selected_full_and_relaxed_minimum_paths_equal_prior_certified_witnesses']
stage=r['discovery_stage']
for key in ('selected_connections','critical_timing_edge_ids','model_cpd_ns'):
    assert stage[key]==discovery[key]
assert len(stage['events'])==len(discovery['events'])==6
for a,z in zip(stage['events'],discovery['events']):assert clean(a)==clean(z)
owners=historical('fresh_critical_owner_transactions_v1')
op=historical('fresh_critical_owner_transactions_v1','parity_verification.json')
assert op['all4_candidates_and102_stage_paths_equal_historical_native_validated_states']
assert len(r['owner_stage']['rows'])==len(owners['rows'])==4
total=0
for a,z in zip(r['owner_stage']['rows'],owners['rows']):
    for key in ('plan','state','transaction_complete','published','critical_delay_improved'):
        assert a[key]==z[key],key
    assert len(a['events'])==len(z['events'])
    for x,y in zip(a['events'],z['events']):
        assert clean(x,('certificate','certificate_sha256'))==clean(y,('certificate','certificate_sha256'))
        assert sha(x['certificate'])==x['certificate_sha256']
        assert json.loads(Path(x['certificate']).read_text())==json.loads(Path(y['certificate']).read_text())
    total+=len(a['events'])
assert total==102
eligible=[(row['plan']['critical'],0 if row['plan']['order']=='ASCENDING' else 1,i)
          for i,row in enumerate(r['owner_stage']['rows']) if row['transaction_complete']]
selected=min(eligible)[2]
assert selected==r['selected_owner_plan']==p['selected_owner_plan']
wire=historical('direct_owner_global_wire_v1')
wp=historical('direct_owner_global_wire_v1','verification.json')
assert wp['all1929_events_and_complete_original_xml_fraction_frame_pass'] and wp['all_dynamic_model_guards_pass']
assert len(r['passes'])==1 and p['active_pass_indices']==[2]
stage=r['passes'][0];assert stage['pass_index']==2
for key in ('initial_wire','final_wire','state'):assert stage[key]==wire[key]
assert len(stage['events'])==len(wire['events'])==1929
state={cid:[list(x) for x in path] for cid,path in r['owner_stage']['rows'][selected]['state'].items()}
for x,y in zip(stage['events'],wire['events']):
    assert clean(x)==clean(y)
    if x['status']=='COMMIT':state[str(x['connection_id'])]=x['new_path']
assert state==r['state']==stage['state']==wire['state']
assert r['minrc_native_calls']==14 and r['owner_native_calls']==102 and r['wire_native_calls']==892 and r['fallback_calls']==0
covered=sum(r[k]['elapsed_seconds'] for k in ('budget_stage','discovery_stage','owner_stage'))+sum(s['elapsed_seconds'] for s in r['passes'])
assert 0<covered<=r['candidate_elapsed_seconds']
bindings[str(Path(__file__))]=sha(Path(__file__))
assert all(sha(path)==digest for path,digest in bindings.items())
out=dict(bindings=bindings,all8_budget_attempts_and_complete_state_equal=True,
         all6_critical_owner_searches_and_blockers_equal=True,
         all4_owner_candidates_and102_stage_certificate_contents_equal=True,
         all1929_wire_events_answers_work_counts_and_full_state_equal=True,
         candidate_elapsed_seconds=r['candidate_elapsed_seconds'],
         covered_stage_seconds=covered,unclassified_seconds=r['candidate_elapsed_seconds']-covered,
         original_budget_violation_ids=[785,1637],budget_safe_connections=1927,final_wire=11497,all_dynamic_model_guards_pass=True,
         full_workflow_seconds=None,
         scope='Independent full-trace identity inherits original XML/Fraction, owner potential certificates and complete exact dynamic model state evidence; actual native acceptance remains downstream. Production uses live raw-route state and derives all downstream candidate values, historical references only verifier. Single clock from provided post-resume route to candidate; upstream route/endpoints/budgets and downstream VPR/canonical/audits, final receipt serialization and close excluded. No new VPR execution, full-workflow or paired speedup, original HDL equivalence or unseen-family claim.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n')
print({k:v for k,v in out.items() if k!='bindings'},flush=True)
