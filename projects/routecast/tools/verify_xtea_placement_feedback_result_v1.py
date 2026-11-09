"""Independent geometry, selection, final gate and explicit-cost reconstruction."""
import json
from pathlib import Path
import sys
from collections import defaultdict

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools/native_resume_prototype'))
from pre_route_endpoints import sha, placements
from source_binding_v2 import closure


def main():
    bindings = closure([Path(__file__)])

    def certified(directory, flag):
        p = directory / 'verification.json'
        v = json.loads(p.read_text())
        assert v[flag]
        for path, digest in v['bindings'].items():
            assert sha(path) == digest, path
            assert path not in bindings or bindings[path] == digest
            bindings[path] = digest
        bindings[str(p)] = sha(p)
        return v

    cohort = R / 'experiments/xtea_placement_feedback_cohort_v2_2026-10-13'
    decisions = R / 'experiments/xtea_placement_feedback_decisions_v1_2026-10-13'
    native = R / 'experiments/xtea_placement_feedback_native_v1_2026-10-13'
    cv = certified(cohort, 'all_eight_legal_moves_and_complete_endpoint_identity_pass')
    dv = certified(decisions, 'decisions_frozen_before_new_native_labels')
    nv = certified(native, 'all_selected_native_physical_and_canonical_pass')
    protocol = json.loads((cohort / 'protocol.json').read_text())
    decision = json.loads((decisions / 'decision.json').read_text())
    assert sha(decisions / 'decision.json') == dv['decision_sha256']
    original_ep = json.loads(Path(protocol['baseline_endpoint']).read_text())
    original_place = placements(original_ep['inputs']['place']['path'], original_ep['inputs']['net']['sha256'])
    mapping = json.loads((Path(original_ep['inputs']['net']['path']).parent / 'mapping.json').read_text())
    allowed_nets = {q['net_id'] for q in original_ep['connections']}
    members = defaultdict(set)
    for pin in mapping['pin_details']:
        if pin['net_id'] in allowed_nets:
            members[pin['net_id']].add(pin['block'])
    assert set(members) == allowed_nets

    def geometry(pos):
        boxes = []
        for names in members.values():
            xs = sorted(pos[n][0] for n in names)
            ys = sorted(pos[n][1] for n in names)
            boxes.append(xs[-1] - xs[0] + ys[-1] - ys[0])
        return sum(boxes)

    assert geometry(original_place) == protocol['baseline_hpwl']
    rows = {r['candidate_id']: r for r in decision['rows']}
    assert set(rows) == set(range(9)) and rows[0]['hpwl'] == geometry(original_place)
    totals = defaultdict(float)
    checks = []
    for item, frozen in zip(cv['rows'], protocol['selected']):
        cid = item['candidate_id']
        assert cid == frozen['candidate_id']
        ep = json.loads(Path(item['endpoint']).read_text())
        pos = placements(ep['inputs']['place']['path'], ep['inputs']['net']['sha256'])
        assert set(pos) == set(original_place)
        a, b = frozen['pair']
        assert {n for n in pos if pos[n] != original_place[n]} == {a, b}
        assert pos[a][:4] == original_place[b][:4] and pos[b][:4] == original_place[a][:4]
        assert all(pos[n][4] == original_place[n][4] for n in pos)
        hpwl = geometry(pos)
        assert hpwl == frozen['hpwl'] == rows[cid]['hpwl'] <= rows[0]['hpwl']
        assert hpwl - rows[0]['hpwl'] == frozen['hpwl_delta']
        directory = decisions / ('candidate_%02d' % cid)
        model = directory / 'model'
        sketch = json.loads((model / 'sketch.json').read_text())
        assert sketch['completed_connections'] == sketch['required_connections'] == 2450
        assert rows[cid]['sketch_overflow'] == sketch['overflow_units']
        for stage, seconds in rows[cid]['stage_seconds'].items():
            terminal = json.loads((directory / (stage + '_terminal.json')).read_text())
            assert terminal['exit_status'] == 0 and terminal['process_seconds'] == seconds
            totals[stage] += seconds
        warm = json.loads((directory / 'prepared/warm/verification.json').read_text())
        totals['full_zero_cost_rebuild_audit_nested_in_prepare'] += warm['full_rebuild_audit_seconds']
        checks.append(dict(candidate_id=cid, independently_rebuilt_hpwl=hpwl, audited_sketch_overflow=sketch['overflow_units']))
    eligible = [cid for cid in sorted(rows) if rows[cid]['sketch_overflow'] <= rows[0]['sketch_overflow']]
    off = sorted(rows, key=lambda cid: (rows[cid]['hpwl'], cid))[0]
    on = sorted(eligible, key=lambda cid: (rows[cid]['hpwl'], cid))[0]
    assert eligible == decision['on_admitted_candidates']
    assert (off, on) == (decision['off_candidate'], decision['on_candidate'])
    natives = {r['candidate_id']: r for r in json.loads((native / 'rows.json').read_text())}
    assert set(natives) == {0, off, on}
    result = json.loads((native / 'result.json').read_text())
    for arm, cid in [('off', off), ('on', on)]:
        r, baseline = natives[cid], natives[0]
        accepted = cid != 0 and r['wirelength'] < baseline['wirelength'] and r['diagnostic_cpd_ns'] <= baseline['diagnostic_cpd_ns']
        final_id = cid if accepted else 0
        final = result['arms'][arm]
        assert final['native_gate_accepted'] == accepted and final['final_candidate_id'] == final_id
        assert final['final_wirelength'] == natives[final_id]['wirelength']
        assert final['final_diagnostic_cpd_ns'] == natives[final_id]['diagnostic_cpd_ns']
        final_ep = json.loads(Path(rows[final_id]['endpoint']).read_text())
        assert placements(final['final_placement'], final_ep['inputs']['net']['sha256']) == placements(final_ep['inputs']['place']['path'], final_ep['inputs']['net']['sha256'])
        assert Path(final['final_route']).resolve() == (native / ('candidate_%02d' % final_id) / 'output.route').resolve()
    sum_stages = sum(v for k, v in totals.items() if k != 'full_zero_cost_rebuild_audit_nested_in_prepare')
    assert sum_stages <= decision['full_decision_driver_seconds']
    evidence = dict(
        bindings=bindings, all_bound_artifacts_rechecked=True,
        all_eight_geometries_selections_and_symmetric_final_gates_reconstructed=True,
        candidate_checks=checks, on_admitted_candidates=eligible,
        final_arms=result['arms'],
        native_rows=[{k: r[k] for k in ['candidate_id', 'wirelength', 'diagnostic_cpd_ns', 'iterations', 'native_process_seconds']} for r in natives.values()],
        costs=dict(common_cohort_preparation_seconds=cv['whole_preparation_seconds'], candidate_stage_process_seconds=dict(totals), sum_disjoint_candidate_stages_seconds=sum_stages, measured_decision_driver_seconds=decision['full_decision_driver_seconds'], measured_native_evaluation_driver_seconds=result['full_native_driver_seconds'], note='Nested full-rebuild audit time is included in prepare and is not added again. Cohort/decision/native driver timers are separate research phases, not a matched fresh end-to-end on/off benchmark. Original RR/packing/placement/timing capture and prior-sketch construction are reused and remain additional/amortized costs.'),
        positive_net_time_gain_proven=False, unseen_family_validation=False,
        scope='Eight frozen development moves and actual SKETCH-gated placement selection, with native results only after decision freeze. Same complete legality and native quality gate in both arms. Diagnostic printed CPD on experimental async architecture; no TP live-state integration, hardware, or generalization claim.',
    )
    assert all(sha(p) == h for p, h in bindings.items())
    with (native / 'independent_result_verification_v1.json').open('x') as f:
        f.write(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps({k: v for k, v in evidence.items() if k not in ['bindings', 'candidate_checks']}, indent=2), flush=True)


if __name__ == '__main__':
    main()
