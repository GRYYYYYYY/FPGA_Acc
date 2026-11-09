"""Record seed6 posterior repair, preserving all frozen-cohort limitations."""
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
    previous = R / 'work/current_research_claim_matrix_v17_20261020/matrix.json'
    matrix = json.loads(previous.read_text())
    for name, expected in matrix['source_sha256'].items():
        assert sha(R / name) == expected, name
    evidence = [
        'work/prospective_parent_interim_quality_20261020/audit.json',
        'work/prospective_parent_net_changes_20261020/analysis.json',
        'work/prospective_parent_critical_delay_diagnosis_20261020/critical_overlap.json',
        'work/prospective_parent_critical_delay_diagnosis_20261020/path_profile.json',
        'work/prospective_parent_critical_delay_diagnosis_20261020/capacity_delay_floors.json',
        'work/prospective_parent_critical_delay_diagnosis_20261020/blocker_subset_floors.json',
        'work/posterior_critical_minimum_blocker_exchange_20261020/native_summary.json',
        'work/posterior_seed6_exchange_followup_20261020/native_summary.json',
        'work/posterior_seed6_exchange_followup_20261020/supervisor_failure_review.json',
        'work/native_review_startup_race_regression_20261020/regression_audit.json',
        'work/posterior_seed6_bounded_wire_cleanup_20261020/independent_audit.json',
        'work/posterior_seed6_final_joint_pass_native_recheck_20261020/tree_preflight/independent_preflight.json',
        'work/posterior_seed6_final_joint_pass_native_recheck_20261020/compatibility_audit.json',
    ]
    values = [json.loads((R / name).read_text()) for name in evidence]
    for value in values:
        for name, expected in value.get('source_sha256', {}).items():
            assert sha(name) == expected, name
    assert values[6]['native_joint_passes'] == 0
    assert values[7]['joint_passes'] == 0
    outcome, = values[10]['outcomes']
    assert outcome['joint_baseline_pass'] and outcome['nets_visited'] == outcome['accepted'] == 1
    final = values[-1]
    assert (final['wirelength'], final['cpd_ns'], final['modeled_crossings']) == (19228, 11.1417, 1199)
    assert final['timing_CSV_bytes_identical'] and final['connections'] == 3500
    assert not any(c['id'] == 'Q8' for c in matrix['claims'])
    matrix['claims'].append({
        'id': 'Q8', 'gates': ['G2', 'G4', 'G8'],
        'claim': 'Posterior blocker exchanges plus bounded wire cleanup jointly repair known apex2 seed6',
        'status': 'supported_in_declared_scope', 'evidence': evidence.copy(),
        'measurements': {k: final[k] for k in ['wirelength', 'baseline_wirelength', 'cpd_ns', 'baseline_cpd_ns',
                                              'modeled_crossings', 'baseline_modeled_crossings']},
        'limits': 'Separate posterior development after observing seed6 failure. Initial7exchange arms have0jointpasses; followup3arms improveCPDbutfailWL; oneacceptedcleanupnet establishesjointpass. Exactnative reloads agree. Does not replace running frozen seeds6to10 pipeline outcomes or original reserved3of5. No fullpipeline repeats, independent circuit generalization, statistical significance, physicalSLL or board acceleration.',
    })
    quality = next(c for c in matrix['claims'] if c['id'] == 'Q5')
    quality['limits'] += ' Seed6 additionally has a separate posterior joint repair; frozen seeds6to10 pipeline remains ongoing and must be reported independently.'
    out = R / 'work/current_research_claim_matrix_v18_20261020'
    out.mkdir()
    plan = R / 'experiments/research_plan.json'
    (out / 'plan_snapshot.json').write_bytes(plan.read_bytes())
    evidence.extend([str((out / 'plan_snapshot.json').relative_to(R)), str(Path(__file__).resolve().relative_to(R))])
    for name in evidence:
        matrix['source_sha256'][name] = sha(R / name)
    matrix.update(schema='dieroute.claim_matrix.v18', recorded_ns=time.time_ns(),
                  predecessor={'path': str(previous.relative_to(R)), 'sha256': sha(previous)})
    assert len(matrix['gates']) == 8 and all(g['status'] != 'complete' for g in matrix['gates'])
    target = out / 'matrix.json'
    target.write_text(json.dumps(matrix, indent=2, ensure_ascii=False) + '\n')
    value = json.loads(plan.read_text())
    value['current_claim_matrix'] = {'path': str(target.relative_to(R)), 'sha256': sha(target),
                                     'status': matrix['status'], 'research_complete': False}
    next(g for g in value['gates'] if g['id'] == 'G4')['posterior_seed6_joint_repair'] = evidence[12]
    temp = plan.with_suffix('.matrix18.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temp.replace(plan)
    print(json.dumps({'claims': len(matrix['claims']), 'sources': len(matrix['source_sha256']), 'open_gates': 8}))


if __name__ == '__main__':
    main()
