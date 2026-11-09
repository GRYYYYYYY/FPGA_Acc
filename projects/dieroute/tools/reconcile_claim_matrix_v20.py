"""Reconcile completed topology, phase, queue integration and HLS evidence."""
import hashlib
import json
import time
from pathlib import Path

R = Path(__file__).resolve().parents[1]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def main():
    previous = R / 'work/current_research_claim_matrix_v19_20261020/matrix.json'
    matrix = json.loads(previous.read_text())
    for name, expected in matrix['source_sha256'].items():
        assert sha(R / name) == expected, name
    specs = [
        ('Q10', ['G3', 'G4', 'G5'],
         'Current hierarchical routing reduces model crossings in all six topology pairs but jointly passes flat controls in only two',
         ['work/current_layer_capacity_pair_audit_v2_20261020/comparison_summary.json'],
         'One ex5p seed, six 2/3/4-layer and channel-width pairs. All twelve valid runs legal; six invalid startup attempts retained separately. Per-layer grid constant, total graph grows. No strong scaling, universal quality or physical SLL claim.'),
        ('P3', ['G2', 'G6', 'G7'],
         'Exact phase profiling locates most executor CPU cost in both planning estimators',
         ['work/remaining_tail_phase_profile_20261020/phase_profile_audit.json'],
         'One apex2 seed6 instrumented CPU parent, exact native output equality. Forward and remaining-layer tail sum to about 87.1% of executor thread CPU. Timer overhead remains. Not whole refinement, general workload or measured device acceleration.'),
        ('R2', ['G2', 'G6'],
         'Both actual RRBackend estimator loops preserve full seed6 native parent outputs after callback and bounded frontier adaptation',
         ['work/bounded_frontier_rr_variant_20261020/native_equivalence_v2/native_equivalence_audit.json',
          'work/batched_estimators_rr_variant_20261020/differential_audit.json',
          'work/batched_estimators_rr_variant_20261020/native_equivalence_audit.json'],
         'Forty core route artifacts and non-timing reports identical for each complete parent. 2400 small graph differential comparisons include resource journals and work. CPU storage grows, finite queue cap can fail other inputs. Observed single timings do not show a speedup. Not resident-device integration or five full policy repeats.'),
        ('H3', ['G6', 'G7'],
         'Insert-lookup boundary implementation fails requested 300MHz setup timing despite complete routing',
         ['work/insert_lookup_boundary_routed_review_20261020/independent_audit.json'],
         'Retained requested-clock DCP has WNS -1.218ns; hold, pulse and routing checks pass. Final adjusted-clock bitstream constraint correspondence unproven. No board performance or clock closure.'),
        ('H4', ['G6'],
         'Both resident direct-array estimators generate RTL in HLS but RTL equivalence remains unproven',
         ['work/resident_upstream_HLS_v3_20261020/HLS_review.json',
          'work/resident_upstream_HLS_v3_20261020/pipeline_bottleneck_review.json',
          'work/resident_tail_HLS_v3_20261020/HLS_review.json',
          'work/resident_upstream_flat_differential_20261020/audit.json',
          'work/resident_tail_flat_differential_20261020/audit.json',
          'work/resident_upstream_HLS_v4_20261020/failure_review.json'],
         'Forward 3000 and reverse 2000 CPU snapshot comparisons; separate 200000 exact RR cost checks. Source pointer-object and control-bundle synthesis failures retained. Both flat operators synthesize, but cosim C-vector generation fails before RTL execution. External heap loop II up to 216 cycles; no representative throughput, integrated XO, routed clock or board result. Aligned wire-type experiment pending and excluded from supported results.'),
    ]
    evidence = []
    values = {}
    for _, _, _, names, _ in specs:
        for name in names:
            if name in values:
                continue
            value = json.loads((R / name).read_text())
            for source, digest in value.get('source_sha256', {}).items():
                source_path = Path(source)
                if not source_path.is_absolute():
                    source_path = R / source_path
                assert sha(source_path) == digest, str(source_path)
            values[name] = value
            evidence.append(name)
    topology = values[specs[0][3][0]]
    assert topology['native_legal'] == topology['algorithm_cells'] == 12
    assert topology['hierarchical_joint_vs_flat'] == 2
    native = values[specs[2][3][-1]]
    assert len(native['core_artifacts']) == 40
    assert native['status'] == 'candidate_full_native_parent_exact_core_equivalence_verified'
    timing = values[specs[3][3][0]]
    assert timing['design_timing_summary']['wns_ns'] == -1.218
    for ident, gates, claim, names, limits in specs:
        assert all(c['id'] != ident for c in matrix['claims'])
        matrix['claims'].append(dict(id=ident, gates=gates, claim=claim,
                                    status='supported_in_declared_scope', evidence=names,
                                    limits=limits))
    out = R / 'work/current_research_claim_matrix_v20_20261020'
    out.mkdir()
    plan_path = R / 'experiments/research_plan.json'
    (out / 'plan_snapshot.json').write_bytes(plan_path.read_bytes())
    evidence += [str((out / 'plan_snapshot.json').relative_to(R)),
                 str(Path(__file__).resolve().relative_to(R))]
    for name in evidence:
        matrix['source_sha256'][name] = sha(R / name)
    matrix.update(schema='dieroute.claim_matrix.v20', recorded_ns=time.time_ns(),
                  predecessor={'path': str(previous.relative_to(R)), 'sha256': sha(previous)})
    assert len(matrix['gates']) == 8 and all(g['status'] != 'complete' for g in matrix['gates'])
    target = out / 'matrix.json'
    target.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + '\n')
    plan = json.loads(plan_path.read_text())
    plan['current_claim_matrix'] = dict(path=str(target.relative_to(R)), sha256=sha(target),
                                      status=matrix['status'], research_complete=False)
    plan['resident_estimator_development'] = {
        'full_cpu_parent_equivalence': specs[2][3][-1],
        'upstream_synthesis_review': specs[4][3][0],
        'reverse_synthesis_review': specs[4][3][2],
        'RTL_equivalence': 'unproven_C_vector_generation_failures_retained',
        'pending_alignment_experiment': 'work/resident_upstream_HLS_v5_20261020/protocol.json',
        'research_complete': False}
    temporary = plan_path.with_suffix('.matrix20.tmp')
    temporary.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(plan_path)
    print(json.dumps(dict(claims=len(matrix['claims']), sources=len(matrix['source_sha256']), open_gates=8)))


if __name__ == '__main__':
    main()
