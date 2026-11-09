"""External, bounded final admission; never launches or recovers experiment stages."""
import argparse
import datetime
import json
import resource
import time
from pathlib import Path

from archive_design_exposure_v3 import sha

R = Path(__file__).resolve().parents[1]
PHYSICAL = 'all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'
EVENT_FLAGS = (
    'independent_owner_sets_scaled_polynomial',
    'complete_prospective_overflow_guard_rejected_candidate_and_unchanged_epoch_pass',
    'complete_same_snapshot_objective_guard_and_retained_state_pass',
    'complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass',
    'complete_fallback_attempt_membership_actual_old_objective_and_budget_checks_pass',
    'complete_present_snapshot_owner_exclusion_and_union_objective_pass',
    'complete_frozen_perpin_raw_plus_max_user_unique_node_objective_pass',
    'complete_structural_node_cost_original_XML_and_float32_bits_rebuild_pass',
)


def load(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('factor', type=int, choices=(1, 2, 4))
    args = parser.parse_args()
    free = int(Path('/sys/fs/cgroup/memory.max').read_text()) - int(Path('/sys/fs/cgroup/memory.current').read_text())
    limit = 512 * 2**20
    # Conservative reservation even if a subsequent queue-owned model has launched.
    # This verifier never changes that queue or claims reserved resources from it.
    assert free >= limit + 8 * 2**30, 'Final metadata verifier deferred by memory gate'
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    tick = time.perf_counter()
    case = R / f'experiments/titan23_neuron_scaled_present_factor{args.factor}_pipeline_v1_2026-10-15'
    reference = R / 'experiments/titan23_neuron_compiled_criticality_pipeline_v1_2026-10-15'
    target = case / 'independent_final_admission_v1.json'
    assert not target.exists(), 'Final record already exists; no overwrite'
    bindings = {}

    def bind(path):
        digest = sha(path)
        assert str(path) not in bindings or bindings[str(path)] == digest
        bindings[str(path)] = digest
        return load(path)

    def merge(mapping):
        for path, digest in mapping.items():
            assert path not in bindings or bindings[path] == digest
            bindings[path] = digest

    protocol = bind(case / 'protocol.json')
    assert (protocol['original_nodes'], protocol['original_edges'], protocol['connections'],
            protocol['nets'], protocol['rounds'], protocol['present_factor']) == (
                3593250, 39165143, 77106, 50767, 2, args.factor)
    assert protocol['heldout'] is False and protocol['native_route_labels_used_by_model'] is False
    merge(protocol['bindings'])
    pipeline = bind(case / 'pipeline_terminal.json')
    assert pipeline['exit_status'] == 0 and pipeline['all_stages_completed'] is True
    stages = {}
    for name in ('model', 'initial_audit', 'sketch_audit', 'event_audit'):
        terminal = bind(case / (name + '_terminal.json'))
        process = bind(case / (name + '_process.json'))
        expected = (20 if name == 'model' else 8) * 2**30
        assert type(terminal['exit_status']) is int and terminal['exit_status'] == 0
        assert terminal['address_space_limit_bytes'] == process['address_space_limit_bytes'] == expected
        admissions = []
        for path in sorted(case.glob(name + '_admission_*.json')):
            admission = bind(path)
            if admission['admitted'] is not True:
                continue
            assert admission['child_limit_bytes'] == expected
            assert admission['margin_bytes'] == 8 * 2**30
            assert admission['shared_memory_max_bytes'] - admission['shared_memory_current_bytes'] >= expected + 8 * 2**30
            admissions.append(str(path))
        assert len(admissions) == 1, ('ambiguous successful stage admission', name)
        stages[name] = dict(terminal=terminal, successful_admission=admissions[0])
    initial = bind(case / 'model/initial_physical_verification.json')
    sketch = bind(case / 'model/sketch_physical_verification.json')
    events = bind(case / 'model/verification.json')
    for proof in (initial, sketch, events):
        assert proof[PHYSICAL] is True and proof['completed'] == 77106
        merge(proof['bindings'])
    assert events['present_factor'] == args.factor and events['events'] == 101534
    assert all(events[key] is True for key in EVENT_FLAGS)
    assert events['committed'] + events['retained'] == 101534
    assert sketch['overflow_units'] == events['overflow_units']
    baseline = bind(reference / 'model/protocol.json')
    current = bind(case / 'model/protocol.json')
    assert current['present_factor'] == args.factor
    assert {k: v for k, v in baseline.items() if k not in ('bindings', 'present_cost_policy')} == {
        k: v for k, v in current.items() if k not in ('bindings', 'present_cost_policy', 'present_factor')}
    names = ('initial.json', 'floors.json', 'round0.json', 'round1.json', 'sketch.json')
    for name in names:
        candidate, original = case / 'model' / name, reference / 'model' / name
        bindings[str(candidate)] = sha(candidate)
        if args.factor == 1 or name in ('initial.json', 'floors.json'):
            bindings[str(original)] = sha(original)
            assert bindings[str(candidate)] == bindings[str(original)]
    if args.factor == 1:
        parity = bind(case / 'exact_reference_parity.json')
        assert parity['all_complete_frames_byte_equal'] is True
        assert parity['all_events_and_round_metadata_equal'] is True
        assert len(parity['complete_round_event_digests']) == 2
        assert all(row['round_index'] == i and row['event_count'] == 50767
                   for i, row in enumerate(parity['complete_round_event_digests']))
        streaming = bind(case / 'closed_all_events_stream_parity_v1.json')
        assert streaming['all_events_and_round_metadata_equal'] is True and streaming['events'] == 101534
        merge(streaming['bindings'])
    development = bind(case / 'development_admission.json')
    assert development['all_stages_completed'] is True
    assert development['present_factor'] == args.factor
    assert development['full_original_connections'] == 77106
    assert development['final_overflow'] == events['overflow_units']
    assert development['quality_improvement_proven'] is False and development['promoted'] is False
    bindings[str(Path(__file__))] = sha(__file__)
    bindings[str(R / 'tools/archive_design_exposure_v3.py')] = sha(R / 'tools/archive_design_exposure_v3.py')
    for path, digest in bindings.items():
        assert sha(path) == digest, ('binding drift', path)
    value = dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 bindings=bindings, all_pass=True, present_factor=args.factor,
                 all_original_connections=77106, all_events=101534,
                 all_three_independent_audits_pass=True,
                 scientific_protocol_unchanged_except_registered_factor=True,
                 factor1_complete_state_and_event_parity=(args.factor == 1),
                 stage_resources_and_terminals=stages,
                 overflow_units=events['overflow_units'],
                 verifier_address_space_limit_bytes=limit,
                 shared_headroom_before_bytes=free,
                 seconds=time.perf_counter() - tick,
                 paired_performance_improvement_proven=False,
                 quality_improvement_proven=False, promoted=False,
                 scope='Complete frozen development-software admission. Factor1 parity additionally checked against closed full-state and independently streamed events. Historical stage resource records are checked; live kernel evidence is separate. No heldout-family, improved quality, native QoR, workflow gain or hardware claim.')
    with target.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: value[k] for k in ('all_pass', 'present_factor', 'all_original_connections',
                                         'all_events', 'overflow_units', 'seconds')}))


if __name__ == '__main__':
    main()
