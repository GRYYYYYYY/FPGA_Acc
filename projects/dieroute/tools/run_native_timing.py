#!/usr/bin/env python3
"""Archive read-only bus-skew, targeted timing and selected-net delay queries."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import time

from run_native_case import sha256


def main():
    if not __debug__:
        raise RuntimeError('verification requires assertions')
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('native-run', 'selected-nets', 'targets', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    parent, out = a.native_run.resolve(), a.output.resolve()
    pm = json.loads((parent/'manifest.json').read_text())
    assert pm['status'] == 'reports_generated' and pm['returncode'] == 0
    # The first baseline manifest predates these flags. Both legacy and current
    # inputs are checked against their frozen digests before and after this run.
    assert pm.get('input_unchanged', True) and pm.get('dependencies_unchanged', True)
    inputs = {str(parent/'manifest.json'): sha256(parent/'manifest.json'), pm['input']: pm['input_sha256'],
              str(a.selected_nets.resolve()): sha256(a.selected_nets), str(a.targets.resolve()): sha256(a.targets),
              **pm.get('dependencies', {})}
    loader = parent/'checkpoint_load.tcl'
    if loader.exists():
        inputs[str(loader)] = pm['artifacts']['checkpoint_load.tcl']
    for path, digest in inputs.items():
        assert sha256(path) == digest, path
    vivado = shutil.which('vivado')
    assert vivado, 'source the target Xilinx settings64.sh'
    out.mkdir(parents=True, exist_ok=False)
    for name in ('check_native_timing.tcl', 'run_native_timing.py', 'run_native_case.py'):
        shutil.copy2(Path(__file__).with_name(name), out/name)
    for source, name in ((a.selected_nets, 'nets.tsv'), (a.targets, 'targets.tsv')):
        shutil.copy2(source, out/name)
    if loader.exists():
        shutil.copy2(loader, out/'checkpoint_load.tcl')
    command = [vivado, '-mode', 'batch', '-source', str(out/'check_native_timing.tcl'), '-tclargs',
               pm['input'], str(out/'checkpoint_load.tcl') if loader.exists() else '-',
               str(out/'nets.tsv'), str(out/'targets.tsv'), str(out/'reports')]
    record = dict(schema='dieroute.native_extended_timing.v1', status='running', inputs=inputs,
                  command=command, cwd=str(out), started_ns=time.time_ns(), board_result=False, changes_routes=False)
    manifest = out/'manifest.json'

    def save():
        tmp = out/'manifest.tmp'
        tmp.write_text(json.dumps(record, indent=2)+'\n')
        tmp.replace(manifest)

    save()
    try:
        with (out/'console.log').open('w') as log:
            proc = subprocess.Popen(command, cwd=out, stdout=log, stderr=subprocess.STDOUT)
            record['pid'] = proc.pid
            save()
            code = proc.wait()
        record['returncode'] = code
        for path, digest in inputs.items():
            assert sha256(path) == digest, path
        record['inputs_unchanged'] = True
        required = ('design.txt', 'route_status.rpt', 'bus_skew_summary.rpt', 'bus_skew_paths.rpt',
                    'worst_hold.rpt', 'worst_setup.rpt', 'query_status.tsv', 'net_delays.tsv', 'completed.txt')
        record['reports_complete'] = all((out/'reports'/name).is_file() for name in required)
        assert code == 0 and record['reports_complete'], 'native timing reports incomplete'
        assert 'queries_failed=0\n' in (out/'reports/completed.txt').read_text()
        record['status'] = 'reports_generated'
    except Exception as exc:
        record.update(status='failed', error=repr(exc))
        raise
    finally:
        record['finished_ns'] = time.time_ns()
        record['artifacts'] = {str(f.relative_to(out)): sha256(f) for f in out.rglob('*') if f.is_file() and f != manifest}
        save()
    print(json.dumps(dict(status=record['status'], manifest=str(manifest))))


if __name__ == '__main__':
    main()
