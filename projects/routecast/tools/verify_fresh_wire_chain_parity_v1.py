"""Authenticate fresh full-cohort production against frozen independent evidence."""
import json
from pathlib import Path
from pre_route_endpoints import sha

R = Path(__file__).resolve().parents[1]
E = R / 'experiments'
bindings = {}

def read(directory, filename):
    path = E / (directory + '_2026-10-08') / filename
    value = json.loads(path.read_text())
    for name, digest in value.get('bindings', {}).items():
        assert sha(name) == digest, name
        assert name not in bindings or bindings[name] == digest
        bindings[name] = digest
    bindings[str(path)] = sha(path)
    return value

owner = read('fresh_critical_owner_transactions_v1', 'receipt.json')
op = read('fresh_critical_owner_transactions_v1', 'parity_verification.json')
assert op['all4_candidates_and102_stage_paths_equal_historical_native_validated_states']
eligible = [(row['plan']['critical'], 0 if row['plan']['order'] == 'ASCENDING' else 1, i)
            for i, row in enumerate(owner['rows']) if row['transaction_complete']]
selected = min(eligible)[2]
previous = owner['rows'][selected]['state']
pairs = [('fresh_wire_contraction_round1_v2', 'complete_wire_contraction_v1', 'verification.json'),
         ('fresh_wire_contraction_round2_v1', 'complete_wire_contraction_v2', 'verification_v3.json'),
         ('fresh_wire_contraction_global_v1', 'global_guard_wire_contraction_static_multiplicity_v1', 'verification.json')]
rows = []
for fresh, historical, proof_name in pairs:
    new = read(fresh, 'receipt.json')
    old = read(historical, 'receipt.json')
    proof = read(fresh, 'verification.json')
    hp = read(historical, proof_name)
    assert proof['all1929_events_and_complete_original_xml_fraction_frame_pass']
    assert hp['all1929_events_and_complete_original_xml_fraction_frame_pass']
    for key in ('scale', 'initial_wire', 'final_wire', 'state'):
        assert new[key] == old[key], (fresh, key)
    assert len(new['events']) == len(old['events']) == 1929
    assert [e['connection_id'] for e in new['events']] == list(range(1929))
    for a, b in zip(new['events'], old['events']):
        assert {k:v for k,v in a.items() if k != 'search_seconds'} == b if 'search_seconds' not in b else {k:v for k,v in a.items() if k != 'search_seconds'} == {k:v for k,v in b.items() if k != 'search_seconds'}
        if a['status'] == 'COMMIT':
            previous[str(a['connection_id'])] = a['new_path']
    assert previous == new['state']
    rows.append(dict(stage=fresh, queries=1929, commits=proof['commits'], initial_wire=new['initial_wire'], final_wire=new['final_wire'], component_seconds=new.get('component_elapsed_seconds', new.get('elapsed_seconds'))))

static = read('global_guard_wire_contraction_static_multiplicity_v1', 'parity_verification.json')
assert static['native_evidence_inherited_by_exact_complete_state_equality']
native = read('global_guard_wire_contraction_v1', 'receipt.json')
quality = read('global_guard_wire_contraction_v1', 'native_quality_verification.json')
assert previous == native['state'] and quality['full_chain_pass'] and quality['joint_quality_pass']
assert quality['initial_fixups'] == 99 and quality['canonical_fixups'] == 0
topology = read('fresh_wire_contraction_global_v1', 'topology_verification.json')
assert topology['all_static_query_multiplicity_bounds_and_attaining_paths_pass']
bindings[str(Path(__file__))] = sha(Path(__file__))
assert all(sha(p) == h for p,h in bindings.items())
out = dict(bindings=bindings, selected_fresh_owner_plan=selected,
           all5787_semantic_events_search_answers_work_counts_and_full_states_equal=True,
           all_three_fresh_states_reconstructed_from_selected_owner_and_commits=True,
           native_evidence_inherited_by_exact_complete_state_equality=True,
           native_cpd_ns=quality['cpd_ns'], native_wirelength=quality['wirelength'],
           first_native_fixups=99, canonical_fixups=0, original_budget_violation_ids=[785,1637],
           stages=rows, full_workflow_seconds=None,
           scope='Historical references used only in this verifier; full fresh production chain preserves all queries and original budgets. Native evidence inherited by complete path identity, no new VPR run. Separate stage clocks are not end-to-end or paired speedup evidence. Upstream input generation, shared driver, native acceptance costs, original HDL equivalence and unseen-family validity remain incomplete.')
path = E / 'fresh_wire_contraction_global_v1_2026-10-08/chain_parity_verification.json'
path.write_text(json.dumps(out, indent=2) + '\n')
print({k:v for k,v in out.items() if k != 'bindings'}, flush=True)
