"""Record limited seed5 posterior repair without replacing frozen validation."""
from pathlib import Path
import hashlib
import json
import time

R = Path(__file__).resolve().parents[1]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    previous = R / 'work/current_research_claim_matrix_v16_20261020/matrix.json'
    matrix = json.loads(previous.read_text())
    for name, expected in matrix['source_sha256'].items():
        assert sha(R / name) == expected, name
    evidence = [
        'work/apex2_seed5_frozen_reverse_wirelength_refinement_20261020/independent_audit.json',
        'work/apex2_seed5_lexicographic_refinement_20261020/independent_audit.json',
        'work/apex2_seed5_ranked_critical_refinement_20261020/interruption_review.json',
        'work/apex2_seed5_ranked_delay_objective_20261020/independent_audit.json',
        'work/apex2_seed5_critical_capacity_closure_v2_20261020/independent_construction_review.json',
        'work/apex2_seed5_critical_capacity_closure_v2_20261020/native_queue/task621/independent_native_audit.json',
        'work/apex2_seed5_final_joint_pass_native_recheck_20261020/compatibility_audit.json',
    ]
    values = [json.loads((R / name).read_text()) for name in evidence]
    for value in values:
        for path, expected in value['source_sha256'].items():
            assert sha(path) == expected, path
    assert values[0]['final_private_cpd_ns'] == 11.2868 and not values[0]['final_original_baseline_joint_pass']
    assert values[3]['final_private_cpd_ns'] == 11.2247 and not values[3]['final_original_baseline_joint_pass']
    assert (values[4]['restored_nets'], values[4]['total_nets']) == (789, 856)
    native = values[5]
    assert all(native['checks'].values())
    assert (native['wirelength'], native['cpd_ns'], native['model_crossings']) == (18917, 11.202, 1442)
    assert values[6]['timing_CSV_bytes_identical']
    quality = next(c for c in matrix['claims'] if c['id'] == 'Q5')
    quality['limits'] = 'Seed1 and seed5 now have posterior joint repairs under evolved policies. Frozen final seed1 policy still fails seed5 at11.2868ns. Later seed5 closure restores789of856nets and retains only8WLgain/1.6psCPDmargin. Original reserved3of5jointpasses unchanged. No common frozen-policy independent validation, statistical generalization or FPGA acceleration.'
    quality['evidence'].extend(evidence)
    matrix['claims'].append({
        'id': 'Q7', 'gates': ['G2', 'G4', 'G8'],
        'claim': 'Capacity-aware baseline restoration repairs known apex2 seed5 joint native quality',
        'status': 'supported_in_declared_scope', 'evidence': evidence,
        'measurements': {'wirelength': 18917, 'baseline_wirelength': 18925,
                         'cpd_ns': 11.202, 'baseline_cpd_ns': 11.2036,
                         'modeled_crossings': 1442, 'baseline_modeled_crossings': 1442,
                         'restored_nets': 789, 'total_nets': 856, 'unique_native_trees': 1},
        'limits': 'Known failure used repeatedly for posterior development. Three fixed closure arms deduplicate to one native tree. Only67candidate nets retained,not necessarily all different from baseline. Exact mixture/native legality/capacity pass;legacy/source-bound metrics and3500roundedtimingrows identical. Tiny gains not significance. Earlier frozen-policy failure and originalreservedcohort retained. No fullpipeline repeat,independent unseen-seed validation,physicalSLLorboardperformance.',
    })
    out = R / 'work/current_research_claim_matrix_v17_20261020'
    out.mkdir()
    plan = R / 'experiments/research_plan.json'
    (out / 'plan_snapshot.json').write_bytes(plan.read_bytes())
    evidence.extend([str((out / 'plan_snapshot.json').relative_to(R)), str(Path(__file__).resolve().relative_to(R))])
    for name in evidence:
        matrix['source_sha256'][name] = sha(R / name)
    matrix.update(schema='dieroute.claim_matrix.v17', recorded_ns=time.time_ns(),
                  predecessor={'path': str(previous.relative_to(R)), 'sha256': sha(previous)})
    assert len(matrix['gates']) == 8 and all(g['status'] != 'complete' for g in matrix['gates'])
    target = out / 'matrix.json'
    target.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + '\n')
    value = json.loads(plan.read_text())
    value['current_claim_matrix'] = {'path': str(target.relative_to(R)), 'sha256': sha(target),
                                     'status': matrix['status'], 'research_complete': False}
    value['apex2_seed5_capacity_closure'].update(status='posterior_joint_pass_exact_mixture_and_final_reload_verified',
                                                recheck_audit=evidence[6])
    next(g for g in value['gates'] if g['id'] == 'G4')['posterior_seed5_capacity_closure_audit'] = evidence[4]
    plan.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'claims': len(matrix['claims']), 'sources': len(matrix['source_sha256']),
                      'open_gates': 8, 'research_complete': False}))


if __name__ == '__main__':
    main()
