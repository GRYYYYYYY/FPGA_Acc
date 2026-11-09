"""Full trace identity and single-driver component cost boundary verification."""
import json
from pathlib import Path
from pre_route_endpoints import sha

R = Path(__file__).resolve().parents[1]
E = R / 'experiments'
D = E / 'shared_fresh_wire_pipeline_v1_2026-10-08'
bindings = {}

def read(path):
    obj = json.loads(path.read_text())
    for name, digest in obj.get('bindings', {}).items():
        assert sha(name) == digest, name
        assert name not in bindings or bindings[name] == digest
        bindings[name] = digest
    bindings[str(path)] = sha(path)
    return obj

r = read(D / 'receipt.json')
p = read(D / 'protocol.json')
assert sha(D / 'protocol.json') == r['protocol_sha256']
chain = read(E / 'fresh_wire_contraction_global_v1_2026-10-08/chain_parity_verification.json')
assert chain['all5787_semantic_events_search_answers_work_counts_and_full_states_equal']
owner = read(E / 'fresh_critical_owner_transactions_v1_2026-10-08/receipt.json')
eligible = [(row['plan']['critical'], 0 if row['plan']['order']=='ASCENDING' else 1, i)
            for i,row in enumerate(owner['rows']) if row['transaction_complete']]
selected = min(eligible)[2]
assert selected == p['selected_owner_plan'] == chain['selected_fresh_owner_plan']
state = {cid:[list(x) for x in path] for cid,path in owner['rows'][selected]['state'].items()}
names = ['fresh_wire_contraction_round1_v2', 'fresh_wire_contraction_round2_v1', 'fresh_wire_contraction_global_v1']
assert len(r['passes']) == 3 and p['max_labels_by_pass'] == [10000,100000,100000]
search_seconds = 0
commits = []
for index,(stage,name) in enumerate(zip(r['passes'],names)):
    old = read(E / (name+'_2026-10-08') / 'receipt.json')
    assert stage['pass_index'] == index
    for key in ('initial_wire','final_wire','state'):
        assert stage[key] == old[key]
    assert len(stage['events']) == len(old['events']) == 1929
    assert [e['connection_id'] for e in stage['events']] == p['query_order'] == list(range(1929))
    count = 0
    for a,b in zip(stage['events'],old['events']):
        assert {k:v for k,v in a.items() if k!='search_seconds'} == {k:v for k,v in b.items() if k!='search_seconds'}
        search_seconds += a.get('search_seconds',0)
        if a['status']=='COMMIT':
            state[str(a['connection_id'])] = a['new_path']
            count += 1
    assert state == stage['state']
    assert stage['elapsed_seconds'] >= sum(e.get('search_seconds',0) for e in stage['events'])
    commits.append(count)
assert state == r['state'] and commits == [46,10,113]
assert abs(search_seconds-r['search_seconds']) < 1e-8
assert r['elapsed_seconds'] >= sum(s['elapsed_seconds'] for s in r['passes'])
assert 0 <= r['native_input_preparation_seconds'] <= search_seconds
assert r['fallback_calls'] == 0
residual = r['elapsed_seconds']-r['setup_nonphase_seconds']-sum(r['phases_seconds'].values())-search_seconds
assert residual >= -1e-6
bindings[str(Path(__file__))] = sha(Path(__file__))
assert all(sha(path)==digest for path,digest in bindings.items())
out = dict(bindings=bindings, all5787_semantic_events_search_answers_and_work_counts_equal=True,
           all_three_complete_frames_independently_certified_by_trace_identity=True,
           native_evidence_inherited_by_final_state_identity=True,
           commits_by_pass=commits, final_wire=11474,
           component_elapsed_seconds=r['elapsed_seconds'], search_seconds=search_seconds,
           setup_nonphase_seconds=r['setup_nonphase_seconds'], phases_seconds=r['phases_seconds'],
           unclassified_seconds=residual, native_calls=r['native_calls'], fallback_calls=0,
           original_budget_violation_ids=[785,1637], full_workflow_seconds=None,
           scope='Single-process wire component reuses one fresh CSR/native context/ledger; every event matches the independently audited fresh chain. Timing initialized from actual current state at third pass. Native evidence inherited, no new VPR run. Upstream state generation and downstream native/canonical/audits excluded. No paired or complete workflow speedup, original HDL equivalence or unseen-family claim.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n')
print({k:v for k,v in out.items() if k!='bindings'},flush=True)
