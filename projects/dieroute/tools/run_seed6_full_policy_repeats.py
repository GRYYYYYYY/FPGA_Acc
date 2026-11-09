"""Five fresh same-input full-policy attempts; retain every failed attempt."""
import contextlib
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import run_native_joint_budget_repeat_stage as sweep
import run_native_refreshed_critical_policy_v1 as refresh
from shared_tree_budget_repair_implicit import repair
from audit_prospective_final_native_identity import verify_quality
import audit_private_tree_capacity as capacity

sweep.repair = repair
refresh.repair = repair


def main():
    directory = Path(sys.argv[1]).resolve()
    protocol = json.loads((directory / 'protocol.json').read_text())
    root = Path(protocol['root'])
    assert protocol['repeats'] == 5
    assert not (directory / 'manifest.json').exists(), 'No replay'
    state = {'status': 'starting_five_full_policy_repeats', 'pid': os.getpid(), 'attempts': [], 'research_complete': False}

    def sha(path):
        h = hashlib.sha256()
        with Path(path).open('rb') as stream:
            for block in iter(lambda: stream.read(1048576), b''):
                h.update(block)
        return h.hexdigest()

    def write(path, value):
        with path.open('x') as stream:
            json.dump(value, stream, indent=2)
            stream.write('\n')

    def save():
        temporary = directory / 'manifest.tmp'
        temporary.write_text(json.dumps(state, indent=2) + '\n')
        temporary.replace(directory / 'manifest.json')

    def verify(document):
        for name, expected in document['source_sha256'].items():
            assert sha(name) == expected, name

    def command(args, log, attempt, receipt=None):
        started = time.monotonic_ns()
        with log.open('x') as stream:
            child = subprocess.Popen(args, cwd=root, stdout=stream, stderr=subprocess.STDOUT)
            attempt['active_child_pid'] = child.pid
            if receipt is not None:
                stat = (Path('/proc') / str(child.pid) / 'stat').read_text()
                fields = stat[stat.rfind(')') + 2:].split()
                write(receipt, {'status': 'contemporaneous_subprocess_launch', 'pid': child.pid,
                                'start_ticks': fields[19], 'observed_ns': time.time_ns(), 'command': args,
                                'protocol_sha256': sha(receipt.parent / 'protocol.json')})
            save()
            code = child.wait()
        attempt['commands'].append({'command': args, 'returncode': code, 'wall_ns': time.monotonic_ns() - started})
        save()
        assert code == 0, (args, code)

    try:
        verify(protocol)
        parameter_source = json.loads(Path(protocol['parameter_source']).read_text())
        verify(parameter_source)
        original_case = json.loads(Path(protocol['case_protocol']).read_text())['cases'][0]
        parent_reviews = json.loads(Path(protocol['parent_review_protocol']).read_text())
        original_review, = [v for v in parent_reviews['cases'] if v['label'] == 'apex2_seed6']
        old_recipe = Path(protocol['parent_recipe'])
        old_parent = original_case['repeat_parent_directory']
        reference = json.loads(Path(protocol['reference_mode_audit']).read_text())
        assert reference['final_original_baseline_joint_pass']
        reference_tree_hash = sha(reference['current_state']['tree'])
        save()
        for repeat in range(5):
            started = time.monotonic_ns()
            run = directory / ('repeat_' + str(repeat))
            run.mkdir()
            attempt = {'repeat': repeat, 'label': 'apex2_seed6', 'status': 'fresh_parent_running', 'commands': []}
            state['attempts'].append(attempt)
            state.update(status='executing_fresh_full_policy_attempt', active_repeat=repeat)
            save()
            try:
                verify(protocol)
                recipe = run / 'recipe'
                recipe.mkdir()
                (recipe / 'source').symlink_to((old_recipe.parent / 'source').resolve(), target_is_directory=True)
                (recipe / 'input.tasks').symlink_to((old_recipe.parent / 'input.tasks').resolve())
                (recipe / 'pair.json').write_bytes(old_recipe.read_bytes())
                parent = run / 'parent'
                command([sys.executable, protocol['parent_runner'], str(recipe / 'pair.json'),
                         protocol['timing_build'], str(parent)], run / 'parent.log', attempt)
                attempt['status'] = 'parent_native_review'
                save()
                for i, item in enumerate(original_review['steps']):
                    args = [v.replace(old_parent, str(parent)).replace(str(old_recipe), str(recipe / 'pair.json'))
                            for v in item['command']]
                    command(args, run / ('parent_review_' + str(i) + '.log'), attempt)
                parent_quality = json.loads((parent / 'native_validation/validation.json').read_text())
                assert parent_quality['legal']
                metrics = json.loads((parent / 'route.json').read_text())
                iterations = metrics['iterations']
                assert iterations >= parameter_source['minimum_prior_timing_iterations']
                assert iterations + 1 <= parameter_source['maximum_total_routing_sweeps']
                case = copy.deepcopy(original_case)
                case['repeat_parent_directory'] = str(parent)
                producer = run / 'initial'
                producer.mkdir()
                output = producer / 'apex2_seed6'
                output.mkdir()
                cp = {k: copy.deepcopy(v) for k, v in parameter_source.items() if k != 'source_sha256'}
                cp.update(cases=[case], vpr=protocol['validation_vpr'],
                          parent_iteration_accounting={'apex2_seed6': {'routing_iterations': iterations, 'additional_sweeps': 1}},
                          scope='One same-input full-policy repeat; not an independent seed or circuit.')
                bound = [Path(protocol['parameter_source']), Path(__file__).resolve(),
                         parent / 'tree_audit.json', parent / 'session_provenance_audit.json',
                         parent / 'native_validation/validation.json', parent / 'route.route_trees.csv', parent / 'native.route',
                         *[Path(cp[k]) for k in ['writer', 'validator', 'vpr']]]
                cp['source_sha256'] = {str(p): sha(p) for p in bound}
                write(output / 'protocol.json', cp)
                row = {'label': 'apex2_seed6', 'stages': []}
                initial_started = time.monotonic_ns()
                results = []
                for name, module in [('sweep', sweep), ('refresh', refresh)]:
                    attempt['status'] = 'initial_' + name
                    save()
                    module.P = output / name
                    module.P.mkdir()
                    if name == 'refresh':
                        case['policy_parent_tree'] = results[0]['current_tree']
                    stage_started = time.monotonic_ns()
                    with (run / (name + '.log')).open('x') as stream, contextlib.redirect_stdout(stream):
                        result = module.run_case(case, cp)
                    results.append(result)
                    row['stages'].append({'stage': name, 'status': 'terminal',
                                          'wall_ns': time.monotonic_ns() - stage_started,
                                          'quality': result['current_quality'], 'final_tree': result['current_tree']})
                row.update(status='initial_sweep_refresh_terminal_requires_independent_review',
                           final_tree=results[-1]['current_tree'], quality=results[-1]['current_quality'],
                           crossings=results[-1]['final_crossings'], wall_ns=time.monotonic_ns() - initial_started)
                write(producer / 'manifest.json', {'status': 'one_repeat_initial_stages_terminal', 'cases': [row]})
                command([sys.executable, str(root / 'tools/audit_prospective_initial_case.py'), str(producer),
                         'apex2_seed6', str(run / 'initial_review')], run / 'initial_audit.log', attempt)
                initial_report = run / 'initial_review/audit.json'
                initial = json.loads(initial_report.read_text())
                final_report = initial_report if initial['joint_quality_pass'] else None
                prior = None
                if final_report is None:
                    for mode in ['wirelength', 'delay']:
                        attempt['status'] = 'native_mode_' + mode
                        save()
                        mode_dir = run / mode
                        args = [sys.executable, protocol['mode_preparer'], protocol['baselines'], protocol['roundtrip'],
                                protocol['costs'], str(output / 'protocol.json'), str(initial_report), mode, str(mode_dir)]
                        if prior is not None:
                            args += ['--prior-mode', str(prior)]
                        command(args, run / (mode + '_prepare.log'), attempt)
                        command([sys.executable, protocol['mode_actor'], str(mode_dir)],
                                run / (mode + '_actor.log'), attempt, receipt=mode_dir / 'launch_receipt.json')
                        terminal = json.loads((mode_dir / 'manifest.json').read_text())['status']
                        assert terminal in ['experiment_terminal_original_baseline_joint_quality_pass',
                                            'experiment_terminal_all_selected_tasks_exhausted',
                                            'experiment_terminal_frozen_stage_budget_exhausted',
                                            'experiment_terminal_no_selected_regression']
                        command([sys.executable, protocol['mode_auditor'], str(mode_dir)], run / (mode + '_audit.log'), attempt)
                        mode_report = mode_dir / 'mode_audit.json'
                        reviewed = json.loads(mode_report.read_text())
                        if reviewed['final_original_baseline_joint_pass']:
                            final_report = mode_report
                            break
                        prior = mode_dir
                if final_report is None:
                    attempt['status'] = 'capacity_fallback'
                    save()
                    fallback = run / 'capacity_fallback'
                    command([sys.executable, protocol['fallback_runner'], str(prior), str(fallback), '--run'],
                            run / 'capacity_fallback.log', attempt)
                    command([sys.executable, protocol['fallback_auditor'], str(fallback)], run / 'fallback_audit.log', attempt)
                    final_report = fallback / 'fallback_audit.json'
                final = json.loads(final_report.read_text())
                passed = final.get('joint_quality_pass', final.get('final_original_baseline_joint_pass'))
                attempt.update(status='full_policy_attempt_reviewed', joint_quality_pass=passed, final_report=str(final_report))
                if passed:
                    if 'current_state' in final:
                        final_tree = Path(final['current_state']['tree'])
                        crossings = final['current_state']['model_crossings']
                    elif 'final_tree' in final:
                        final_tree = Path(final['final_tree'])
                        crossings = final['crossings']
                    else:
                        leaf = Path(final['selected_native_audit'])
                        final_tree = leaf.parent / 'candidate/route.route_trees.csv'
                        crossings = json.loads(leaf.read_text())['model_crossings']
                    quality = verify_quality(final_tree.parent / 'native_validation/validation.json', Path(case['native_case']), sha)
                    pre = run / 'final_capacity'
                    pre.mkdir()
                    write(pre / 'protocol.json', {'candidate_tree': str(final_tree), 'baseline_tree': case['native_tree'],
                                                  'connections': case['connections'], 'resources': case['input_prefix'] + '.resources',
                                                  'node_die': case['topology_prefix'] + '.node_die'})
                    with (run / 'final_capacity.log').open('x') as stream, contextlib.redirect_stdout(stream):
                        capacity.main(pre)
                    capacity_report = json.loads((pre / 'independent_preflight.json').read_text())
                    assert capacity_report['candidate']['overused_resources'] == 0
                    assert quality['total_wirelength'] <= case['baseline_wirelength'] and quality['critical_path_delay_ns'] <= case['baseline_cpd_ns']
                    attempt.update(final_tree_sha256=sha(final_tree), same_tree_as_reference=(sha(final_tree) == reference_tree_hash),
                                   wirelength=quality['total_wirelength'], cpd_ns=quality['critical_path_delay_ns'], model_crossings=crossings)
            except Exception:
                attempt.update(status='full_policy_attempt_error_retained_no_retry', joint_quality_pass=False,
                               error=traceback.format_exc())
            attempt['full_attempt_wall_ns'] = time.monotonic_ns() - started
            save()
        verify(protocol)
        state.update(status='five_full_policy_attempts_terminal_require_independent_cohort_review',
                     joint_passes=sum(v.get('joint_quality_pass', False) for v in state['attempts']))
        save()
    except BaseException:
        state.update(status='full_repeat_supervisor_stopped_requires_review', error=traceback.format_exc())
        save()
        raise


if __name__ == '__main__':
    main()
