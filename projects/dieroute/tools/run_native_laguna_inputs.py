#!/usr/bin/env python3
"""Export SDK Laguna topology against the frozen native-graph runtime."""
import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from run_native_case import sha256


def main():
    if not __debug__:
        raise RuntimeError('audit requires Python assertions')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--graph-run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    parent = args.graph_run.resolve() / 'manifest.json'
    gm = json.loads(parent.read_text())
    assert gm['status'] == 'passed' and gm['dependencies_unchanged']
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out / 'classes').mkdir()
    for name in ('NativeLagunaInputs.java', 'run_native_case.py', Path(__file__).name):
        shutil.copy2(Path(__file__).with_name(name), out / name)
    original = gm['command']
    java = Path(original[0])
    cp = original[original.index('-cp') + 1].split(':', 1)[1]
    env = dict(os.environ, RAPIDWRIGHT_PATH=gm['runtime'])
    commands = [
        ('compile', [str(java.with_name('javac')), '-cp', cp, '-d', str(out / 'classes'), str(out / 'NativeLagunaInputs.java')]),
        ('export', [str(java), '-ea', '-Xmx8g', '-cp', str(out / 'classes') + ':' + cp, 'NativeLagunaInputs', gm['device'], str(out / 'export')]),
    ]
    inputs = {str(parent): sha256(parent)}
    for group in ('runtime_data', 'jars', 'classpath_classes'):
        inputs.update(gm[group])
    record = dict(schema='dieroute.native_laguna_inputs_run.v2', status='running',
                  started_ns=time.time_ns(), inputs=inputs, graph_manifest=str(parent),
                  RAPIDWRIGHT_PATH=env['RAPIDWRIGHT_PATH'], steps=[],
                  source_sha256={f.name: sha256(f) for f in out.iterdir() if f.is_file()})
    manifest = out / 'manifest.json'

    def save():
        tmp = out / 'manifest.tmp'
        tmp.write_text(json.dumps(record, indent=2) + '\n')
        tmp.replace(manifest)

    save()
    try:
        for path, expected in inputs.items():
            assert sha256(path) == expected, path
        for name, command in commands:
            step = dict(name=name, command=command)
            record['steps'].append(step)
            with (out / (name + '.log')).open('w') as log:
                proc = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT)
                step['pid'] = proc.pid
                save()
                step['returncode'] = proc.wait()
            assert step['returncode'] == 0, name
        for path, expected in inputs.items():
            assert sha256(path) == expected, path
        record.update(status='passed', dependencies_unchanged=True)
    except Exception as exc:
        record.update(status='failed', error=repr(exc))
        raise
    finally:
        record['finished_ns'] = time.time_ns()
        record['artifacts'] = {str(f.relative_to(out)): sha256(f) for f in sorted(out.rglob('*')) if f.is_file() and f != manifest}
        save()
    print(json.dumps(dict(manifest=str(manifest), status=record['status'])))


if __name__ == '__main__':
    main()
