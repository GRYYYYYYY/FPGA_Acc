"""Run unchanged frozen sweep/refresh functions after each parent review."""
from pathlib import Path
import hashlib
import json
import os
import sys
import time
import traceback
import run_native_joint_budget_repeat_stage as sweep
import run_native_refreshed_critical_policy_v1 as refresh
from shared_tree_budget_repair_implicit import repair as implicit_repair

sweep.repair = implicit_repair
refresh.repair = implicit_repair


def main():
    directory = Path(sys.argv[1]).resolve()
    protocol = json.loads((directory / 'protocol.json').read_text())
    assert not (directory / 'manifest.json').exists(), 'No implicit replay'
    state = {'status': 'checking_frozen_sources', 'pid': os.getpid(), 'cases': [],
             'research_complete': False, 'adopted': False}

    def sha(path):
        digest = hashlib.sha256()
        with Path(path).open('rb') as stream:
            for block in iter(lambda: stream.read(1048576), b''):
                digest.update(block)
        return digest.hexdigest()

    def save():
        temp = directory / 'manifest.tmp'
        temp.write_text(json.dumps(state, indent=2) + '\n')
        temp.replace(directory / 'manifest.json')

    def read_reviews():
        try:
            return json.loads(Path(protocol['review_manifest']).read_text())
        except (OSError, json.JSONDecodeError):
            return {}

    def live():
        owner = protocol['review_owner']
        path = Path('/proc') / str(owner['pid']) / 'stat'
        if not path.exists():
            return False
        text = path.read_text()
        fields = text[text.rfind(')') + 2:].split()
        return fields[0] != 'Z' and fields[19] == owner['start_ticks']

    try:
        for path, expected in protocol['source_sha256'].items():
            assert sha(path) == expected, path
        reference = json.loads(Path(protocol['frozen_parameter_source']).read_text())
        for path, expected in reference['source_sha256'].items():
            assert sha(path) == expected, path
        state['frozen_reference_files_verified'] = len(reference['source_sha256'])
        save()
        for case in protocol['cases']:
            label = case['label']
            state.update(status='waiting_for_reviewed_parent', active_case=label)
            save()
            while True:
                reviews = read_reviews()
                reviewed = next((v for v in reviews.get('cases', []) if v['label'] == label), None)
                if reviewed and reviewed.get('status') in [
                    'parent_tree_provenance_writeback_native_validation_terminal',
                    'parent_failed_no_review_or_resampling', 'parent_review_failed_outcome_retained']:
                    break
                assert reviews.get('status') != 'parent_review_queue_stopped_requires_review', reviews.get('error')
                assert live(), 'Original review owner missing; reconcile without restart'
                time.sleep(10)
            row = {'label': label, 'stages': [], 'parent_review_status': reviewed['status']}
            state['cases'].append(row)
            if not reviewed.get('native_legal', False):
                row['status'] = 'parent_failure_retained_no_refinement'
                save()
                continue
            output = directory / label
            output.mkdir()
            parent = Path(case['repeat_parent_directory'])
            metrics = json.loads((parent / 'route.json').read_text())
            iterations = metrics['iterations']
            assert iterations >= reference['minimum_prior_timing_iterations']
            if iterations + 1 > reference['maximum_total_routing_sweeps']:
                row.update(status='frozen_initial_sweep_budget_exhausted', parent_iterations=iterations)
                save()
                continue
            case_protocol = {k: v for k, v in reference.items() if k != 'source_sha256'}
            case_protocol.update(cases=[case], vpr=protocol['validation_vpr'],
                                 parent_iteration_accounting={label: {'routing_iterations': iterations, 'additional_sweeps': 1}},
                                 scope='Prospective fixed initial sweep/refresh only; no algorithm changes or board claim.')
            files = [Path(protocol['frozen_parameter_source']), Path(__file__).resolve(),
                     parent / 'tree_audit.json', parent / 'session_provenance_audit.json',
                     parent / 'native_validation/validation.json', parent / 'route.route_trees.csv', parent / 'native.route']
            files.extend(Path(value) for value in [case_protocol['writer'], case_protocol['validator'], case_protocol['vpr']])
            case_protocol['source_sha256'] = {str(path): sha(path) for path in files}
            (output / 'protocol.json').write_text(json.dumps(case_protocol, indent=2) + '\n')
            case_start = time.monotonic_ns()
            results = []
            try:
                for name, module in [('sweep', sweep), ('refresh', refresh)]:
                    module.P = output / name
                    module.P.mkdir()
                    if name == 'refresh':
                        case['policy_parent_tree'] = results[0]['current_tree']
                    stage = {'stage': name, 'status': 'running'}
                    row['stages'].append(stage)
                    state['status'] = 'running_frozen_initial_refinement'
                    save()
                    start = time.monotonic_ns()
                    result = module.run_case(case, case_protocol)
                    results.append(result)
                    stage.update(status='terminal', wall_ns=time.monotonic_ns() - start,
                                 quality=result['current_quality'], final_tree=result['current_tree'])
                    save()
                row.update(status='initial_sweep_refresh_terminal_requires_independent_review',
                           final_tree=results[-1]['current_tree'], quality=results[-1]['current_quality'],
                           crossings=results[-1]['final_crossings'], wall_ns=time.monotonic_ns() - case_start)
            except Exception:
                row.update(status='initial_refinement_error_retained_no_replay',
                           wall_ns=time.monotonic_ns() - case_start, error=traceback.format_exc())
            save()
        state['status'] = 'five_prospective_initial_refinement_attempts_terminal_requires_review'
        save()
    except BaseException:
        state.update(status='initial_refinement_queue_stopped_requires_review', error=traceback.format_exc())
        save()
        raise


if __name__ == '__main__':
    main()
