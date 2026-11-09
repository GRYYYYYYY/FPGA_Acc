"""Real own-child timeout/no-retry tests and heavy-trial predecessor boundaries."""
import copy
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import neuron_no_retention_trial_v1 as trial
from evaluate_neuron_quotient_astar_full_comparison_v1 import evaluate_frame as baseline_metric_function


def main():
    assert trial.evaluate_frame is baseline_metric_function
    protocol = trial.load(trial.OUT/'protocol.json')
    assert protocol['metric_sets'] == 8 and protocol['concrete_count'] == 1678392
    assert protocol['concrete_k'] == 83920 and protocol['spatial_count'] == 48194 and protocol['spatial_k'] == 20
    trial.check(protocol['bindings'])
    out = trial.R/'experiments/neuron_no_retention_trial_guard_v1_2026-10-17'
    out.mkdir()
    stage_results = {}
    for name, code, timeout in (('success', "print('closed')", 5),
                                 ('failed', 'raise SystemExit(7)', 5),
                                 ('timed_out', 'import time;time.sleep(10)', .1)):
        root = out/name
        root.mkdir()
        try:
            trial.run_stage(root, 'child', ['-c', code], 64*2**20, timeout)
        except AssertionError:
            assert name in ('failed', 'timed_out')
        else:
            assert name == 'success'
        terminal = trial.load(root/'child_terminal.json')
        assert terminal['timed_out'] == (name == 'timed_out')
        assert terminal['exit_status'] == (0 if name == 'success' else 7 if name == 'failed' else -15)
        assert trial.gone(root, 'child_process.json')
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir()}
        with patch.object(trial.subprocess, 'Popen') as launch:
            try:
                trial.run_stage(root, 'child', ['-c', 'raise SystemExit(0)'], 64*2**20, 5)
            except AssertionError as error:
                assert 'no retry' in str(error)
            else:
                raise AssertionError('Started stage was retried')
            launch.assert_not_called()
        assert before == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir()}
        stage_results[name] = terminal
    records = {
        trial.BASELINE_QUEUE/'terminal.json': dict(exit_status=0, full_candidate_and_all8_metrics_completed=True),
        trial.BASELINE/'independent_final_admission_v1.json': dict(all_pass=True, all_original_connections=77106, all_events=101534, bindings={}),
        trial.BASELINE_METRICS/'verification.json': dict(all_pass=True, independently_checked_metric_sets=8, promoted=False, bindings={})}
    cases = [('ready', records, True, False)]
    for path, field, value in (
        (trial.BASELINE_QUEUE/'terminal.json', 'exit_status', 1),
        (trial.BASELINE_QUEUE/'terminal.json', 'full_candidate_and_all8_metrics_completed', False),
        (trial.BASELINE/'independent_final_admission_v1.json', 'all_pass', False),
        (trial.BASELINE/'independent_final_admission_v1.json', 'all_original_connections', 77105),
        (trial.BASELINE/'independent_final_admission_v1.json', 'all_events', 101533),
        (trial.BASELINE_METRICS/'verification.json', 'all_pass', False),
        (trial.BASELINE_METRICS/'verification.json', 'independently_checked_metric_sets', 4),
        (trial.BASELINE_METRICS/'verification.json', 'promoted', True)):
        fixture = copy.deepcopy(records)
        fixture[path][field] = value
        cases.append((field, fixture, True, False))
    fixture = copy.deepcopy(records)
    del fixture[trial.BASELINE_QUEUE/'terminal.json']
    cases += [('missing terminal', fixture, True, False), ('live owner', records, False, False),
              ('binding drift', records, True, True)]
    checked = 0
    for name, fixture, gone, drift in cases:
        def load(path):
            if path not in fixture:
                raise FileNotFoundError(str(path))
            return copy.deepcopy(fixture[path])
        def check(_):
            if drift:
                raise AssertionError('binding drift')
        with patch.object(Path, 'exists', lambda p: p in fixture), patch.object(trial, 'load', load), \
                patch.object(trial, 'gone', lambda p: gone), patch.object(trial, 'check', check), \
                patch.object(trial, 'sha', lambda p: 'fixture'), patch.object(trial.subprocess, 'Popen') as launch:
            try:
                result = trial.baseline_gate()
            except (AssertionError, FileNotFoundError):
                assert name != 'ready'
            else:
                assert name == 'ready' and len(result) == 3
            launch.assert_not_called()
        checked += 1
    with patch.object(trial.subprocess, 'Popen') as launch:
        try:
            trial.baseline_gate()
        except AssertionError:
            pass
        else:
            raise AssertionError('Current unfinished A* baseline admitted')
        launch.assert_not_called()
    assert not (trial.OUT/'process.json').exists()
    proof = dict(all_pass=True, stage_real_child_results=stage_results,
        all_three_started_stage_retries_refused_without_mutation=True,
        predecessor_boundary_cases=checked, actual_current_unfinished_baseline_refused=True,
        same_exact_full_domain_metric_function_and_parameters=True,
        no_neuron_causal_job_or_queue_submitted=True,
        bindings={str(p.resolve()): trial.sha(p) for p in (Path(__file__), Path(trial.__file__), trial.OUT/'protocol.json')},
        scope='Controller boundary/resource/own-child timeout behavior and scientific metric identity, not a completed full neuron causal experiment.')
    (out/'verification.json').write_text(json.dumps(proof, indent=2)+'\n')
    print(json.dumps({k: v for k, v in proof.items() if k != 'bindings'}, indent=2), flush=True)


if __name__ == '__main__':
    main()
