"""Failure-boundary tests for the heavy candidate's predecessor gate."""
import copy
import json
from pathlib import Path
from unittest.mock import patch

import run_neuron_quotient_astar_pipeline_v1 as candidate


def main():
    model, metric, diagnosis = candidate.MODEL_QUEUE, candidate.METRIC_QUEUE, candidate.DIAGNOSTIC
    comparison = candidate.METRICS
    records = {
        model/'terminal.json': dict(exit_status=0),
        metric/'terminal.json': dict(exit_status=0, comparison_completed=True),
        comparison/'verification.json': dict(all_pass=True, independently_checked_metric_sets=12,
            factors=[1, 2, 4], promoted=False, bindings={}),
        diagnosis/'terminal.json': dict(exit_status=0),
        diagnosis/'verification.json': dict(all_pass=True, all_endpoint_target_tables=455,
            graph_search_calls=0, bindings={})}
    cases = []
    for path in (model/'terminal.json', metric/'terminal.json', diagnosis/'terminal.json'):
        changed = copy.deepcopy(records)
        changed[path]['exit_status'] = 1
        cases.append((f'failed terminal {path.parent.name}', changed, None, False))
    for path, field, value in (
        (metric/'terminal.json', 'comparison_completed', False),
        (comparison/'verification.json', 'all_pass', False),
        (comparison/'verification.json', 'independently_checked_metric_sets', 8),
        (comparison/'verification.json', 'factors', [1, 2]),
        (comparison/'verification.json', 'promoted', True),
        (diagnosis/'verification.json', 'all_pass', False),
        (diagnosis/'verification.json', 'all_endpoint_target_tables', 454),
        (diagnosis/'verification.json', 'graph_search_calls', 1)):
        changed = copy.deepcopy(records)
        changed[path][field] = value
        cases.append((f'incomplete/wrong {path.parent.name}/{field}', changed, None, False))
    for root in (model, metric, diagnosis):
        cases.append((f'live owner {root.name}', records, root, False))
    for missing in records:
        changed = copy.deepcopy(records)
        del changed[missing]
        cases.append((f'missing {missing.parent.name}/{missing.name}', changed, None, False))
    cases.append(('binding drift', records, None, True))
    passed = []
    for name, fixture, live, drift in [('complete fixture', records, None, False), *cases]:
        def load(path):
            if path not in fixture:
                raise FileNotFoundError(str(path))
            return copy.deepcopy(fixture[path])
        def check(_):
            if drift:
                raise AssertionError('binding drift')
        with patch.object(candidate, 'load', load), patch.object(candidate, 'gone', lambda root: root != live), \
                patch.object(candidate, 'check', check), patch.object(candidate, 'sha', lambda p: 'fixture'), \
                patch.object(candidate.subprocess, 'Popen') as launch:
            try:
                result = candidate.predecessor_bindings()
            except (AssertionError, FileNotFoundError):
                assert name != 'complete fixture'
            else:
                assert name == 'complete fixture' and len(result) == 5
            launch.assert_not_called()
        passed.append(name)
    # The real current gate must refuse while the original queue is live, and
    # must leave the prepared candidate without an ownership/submission record.
    with patch.object(candidate.subprocess, 'Popen') as launch:
        try:
            candidate.predecessor_bindings()
        except (AssertionError, FileNotFoundError):
            pass
        else:
            raise AssertionError('Expected current unfinished predecessor gate to refuse')
        launch.assert_not_called()
    assert not (candidate.OUT/'process.json').exists()
    out = candidate.R/'experiments/neuron_quotient_launch_gate_contract_v1_2026-10-17'
    out.mkdir()
    bindings = {str(p): candidate.sha(p) for p in (Path(__file__),
        Path(candidate.__file__), candidate.OUT/'protocol.json')}
    proof = dict(all_pass=True, bindings=bindings, fixture_cases=passed,
        real_current_predecessors_refused=True, candidate_model_submitted=False,
        scope='Boundary testing for resource-heavy launch ordering only. No model, quality or performance result.')
    (out/'verification.json').write_text(json.dumps(proof, indent=2)+'\n')
    print(json.dumps(proof, indent=2), flush=True)


if __name__ == '__main__':
    main()
