"""Run all twelve declared current-backend cells, retaining every failure."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback


def main():
    directory = Path(sys.argv[1]).resolve()
    protocol = json.loads((directory / 'protocol.json').read_text())
    assert not (directory / 'manifest.json').exists(), 'No replay'
    assert len(protocol['cases']) == 6
    state = {'status': 'checking_frozen_matrix_sources', 'pid': os.getpid(), 'cases': [], 'research_complete': False}

    def save():
        temp = directory / 'manifest.tmp'
        temp.write_text(json.dumps(state, indent=2) + '\n')
        temp.replace(directory / 'manifest.json')

    def verify():
        for name, expected in protocol['source_sha256'].items():
            h = hashlib.sha256()
            with Path(name).open('rb') as stream:
                for block in iter(lambda: stream.read(1048576), b''):
                    h.update(block)
            assert h.hexdigest() == expected, name

    def run(args, log, row):
        started = time.monotonic_ns()
        with log.open('x') as stream:
            child = subprocess.Popen(args, stdout=stream, stderr=subprocess.STDOUT, cwd=protocol['root'])
            row['active_pid'] = child.pid
            save()
            code = child.wait()
        row['commands'].append({'command': args, 'returncode': code, 'wall_ns': time.monotonic_ns() - started})
        save()
        return code

    try:
        verify()
        save()
        for case in protocol['cases']:
            started = time.monotonic_ns()
            row = {'label': case['label'], 'cell': case['cell'], 'mode': case['mode'],
                   'layers': case['layers'], 'width': case['width'], 'status': 'routing', 'commands': []}
            state['cases'].append(row)
            state.update(status='running_declared_current_matrix', active_case=case['label'])
            save()
            try:
                folder = Path(case['output'])
                code = run(case['parent_command'], directory / (case['label'] + '_parent.log'), row)
                if not (folder / 'route.json').exists():
                    assert code != 0
                    row.update(status='parent_execution_failure_retained', native_legal=False)
                    continue
                metrics = json.loads((folder / 'route.json').read_text())
                row.update(iterations=metrics['iterations'], expanded=metrics['expanded'],
                           edge_visits=metrics['edge_visits'], parent_wall_ms=metrics['wall_ms'],
                           overused_resources=metrics['overused_resources'])
                if not metrics['legal']:
                    row.update(status='nonconverged_parent_retained', native_legal=False)
                    continue
                assert code == 0, 'Parent wrapper failed despite legal C++ report'
                for i, args in enumerate(case['review_commands']):
                    if run(args, directory / (case['label'] + '_review' + str(i) + '.log'), row):
                        row.update(status='native_review_failure_retained', native_legal=False)
                        break
                else:
                    quality = json.loads((folder / 'native_validation/validation.json').read_text())
                    pre = json.loads((Path(case['preflight']) / 'independent_preflight.json').read_text())
                    assert quality['legal'] and pre['candidate']['overused_resources'] == 0
                    checks = {'native_legal': quality['legal'], 'capacity': pre['candidate']['overused_resources'] == 0,
                              'wirelength': quality['total_wirelength'] <= case['baseline_wirelength'],
                              'CPD': quality['critical_path_delay_ns'] <= case['baseline_cpd_ns'],
                              'modeled_transitions': pre['candidate']['layer_transitions'] <= pre['baseline']['layer_transitions']}
                    row.update(status='current_matrix_cell_native_reviewed', native_legal=True, checks=checks,
                               joint_quality_pass=all(checks.values()), wirelength=quality['total_wirelength'],
                               cpd_ns=quality['critical_path_delay_ns'], model_crossings=pre['candidate']['layer_transitions'],
                               baseline_model_crossings=pre['baseline']['layer_transitions'])
            except Exception:
                row.update(status='matrix_cell_error_retained_no_retry', native_legal=False, error=traceback.format_exc())
            finally:
                row['full_cell_wall_ns'] = time.monotonic_ns() - started
                save()
        verify()
        state.update(status='six_corrected_flat_cells_terminal_require_independent_review',
                     native_legal=sum(v.get('native_legal', False) for v in state['cases']),
                     joint_passes=sum(v.get('joint_quality_pass', False) for v in state['cases']))
        save()
    except BaseException:
        state.update(status='current_matrix_stopped_requires_review', error=traceback.format_exc())
        save()
        raise


if __name__ == '__main__':
    main()
