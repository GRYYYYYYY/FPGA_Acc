"""Wait for original five-attempt owner, then independently join final evidence."""
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import time
import traceback
from audit_prospective_final_native_identity import verify_quality


def main():
    directory = Path(sys.argv[1]).resolve()
    config = json.loads((directory / 'protocol.json').read_text())
    assert not (directory / 'manifest.json').exists()
    state = {'status': 'waiting_for_original_five_full_attempts', 'pid': os.getpid(), 'research_complete': False}

    def save():
        temp = directory / 'manifest.tmp'
        temp.write_text(json.dumps(state, indent=2) + '\n')
        temp.replace(directory / 'manifest.json')

    refs = {}

    def sha(path):
        path = Path(path).resolve()
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1048576), b''):
                h.update(block)
        refs[str(path)] = h.hexdigest()
        return refs[str(path)]

    def read(path, verify=False):
        sha(path)
        value = json.loads(Path(path).read_text())
        if verify:
            for name, expected in value['source_sha256'].items():
                assert sha(name) == expected, name
        return value

    try:
        for name, expected in config['source_sha256'].items():
            assert sha(name) == expected, name
        save()
        producer = Path(config['producer'])
        while True:
            manifest = json.loads((producer / 'manifest.json').read_text())
            if manifest['status'] == 'five_full_policy_attempts_terminal_require_independent_cohort_review':
                break
            assert manifest['status'] != 'full_repeat_supervisor_stopped_requires_review', manifest.get('error')
            owner = config['owner']
            text = (Path('/proc') / str(owner['pid']) / 'stat').read_text()
            fields = text[text.rfind(')') + 2:].split()
            assert fields[0] != 'Z' and fields[19] == owner['start_ticks']
            time.sleep(10)
        state['status'] = 'reviewing_all_five_full_attempts'
        save()
        protocol = read(producer / 'protocol.json', True)
        manifest = read(producer / 'manifest.json')
        assert protocol['repeats'] == 5 and [v['repeat'] for v in manifest['attempts']] == list(range(5))
        original_case = read(protocol['case_protocol'])['cases'][0]
        reference_parent = Path(original_case['repeat_parent_directory'])
        parent_files = sorted(p.name for p in reference_parent.glob('route.*') if p.name != 'route.json')
        assert parent_files
        reference_metrics = read(reference_parent / 'route.json')
        reference_metrics.pop('wall_ms')
        reference = read(protocol['reference_mode_audit'], True)
        reference_tree_hash = sha(reference['current_state']['tree'])
        rows = []
        for attempt in manifest['attempts']:
            run = producer / ('repeat_' + str(attempt['repeat']))
            row = {'repeat': attempt['repeat'], 'terminal_status': attempt['status'],
                   'joint_quality_pass': False, 'full_attempt_wall_ns': attempt['full_attempt_wall_ns']}
            if attempt['status'] == 'full_policy_attempt_error_retained_no_retry':
                row['classification'] = 'execution_or_audit_error_retained'
                rows.append(row)
                continue
            assert attempt['status'] == 'full_policy_attempt_reviewed'
            assert all(v['returncode'] == 0 for v in attempt['commands'])
            assert sha(run / 'recipe/pair.json') == sha(protocol['parent_recipe'])
            parent = run / 'parent'
            metrics = read(parent / 'route.json')
            metrics.pop('wall_ms')
            row['parent_non_timing_report_identical'] = metrics == reference_metrics
            assert sorted(p.name for p in parent.glob('route.*') if p.name != 'route.json') == parent_files
            row['parent_core_artifacts_identical'] = all(sha(parent / name) == sha(reference_parent / name) for name in parent_files)
            read(parent / 'tree_audit.json', True)
            read(parent / 'session_provenance_audit.json', True)
            read(run / 'initial_review/audit.json', True)
            final = read(attempt['final_report'], True)
            passed = final.get('joint_quality_pass', final.get('final_original_baseline_joint_pass'))
            assert passed is attempt['joint_quality_pass']
            row.update(classification='verified_joint_pass' if passed else 'verified_quality_failure', joint_quality_pass=passed)
            if passed:
                if 'current_state' in final:
                    tree = Path(final['current_state']['tree'])
                    crossings = final['current_state']['model_crossings']
                elif 'final_tree' in final:
                    tree = Path(final['final_tree'])
                    crossings = final['crossings']
                else:
                    leaf = Path(final['selected_native_audit'])
                    tree = leaf.parent / 'candidate/route.route_trees.csv'
                    crossings = read(leaf, True)['model_crossings']
                quality = verify_quality(tree.parent / 'native_validation/validation.json', Path(original_case['native_case']), sha)
                pre = read(run / 'final_capacity/independent_preflight.json', True)
                assert pre['candidate']['overused_resources'] == 0 and pre['candidate']['all_sinks_and_nodes_reachable']
                assert pre['candidate']['layer_transitions'] == crossings <= pre['baseline']['layer_transitions']
                assert quality['total_wirelength'] <= original_case['baseline_wirelength']
                assert quality['critical_path_delay_ns'] <= original_case['baseline_cpd_ns']
                digest = sha(tree)
                assert digest == attempt['final_tree_sha256']
                row.update(final_tree_sha256=digest, same_tree_as_reference=digest == reference_tree_hash,
                           wirelength=quality['total_wirelength'], cpd_ns=quality['critical_path_delay_ns'], crossings=crossings)
            rows.append(row)
        durations = [r['full_attempt_wall_ns'] / 1e9 for r in rows]
        sha(Path(__file__).resolve())
        report = {'status': 'five_full_same_input_policy_attempts_independently_reviewed', 'planned': 5, 'retained': len(rows),
                  'joint_passes': sum(v['joint_quality_pass'] for v in rows),
                  'all_five_exact_parent_and_final_tree_reproductions': all(
                      v['joint_quality_pass'] and v.get('parent_core_artifacts_identical', False)
                      and v.get('parent_non_timing_report_identical', False) and v.get('same_tree_as_reference', False) for v in rows),
                  'full_attempt_seconds': {'min': min(durations), 'median': statistics.median(durations), 'max': max(durations)},
                  'rows': rows, 'source_sha256': refs, 'research_complete': False,
                  'scope': 'Five fresh full-policy attempts on one frozen circuit/seed, including parent, initial repair, native modes and conditional fallback. All attempts retained. Timers include per-attempt verification and exclude baseline/graph preparation; background load uncontrolled. Same-input reproducibility only, not independent seeds/circuits, timing significance, hardware acceleration or closure of all research gates.'}
        with (directory / 'audit.json').open('x') as stream:
            json.dump(report, stream, indent=2)
            stream.write('\n')
        state['status'] = 'five_full_policy_repeat_audit_ready'
        save()
    except BaseException:
        state.update(status='full_repeat_audit_stopped_requires_review', error=traceback.format_exc())
        save()
        raise


if __name__ == '__main__':
    main()
