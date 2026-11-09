"""Retain prior failures while recording audited posterior apex2 joint repair."""
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
    previous = R / 'work/current_research_claim_matrix_v15_20261020/matrix.json'
    matrix = json.loads(previous.read_text())
    for name, expected in matrix['source_sha256'].items():
        assert sha(R / name) == expected, name
    root = 'work/apex2_seed1_reverse_sink_wirelength_refinement_20261020/'
    evidence = [root + name for name in ['independent_audit.json', 'policy_audit.json',
                                        'wirelength_audit.json', 'sink_order_audit.json']]
    evidence.extend(['work/apex2_seed1_final_joint_pass_native_recheck_20261020/compatibility_audit.json',
                     'work/apex2_rounded_refinement_first_five_cost_20261020/audit.json',
                     'work/apex2_exact_wirelength_weights_20261020/audit.json',
                     'work/wirelength_capped_search_oracle_20261020/audit.json'])
    chain = json.loads((R / evidence[0]).read_text())
    assert chain['final_original_baseline_joint_pass']
    state = chain['final_private_state']
    assert (state['wirelength'], state['cpd_ns'], state['model_crossings']) == (19170, 10.8308, 1452)
    reload = json.loads((R / evidence[4]).read_text())
    assert reload['timing_CSV_bytes_identical']
    for name in evidence:
        value = json.loads((R / name).read_text())
        for source, expected in value['source_sha256'].items():
            assert sha(source) == expected, source
    quality = next(c for c in matrix['claims'] if c['id'] == 'Q5')
    quality.update(status='not_supported_no_independent_generalization',
                   limits='Posterior apex2 seed1 repair now passes joint baseline after policy changes and multiple failures. Original reserved cohort remains3of5jointpasses;seed5 failure remains. Two posterior circuits do not prove independent validation, universal quality, statistical generalization or FPGA acceleration.')
    quality['evidence'].extend(evidence)
    quality['measurements'].update(latest_apex2_private_wirelength=19170,
                                   latest_apex2_private_cpd_ns=10.8308,
                                   latest_apex2_private_crossings=1452)
    matrix['claims'].append({
        'id': 'Q6', 'gates': ['G2', 'G4', 'G8'],
        'claim': 'Posterior apex2 seed1 final route jointly improves original frozen native baseline',
        'status': 'supported_in_declared_scope', 'evidence': evidence,
        'measurements': {'wirelength': 19170, 'baseline_wirelength': 19372,
                         'cpd_ns': 10.8308, 'baseline_cpd_ns': 10.8372,
                         'modeled_crossings': 1452, 'baseline_modeled_crossings': 1581},
        'limits': 'Native legal/capacity pass;two final candidates,chosen shorter. Four audits and final legacy/source-bound reloads pass with3500identicalroundedtimingrows. CPDmargin6.4psnot statisticalsignificance. Evolved posterior policy;not original reserved result,independent full-pipeline repeat,newseedvalidation,physicalSLLorFPGAperformance. Partial earlier5stagecost244.04sexcludesinitialrouting/priorrepairs.',
    })
    out = R / 'work/current_research_claim_matrix_v16_20261020'
    out.mkdir()
    plan = R / 'experiments/research_plan.json'
    (out / 'plan_snapshot.json').write_bytes(plan.read_bytes())
    evidence.extend([str((out / 'plan_snapshot.json').relative_to(R)), str(Path(__file__).resolve().relative_to(R))])
    for name in evidence:
        matrix['source_sha256'][name] = sha(R / name)
    matrix.update(schema='dieroute.claim_matrix.v16', recorded_ns=time.time_ns(),
                  predecessor={'path': str(previous.relative_to(R)), 'sha256': sha(previous)})
    assert len(matrix['gates']) == 8 and all(g['status'] != 'complete' for g in matrix['gates'])
    target = out / 'matrix.json'
    target.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + '\n')
    value = json.loads(plan.read_text())
    value['current_claim_matrix'] = {'path': str(target.relative_to(R)), 'sha256': sha(target),
                                     'status': matrix['status'], 'research_complete': False}
    value['apex2_reverse_sink_refinement']['final_native_recheck_audit'] = evidence[4]
    plan.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'claims': len(matrix['claims']), 'sources': len(matrix['source_sha256']),
                      'open_gates': 8, 'research_complete': False}))


if __name__ == '__main__':
    main()
