#!/usr/bin/env python3
"""Independently audit full search CSR using original footprints and SDK topology."""
import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path
from run_native_case import sha256


def main():
    if not __debug__:
        raise RuntimeError('audit requires Python assertions')
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('run', 'sdk_run', 'verifier', 'output'):
        parser.add_argument('--' + name.replace('_', '-'), type=Path, required=True)
    args = parser.parse_args()
    run, sdk = args.run.resolve(), args.sdk_run.resolve()
    rm = json.loads((run / 'manifest.json').read_text())
    sm = json.loads((sdk / 'manifest.json').read_text())
    assert rm['status'] == 'passed' and rm['inputs_unchanged']
    assert sm['status'] == 'passed' and sm['dependencies_unchanged']
    graph, mapping, footprint, csr, policy, access = map(Path, rm['command'][1:7])
    assert Path(sm['graph_manifest']).resolve() == graph.parent / 'manifest.json'
    fm = json.loads((footprint.parent / 'manifest.json').read_text())
    inputs = dict(rm['inputs'])
    inputs[str(footprint / 'pins.bin')] = fm['artifacts']['footprint/pins.bin']
    for name in ('offsets.bin', 'arcs.bin', 'node_protection.bin', 'exclusive_net.bin', 'laguna_input.bin'):
        inputs[str(run / 'search' / name)] = rm['artifacts']['search/' + name]
    for name in ('inputs.bin', 'ubump_nodes.bin'):
        inputs[str(sdk / 'export' / name)] = sm['artifacts']['export/' + name]
    parents = dict(rm['parent_manifests'])
    for path in (run / 'manifest.json', sdk / 'manifest.json', footprint.parent / 'manifest.json'):
        parents[str(path)] = sha256(path)
    # SDK runtime, jars and classes were frozen before/after the SDK export;
    # checking its manifest and export hashes binds that independent evidence.
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    for name in (Path(__file__).name, 'run_native_case.py', 'verify_native_search_graph.cpp'):
        shutil.copy2(Path(__file__).with_name(name), out / name)
    shutil.copy2(Path(__file__).parent.parent / 'include/native_csr_io.hpp', out / 'native_csr_io.hpp')
    shutil.copy2(args.verifier, out / 'verify_native_search_graph')
    command = [str(out / 'verify_native_search_graph'), *map(str, (graph, mapping, footprint, csr, policy, access)),
               str(run / 'search'), str(sdk / 'export/inputs.bin'), rm['architecture_sha256'][:32], str(out / 'audit')]
    record = dict(schema='dieroute.native_search_graph_independent_run.v1', status='running',
                  started_ns=time.time_ns(), inputs=inputs, parent_manifests=parents, command=command,
                  architecture_sha256=rm['architecture_sha256'],
                  source_sha256={f.name: sha256(f) for f in out.iterdir() if f.is_file()})
    manifest = out / 'manifest.json'

    def save():
        tmp = out / 'manifest.tmp'
        tmp.write_text(json.dumps(record, indent=2) + '\n')
        tmp.replace(manifest)

    save()
    try:
        for path, expected in {**inputs, **parents}.items():
            assert sha256(path) == expected, path
        with (out / 'verify.log').open('w') as log:
            proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            record['pid'] = proc.pid
            save()
            record['returncode'] = proc.wait()
        # Even a diagnosed rejection retains evidence that inputs stayed fixed.
        for path, expected in {**inputs, **parents}.items():
            assert sha256(path) == expected, path
        record['inputs_unchanged'] = True
        assert record['returncode'] == 0, 'independent native search graph audit rejected the graph'
        assert json.loads((out / 'audit/audit.json').read_text())['passed']
        record.update(status='passed')
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
