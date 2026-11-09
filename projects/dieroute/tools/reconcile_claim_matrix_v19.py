"""Record one recovered frozen-policy seed result without claiming cohort success."""
from pathlib import Path
import hashlib
import json
import time

R = Path(__file__).resolve().parents[1]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def main():
    previous = R / 'work/current_research_claim_matrix_v18_20261020/matrix.json'
    matrix = json.loads(previous.read_text())
    for name, expected in matrix['source_sha256'].items():
        assert sha(R / name) == expected, name
    evidence = [
        'work/prospective_apex2_seeds6_10_baselines_20261020/candidate_policy.json',
        'work/prospective_apex2_seeds6_10_initial_reviews_20261020/apex2_seed6/audit.json',
        'work/prospective_apex2_seeds6_10_native_modes_20261020/apex2_seed6/wirelength/mode_audit.json',
        'work/prospective_native_mode_receipt_recovery_20261020/seed6_recovery_audit.json',
        'work/prospective_native_mode_receipt_recovery_20261020/seed6_original_failure_snapshot.json',
        'work/prospective_apex2_seeds6_10_native_modes_20261020/apex2_seed6/wirelength/launch_receipt.json',
    ]
    values = [json.loads((R / name).read_text()) for name in evidence]
    for value in values:
        for name, expected in value.get('source_sha256', {}).items():
            assert sha(name) == expected, name
    assert values[0]['status'] == 'frozen_before_new_baseline_outcomes'
    assert values[0]['cohort']['seeds'] == list(range(6, 11))
    assert not values[1]['joint_quality_pass']
    mode, recovery, failure, receipt = values[2:]
    assert mode['final_original_baseline_joint_pass'] and recovery['joint_quality_pass']
    assert failure['status'] == 'native_mode_audit_error_retained_no_replay'
    assert receipt['status'] == 'reconstructed_after_terminal_missing_original_launch_receipt'
    assert receipt['original_launch_time_ns'] is None
    final = mode['current_state']
    assert (final['wirelength'], final['cpd_ns'], final['model_crossings']) == (17865, 11.1809, 1505)
    leaf = json.loads(Path(final['audit']).read_text())
    assert all(leaf['checks'].values())
    matrix['claims'].append({
        'id': 'Q9', 'gates': ['G2', 'G4', 'G8'],
        'claim': 'One declared new-seed frozen-policy attempt reaches joint quality after read-only receipt recovery',
        'status': 'supported_in_declared_scope', 'evidence': evidence.copy(),
        'measurements': {'label': 'apex2_seed6', 'planned_cohort_seeds': [6, 7, 8, 9, 10],
                         'reviewed_final_cases_in_this_claim': 1, 'wirelength': 17865, 'baseline_wirelength': 19306,
                         'cpd_ns': 11.1809, 'baseline_cpd_ns': 11.1843,
                         'modeled_crossings': 1505, 'baseline_modeled_crossings': 1505, 'native_mode_stages': 16},
        'limits': 'Policy frozen before baseline outcomes; same-circuit newseed only. Original audit failed solely because launch_receipt.json was absent. Receipt explicitly reconstructed after terminal; original mode/capacity failures retained. Read-only chain/order/budget/wirelength and final baseline identity checks pass without search rerun or policy change. Other4seeds still running; no 5seed success rate, fullpipeline repeats, statistical timing significance, independent circuit generalization, physicalSLL or board acceleration.',
    })
    quality = next(c for c in matrix['claims'] if c['id'] == 'Q5')
    quality['limits'] += ' One new-seed frozen-policy result,seed6,now passes after missing-receipt audit recovery; the declared5seed cohort remains incomplete and no cohort-level generalization is established.'
    out = R / 'work/current_research_claim_matrix_v19_20261020'
    out.mkdir()
    plan = R / 'experiments/research_plan.json'
    (out / 'plan_snapshot.json').write_bytes(plan.read_bytes())
    evidence.extend([str((out / 'plan_snapshot.json').relative_to(R)), str(Path(__file__).resolve().relative_to(R))])
    for name in evidence:
        matrix['source_sha256'][name] = sha(R / name)
    matrix.update(schema='dieroute.claim_matrix.v19', recorded_ns=time.time_ns(),
                  predecessor={'path': str(previous.relative_to(R)), 'sha256': sha(previous)})
    assert len(matrix['gates']) == 8 and all(g['status'] != 'complete' for g in matrix['gates'])
    target = out / 'matrix.json'
    target.write_text(json.dumps(matrix, indent=2, ensure_ascii=False) + '\n')
    value = json.loads(plan.read_text())
    value['current_claim_matrix'] = {'path': str(target.relative_to(R)), 'sha256': sha(target),
                                     'status': matrix['status'], 'research_complete': False}
    next(g for g in value['gates'] if g['id'] == 'G4')['frozen_seed6_receipt_recovered_result'] = evidence[3]
    temp = plan.with_suffix('.matrix19.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temp.replace(plan)
    print(json.dumps({'claims': len(matrix['claims']), 'sources': len(matrix['source_sha256']), 'open_gates': 8}))


if __name__ == '__main__':
    main()
