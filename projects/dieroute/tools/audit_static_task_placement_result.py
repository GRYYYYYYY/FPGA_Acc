"""Close the bounded static observer-placement study using all fifteen actual runs."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('study', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    root, output = a.study.resolve(), a.output.resolve()
    assert not output.exists()
    files = [Path(__file__).resolve()]

    def read(path):
        files.append(path)
        return json.loads(path.read_text())

    def check_hashes(values):
        assert values
        for name, expected in values.items():
            assert sha(name) == expected, name

    protocol = read(root / 'native_protocol_v2.json')
    check_hashes(protocol['source_sha256'])
    producer = read(root / 'native_manifest_v2.json')
    assert producer['status'] == 'fifteen_native_static_placement_runs_and_native_validations_done_independent_replay_pending'
    assert len(producer['steps']) == 21 and all(s['status'] == 'passed' and s['returncode'] == 0 for s in producer['steps'])
    names = {f'mode{mode}_{repeat}' for mode in range(3) for repeat in range(5)}
    for directory, status in [('trace_audit_queue', 'all_fifteen_static_placement_traces_audited'),
                              ('resource_replay_queue', 'all_fifteen_controller_resource_replays_completed')]:
        queue = read(root / directory / 'manifest.json')
        assert queue['status'] == status and set(queue['audited']) == names and len(queue['audited']) == 15
    outcomes, canonical, counters = {}, {}, {}
    for mode in range(3):
        previous = None
        receipts = []
        for repeat in range(5):
            directory = root / 'native_runs_v2' / f'mode{mode}_{repeat}'
            run = read(directory / 'manifest.json')
            assert run['status'] == 'online_router_completed_equivalence_audit_required' and run['returncode'] == 0
            check_hashes(run['source_sha256'])
            report = read(directory / 'route.json')
            assert report['legal'] and report['task_placement_mode'] == mode
            assert report['speculative_workers'] == 2 and report['present_schedule_mode'] == 0 and report['shadow_sync_windows'] == 1
            report.pop('wall_ms')
            artifacts = sorted(p for p in directory.glob('route.*') if p.name != 'route.json')
            hashes = {p.name: sha(p) for p in artifacts}
            files.extend(artifacts)
            if previous is not None:
                assert previous == (report, hashes), ('repeat mismatch', mode, repeat)
            previous = (report, hashes)
            trace = read(directory / 'placement_trace_audit.json')
            assert trace['status'] == 'static_task_placement_receipts_bound_to_tasks_and_ordered_transactions'
            assert trace['placement_mode'] == mode
            check_hashes(trace['source_sha256'])
            state = read(directory / 'controller_resource_replay_audit.json')
            assert state['status'] == 'controller_resource_versions_epochs_and_final_bytes_replayed'
            check_hashes(state['result']['source_sha256'])
            assert state['result']['final_resources_and_costs_byte_equivalent'] and state['result']['cpu_legal']
            receipts.append({k: trace[k] for k in ['receipts', 'transactions', 'moved_task_occurrences', 'logical_moved_envelope_bytes']})
        assert all(row == receipts[0] for row in receipts)
        canonical[mode] = {k: v for k, v in hashes.items() if k != 'route.task_migration.csv'}
        counters[mode] = report
        validation = read(root / 'native_runs_v2' / f'mode{mode}_0/native_validation/validation.json')
        assert validation['legal'] and validation['vpr_exit_status'] == 0
        base = root / 'native_runs_v2' / f'mode{mode}_0'
        stdout, stderr = [base / 'native_validation' / name for name in ['vpr_analysis.stdout', 'vpr_analysis.stderr']]
        files.extend([base / 'native.route', stdout, stderr])
        assert sha(stdout) == validation['stdout_sha256'] and sha(stderr) == validation['stderr_sha256']
        assert sha(base / 'native.route') == validation['inputs']['route_sha256']
        checks = dict(native_legal=True,
            wirelength_nondegrade=validation['total_wirelength'] <= validation['baseline_wirelength'],
            cpd_nondegrade=validation['critical_path_delay_ns'] <= validation['baseline_cpd_ns'])
        outcomes[str(mode)] = dict(repeats=5, receipts_per_repeat=receipts[0],
            native_qor={k: validation[k] for k in ['total_wirelength', 'critical_path_delay_ns', 'baseline_wirelength', 'baseline_cpd_ns', 'wirelength_delta_percent', 'cpd_delta_percent']},
            remote_shadow_read_entries=report['remote_shadow_reads'], checks=checks,
            joint_native_quality_pass=all(checks.values()))
    assert canonical[0] == canonical[1] == canonical[2]
    normalized = [{k: v for k, v in counters[mode].items() if k not in ['task_placement_mode', 'remote_shadow_reads']} for mode in range(3)]
    assert normalized[0] == normalized[1] == normalized[2]
    assert counters[0]['remote_shadow_reads'] == counters[1]['remote_shadow_reads']
    assert all(outcomes[str(mode)]['native_qor'] == outcomes['0']['native_qor'] for mode in range(3))
    result = dict(status='fifteen_static_observer_placement_runs_and_native_quality_audited',
        outcomes=outcomes, identical_core_artifacts=True, per_run_core_artifact_count=len(canonical[0]),
        counter_difference_fields=['task_placement_mode', 'remote_shadow_reads'],
        remote_read_entry_reduction_percent=100 * (1 - counters[2]['remote_shadow_reads'] / counters[0]['remote_shadow_reads']),
        source_sha256={str(path): sha(path) for path in files},
        scope='Static CPU observer placement on ex5p, two workers, sync1, preset0. All15 actual runs '
              'deterministic, exact controller resource/version replay and placement receipts verified; '
              'all three final routes native-legal with identical quality, failing the strong WL/CPD gate. '
              'Reduced remote-labelled shadow read journal entries are not physical traffic or speedup. '
              'Seed-content/shadow-read independent oracle, adaptive migration, sustained bounded queues, '
              'hardware protocol and broader quality remain open.',
        adopted=False, board_result=False, research_complete=False)
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['source_sha256', 'outcomes']}))


if __name__ == '__main__':
    main()
