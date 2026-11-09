"""Aggregate current matched backend cells; retain the failed interface controls."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
from audit_prospective_final_native_identity import verify_quality


def main():
    directory = Path(sys.argv[1]).resolve()
    config = json.loads((directory / 'protocol.json').read_text())
    assert not (directory / 'manifest.json').exists()
    state = {'status': 'waiting_for_original_matrix_owners', 'pid': os.getpid(), 'research_complete': False}

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
        for dependency in config['dependencies']:
            while True:
                manifest = json.loads(Path(dependency['manifest']).read_text())
                if manifest['status'] == dependency['terminal']:
                    break
                assert manifest['status'] != 'current_matrix_stopped_requires_review', manifest.get('error')
                owner = dependency['owner']
                text = (Path('/proc') / str(owner['pid']) / 'stat').read_text()
                fields = text[text.rfind(')') + 2:].split()
                assert fields[0] != 'Z' and fields[19] == owner['start_ticks']
                time.sleep(10)
        state['status'] = 'checking_all_twelve_matched_cells'
        save()
        hierarchical = Path(config['hierarchical'])
        flat = Path(config['flat'])
        hp = read(hierarchical / 'protocol.json', True)
        fp = read(flat / 'protocol.json', True)
        hm = read(hierarchical / 'manifest.json')
        fm = read(flat / 'manifest.json')
        assert len(hp['cases']) == len(hm['cases']) == 12
        assert len(fp['cases']) == len(fm['cases']) == 6
        hcases = {v['cell']: v for v in hp['cases'] if v['mode'] == 'downstream_bounded'}
        fcases = {v['cell']: v for v in fp['cases']}
        assert set(hcases) == set(fcases)
        assert {(v['layers'], v['width']) for v in hcases.values()} == {(l, w) for l in [2, 3, 4] for w in [80, 96]}
        results = {v['label']: v for v in hm['cases'] if v['mode'] == 'downstream_bounded'}
        results.update({v['label']: v for v in fm['cases']})
        startup_failures = [v for v in hm['cases'] if v['mode'] == 'flat']
        assert len(startup_failures) == 6 and all(not v.get('native_legal', False) for v in startup_failures)
        pairs = []
        for cell in sorted(hcases):
            hc, fc = hcases[cell], fcases[cell]
            hs = read(Path(hc['parent_command'][2]))['steps'][0]
            fs = read(Path(fc['parent_command'][2]))['steps'][0]
            he, fe = dict(hs['routing_environment']), dict(fs['routing_environment'])
            assert he.pop('DIEROUTE_REMAINING_LAYER_TAIL') == '1'
            assert fe.pop('DIEROUTE_REMAINING_LAYER_TAIL') == '0'
            assert he == fe, 'Unregistered paired environment difference'
            assert [v for i, v in enumerate(hs['command']) if i not in [3, 4]] == [v for i, v in enumerate(fs['command']) if i not in [3, 4]]
            assert hs['command'][4] == 'downstream_bounded' and fs['command'][4] == 'flat'
            assert sha(Path(hc['parent_command'][2]).parent / 'input.tasks') == sha(Path(fc['parent_command'][2]).parent / 'input.tasks')
            reviewed = []
            for case in [fc, hc]:
                result = results[case['label']]
                row = {'label': case['label'], 'mode': case['mode'], 'status': result['status'],
                       'native_legal': result.get('native_legal', False), 'joint_quality_pass': False}
                output = Path(case['output'])
                if (output / 'route.json').exists():
                    metrics = read(output / 'route.json')
                    assert metrics['remaining_layer_tail'] == (case['mode'] == 'downstream_bounded')
                    row.update(iterations=metrics['iterations'], overused_resources=metrics['overused_resources'],
                               expanded=metrics['expanded'], edge_visits=metrics['edge_visits'], parent_wall_ms=metrics['wall_ms'])
                if row['native_legal']:
                    assert result['status'] == 'current_matrix_cell_native_reviewed'
                    assert all(v['returncode'] == 0 for v in result['commands'])
                    read(output / 'tree_audit.json', True)
                    read(output / 'session_provenance_audit.json', True)
                    pre = read(Path(case['preflight']) / 'independent_preflight.json', True)
                    q = verify_quality(output / 'native_validation/validation.json', Path(case['native_case']), sha)
                    checks = {'native_legal': q['legal'], 'capacity': pre['candidate']['overused_resources'] == 0,
                              'wirelength': q['total_wirelength'] <= case['baseline_wirelength'],
                              'CPD': q['critical_path_delay_ns'] <= case['baseline_cpd_ns'],
                              'modeled_transitions': pre['candidate']['layer_transitions'] <= pre['baseline']['layer_transitions']}
                    assert checks == result['checks']
                    row.update(checks=checks, joint_quality_pass=all(checks.values()), wirelength=q['total_wirelength'],
                               cpd_ns=q['critical_path_delay_ns'], model_crossings=pre['candidate']['layer_transitions'])
                reviewed.append(row)
            pairs.append({'cell': cell, 'layers': hc['layers'], 'width': hc['width'],
                          'baseline_wirelength': hc['baseline_wirelength'], 'baseline_cpd_ns': hc['baseline_cpd_ns'],
                          'backends': reviewed})
        for path in [directory / 'protocol.json', Path(__file__).resolve()]:
            sha(path)
        report = {'status': 'twelve_current_matched_backend_cells_and_interface_failures_reviewed',
                  'planned_algorithm_cells': 12, 'retained_interface_attempts': startup_failures,
                  'native_legal': sum(v['native_legal'] for pair in pairs for v in pair['backends']),
                  'joint_passes': sum(v['joint_quality_pass'] for pair in pairs for v in pair['backends']),
                  'pairs': pairs, 'source_sha256': refs, 'research_complete': False,
                  'scope': 'Current parent routing only: one ex5p/seed1 run per backend/cell, same per-cell graph/placement/parameters. Hierarchical-only tail switch disabled in flat API repair; original six failed startup attempts preserved. Fixed per-layer grid grows total resources; not strong scaling, repeated benchmark, generalization, full-refinement pipeline or physical board performance. Timers are descriptive under background load.'}
        with (directory / 'audit.json').open('x') as stream:
            json.dump(report, stream, indent=2)
            stream.write('\n')
        state['status'] = 'matched_backend_matrix_audit_ready'
        save()
    except BaseException:
        state.update(status='matched_matrix_audit_stopped_requires_review', error=traceback.format_exc())
        save()
        raise


if __name__ == '__main__':
    main()
