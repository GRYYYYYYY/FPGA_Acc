#!/usr/bin/env python3
"""Freeze a read-only conversion of native delay endpoints to site pins."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from audit_native_timing import read_run
from run_native_case import sha256


def main():
    if not __debug__:
        raise RuntimeError('verification requires assertions')
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('timing-run', 'footprint-run', 'cohort-run', 'jdk', 'cufr', 'runtime', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--heap-gb', type=int, default=24)
    a = p.parse_args()
    assert a.heap_gb > 0
    timing = a.timing_run.resolve();tm, names, targets, bus, delays, paths = read_run(timing)
    footprint = a.footprint_run.resolve();fm = json.loads((footprint/'manifest.json').read_text())
    cohort = a.cohort_run.resolve();cm = json.loads((cohort/'manifest.json').read_text())
    assert fm['status'] == cm['status'] == 'passed' and cm['electrical_model_converged']
    assert cm['inputs'][str(footprint/'manifest.json')] == sha256(footprint/'manifest.json')
    dcp, = [Path(f) for f in fm['inputs'] if f.endswith('.dcp')]
    edif, = [Path(f) for f in fm['inputs'] if f.endswith('.edf')]
    assert tm['inputs'][str(dcp)] == fm['inputs'][str(dcp)]
    inputs = {str(footprint/'manifest.json'): sha256(footprint/'manifest.json'),
              str(cohort/'manifest.json'): sha256(cohort/'manifest.json'),
              str(timing/'manifest.json'): sha256(timing/'manifest.json'), **fm['inputs']}
    for directory, manifest, files in [(footprint, fm, ('footprint/tasks.bin', 'footprint/pins.csv', 'footprint/nets.csv')),
                                        (cohort, cm, ('route/selection.csv',))]:
        for name in files:
            inputs[str(directory/name)] = manifest['artifacts'][name]
    sdk = {**fm['jars'], **fm['classpath_classes'], **{str(f): sha256(f) for f in a.runtime.resolve().rglob('*.dat')}}
    assert str(a.runtime.resolve()) == fm['runtime']
    assert {str(f) for f in (a.cufr.resolve()/'jars').glob('*.jar')} == set(fm['jars'])
    assert {str(f) for f in (a.cufr.resolve()/'bin').rglob('*.class')} == set(fm['classpath_classes'])
    out = a.output.resolve();out.mkdir(parents=True, exist_ok=False);(out/'classes').mkdir()
    for name in ('NativeTimingPins.java', 'run_native_timing_pins.py', 'audit_native_timing.py', 'run_native_case.py'):
        shutil.copy2(Path(__file__).with_name(name), out/name)
    def escape(s):
        return s.replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n').replace('\r', '\\r')
    with (out/'load_pins.tsv').open('w') as f:
        f.write('net_id\tnet_name\tto_pin\n')
        for n, mode, pin in sorted(delays):
            if mode == 'total':
                f.write(f'{n}\t{escape(names[n])}\t{escape(pin)}\n')
    cp = str(a.cufr.resolve()/'bin')+':'+str(a.cufr.resolve()/'jars/*')
    commands = [
        [str(a.jdk.resolve()/'bin/javac'), '-cp', cp, '-d', str(out/'classes'), str(out/'NativeTimingPins.java')],
        [str(a.jdk.resolve()/'bin/java'), f'-Xmx{a.heap_gb}g', '-XX:ActiveProcessorCount=4', '-cp', str(out/'classes')+':'+cp,
         'NativeTimingPins', str(dcp), str(edif), str(out/'load_pins.tsv'), str(out/'pins')]]
    record = dict(schema='dieroute.native_timing_pin_export.v1', status='running', inputs=inputs, sdk=sdk,
                  commands=commands, cwd=str(out), runtime=str(a.runtime.resolve()), steps=[], started_ns=time.time_ns(),
                  board_result=False, changes_routes=False, logical_loads=len(delays)//2)
    manifest = out/'manifest.json'
    def save():
        temp=out/'manifest.tmp';temp.write_text(json.dumps(record, indent=2)+'\n');temp.replace(manifest)
    save()
    try:
        for path, digest in {**inputs, **sdk}.items():
            assert sha256(path) == digest, path
        env = dict(os.environ, RAPIDWRIGHT_PATH=str(a.runtime.resolve()), RW_AUTO_GENERATE_READABLE_EDIF='0')
        for name, command in zip(('compile', 'export'), commands):
            with (out/(name+'.log')).open('w') as log:
                proc = subprocess.Popen(command, cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT)
                step = dict(name=name, pid=proc.pid);record['steps'].append(step);save()
                step['returncode'] = proc.wait();save();assert step['returncode'] == 0, name
        for path, digest in {**inputs, **sdk}.items():
            assert sha256(path) == digest, path
        assert 'routes_changed=false\n' in (out/'pins/completed.txt').read_text()
        record.update(status='passed', inputs_unchanged=True, sdk_unchanged=True)
    except Exception as exc:
        record.update(status='failed', error=repr(exc));raise
    finally:
        record['artifacts']={str(f.relative_to(out)): sha256(f) for f in out.rglob('*') if f.is_file() and f!=manifest}
        record['finished_ns']=time.time_ns();save()
    print(json.dumps(dict(status=record['status'], manifest=str(manifest))))


if __name__ == '__main__':
    main()
