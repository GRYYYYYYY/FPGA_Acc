"""Record four-layer tool compatibility and the audited private timing step."""
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
    previous = R / 'work/current_research_claim_matrix_v14_20261020/matrix.json'
    matrix = json.loads(previous.read_text())
    for name, expected in matrix['source_sha256'].items():
        assert sha(R / name) == expected, name
    added = [
        'work/vpr_four_layer_compatibility_closure_v2_queue_20261020/closure_audit.json',
        'work/vpr_source_bound_four_layer_build_20261020/independent_layer_delta_audit.json',
        'work/vpr_source_bound_four_layer_build_20261020/build_dependency_audit.json',
        'work/source_bound_route_compatibility_20261020/failure_review.json',
        'work/vpr_source_bound_four_layer_postbuild_20261020/prepare_compatibility.log',
        'work/apex2_seed1_stage4_blockers_first_rounded_exchange_20261020/native_queue/task591_500_first/independent_native_audit.json',
        'work/apex2_seed1_stage4_blockers_first_rounded_exchange_20261020/construction_review.json',
        'work/apex2_seed1_stage4_blockers_first_rounded_exchange_20261020/private_acceptance_review.json',
        'work/apex2_seed1_stage4_blockers_first_exchange_20261020/terminal_review.json',
    ]
    closure = json.loads((R / added[0]).read_text())
    assert closure['status'] == 'source_delta_and_observed_four_route_compatibility_verified'
    assert len(closure['observations']) == 2
    candidate = json.loads((R / added[5]).read_text())
    assert candidate['checks']['native_legal'] and not candidate['checks']['CPD']
    assert candidate['cpd_ns'] == 11.0252
    matrix['claims'].append({
        'id': 'C1', 'gates': ['G1', 'G4', 'G8'],
        'claim': 'Four-layer source-bound VPR preserves observed baseline and candidate native outputs on two circuits',
        'status': 'supported_in_declared_scope', 'evidence': added[:5],
        'limits': 'Exactly one header bound 2 to 4; source and build dependency audits passed. Four frozen routes only: native metrics and rounded timing CSV bytes identical. Initial layer assertion and preparation filename failure retained. No historical legacy binary source identity or universal equivalence.',
    })
    quality = next(c for c in matrix['claims'] if c['id'] == 'Q5')
    quality['evidence'].extend(added[5:])
    quality['measurements'].update(latest_apex2_private_wirelength=18423,
                                   latest_apex2_private_cpd_ns=11.0252,
                                   latest_apex2_private_crossings=1489)
    quality['limits'] += ' Later blocker-first rounded-budget candidate improves private CPD by15.7ps; original10.8372ns baseline still fails. Three orders deduplicate to one tree; not independent trials.'
    out = R / 'work/current_research_claim_matrix_v15_20261020'
    out.mkdir()
    plan = R / 'experiments/research_plan.json'
    (out / 'plan_snapshot.json').write_bytes(plan.read_bytes())
    added.extend([str((out / 'plan_snapshot.json').relative_to(R)),
                  str(Path(__file__).resolve().relative_to(R))])
    for name in added:
        matrix['source_sha256'][name] = sha(R / name)
    matrix.update(schema='dieroute.claim_matrix.v15', recorded_ns=time.time_ns(),
                  predecessor={'path': str(previous.relative_to(R)), 'sha256': sha(previous)})
    assert len(matrix['gates']) == 8 and all(g['status'] != 'complete' for g in matrix['gates'])
    target = out / 'matrix.json'
    target.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + '\n')
    value = json.loads(plan.read_text())
    value['current_claim_matrix'] = {'path': str(target.relative_to(R)), 'sha256': sha(target),
                                     'status': matrix['status'], 'research_complete': False}
    plan.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'claims': len(matrix['claims']), 'sources': len(matrix['source_sha256']),
                      'open_gates': 8, 'research_complete': False}))


if __name__ == '__main__':
    main()
