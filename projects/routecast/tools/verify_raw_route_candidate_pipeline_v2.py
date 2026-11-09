"""Authenticate every stage of the single-clock raw-route candidate pipeline."""
import json
from pathlib import Path
from pre_route_endpoints import sha

R = Path(__file__).resolve().parents[1]
E = R / 'experiments'
D = E / 'raw_route_candidate_pipeline_v2_2026-10-08'
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
p=read(D/'protocol.json')
assert r['protocol_sha256']==sha(D/'protocol.json')
b=historical('fresh_native_budget_repairs_v1')
proof=historical('fresh_native_budget_repairs_v1','verification.json')
assert proof['budget_safe_connections']==1927
stage=r['budget_stage']
for key in ('initial_rows','initial_budget_violation_ids','state','final_budget_violation_ids'):
    assert stage[key]==b[key],key
assert len(stage['events'])==len(b['events'])==8
for a,z in zip(stage['events'],b['events']):assert clean(a)==clean(z)
discovery=historical('fresh_critical_owner_discovery_v1')
dp=historical('fresh_critical_owner_discovery_v1','verification.json')
assert dp['all_blocking_node_owner_sets_reconstructed']
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
        assert sha(x['certificate'])==x['certificate_sha256']==y['certificate_sha256']
    total+=len(a['events'])
assert total==102
eligible=[(row['plan']['critical'],0 if row['plan']['order']=='ASCENDING' else 1,i)
          for i,row in enumerate(r['owner_stage']['rows']) if row['transaction_complete']]
selected=min(eligible)[2]
assert selected==r['selected_owner_plan']==p['selected_owner_plan']
wire=historical('shared_fresh_wire_pipeline_v2')
wp=historical('shared_fresh_wire_pipeline_v2','verification.json')
assert wp['all5787_semantic_events_search_answers_and_work_counts_equal']
assert len(r['passes'])==len(wire['passes'])==3
state={cid:[list(x) for x in path] for cid,path in r['owner_stage']['rows'][selected]['state'].items()}
for a,z in zip(r['passes'],wire['passes']):
    for key in ('pass_index','initial_wire','final_wire','state'):assert a[key]==z[key]
    assert len(a['events'])==len(z['events'])==1929
    for x,y in zip(a['events'],z['events']):
        assert clean(x)==clean(y)
        if x['status']=='COMMIT':state[str(x['connection_id'])]=x['new_path']
    assert state==a['state']
assert state==r['state']==wire['state']
assert r['minrc_native_calls']==14 and r['wire_native_calls']==4733 and r['fallback_calls']==0
covered=sum(r[k]['elapsed_seconds'] for k in ('budget_stage','discovery_stage','owner_stage'))+sum(s['elapsed_seconds'] for s in r['passes'])
assert 0<covered<=r['candidate_elapsed_seconds']
bindings[str(Path(__file__))]=sha(Path(__file__))
assert all(sha(path)==digest for path,digest in bindings.items())
out=dict(bindings=bindings,all8_budget_attempts_and_complete_state_equal=True,
         all6_critical_owner_searches_and_blockers_equal=True,
         all4_owner_candidates_and102_stage_certificates_equal=True,
         all5787_wire_events_answers_work_counts_and_full_states_equal=True,
         candidate_elapsed_seconds=r['candidate_elapsed_seconds'],
         covered_stage_seconds=covered,unclassified_seconds=r['candidate_elapsed_seconds']-covered,
         original_budget_violation_ids=[785,1637],budget_safe_connections=1927,final_wire=11474,
         full_workflow_seconds=None,
         scope='Independent full-trace identity inherits original XML/Fraction, owner potential certificates and complete native state evidence. Production uses live raw-route state and derives all downstream candidate values, historical references only verifier. Single clock from provided post-resume route to candidate; upstream route/endpoints/budgets and downstream VPR/canonical/audits, final receipt serialization and close excluded. No new VPR execution, full-workflow or paired speedup, original HDL equivalence or unseen-family claim.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n')
print({k:v for k,v in out.items() if k!='bindings'},flush=True)
