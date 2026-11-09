#!/usr/bin/env python3
"""Resolve audited native trees and serialize a new DCP, then reload and check it.

Python converts IDs and archives evidence; Java only resolves/replaces PIPs.
No routing algorithm, route_design, timing optimization or fallback is invoked.
"""
import argparse
import csv
import json
import mmap
import os
from pathlib import Path
import shutil
import struct
import subprocess
import time

from run_native_case import sha256


def tsv(path, rows):
    with path.open('x') as stream:
        for row in rows:
            cells = [str(v) for v in row]
            if any(any(c in v for c in '\t\r\n') for v in cells):
                raise ValueError('unsupported TSV field')
            stream.write('\t'.join(cells) + '\n')


def main():
    if not __debug__:
        raise RuntimeError('verification requires assertions')
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('run', 'audit', 'output', 'jdk', 'cufr', 'runtime'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--heap-gb', type=int, default=32)
    p.add_argument('--feedback-run', type=Path)
    p.add_argument('--feedback-audit', type=Path)
    p.add_argument('--feedback-case', choices=('zero_floor', 'hold20', 'setup1434'))
    a = p.parse_args()
    run, audit, out = a.run.resolve(), a.audit.resolve(), a.output.resolve()
    rm = json.loads((run/'manifest.json').read_text())
    au = json.loads((audit/'audit.json').read_text())
    assert rm['status'] == 'passed' and rm['electrical_model_converged']
    assert au['passed'] and au['inputs_unchanged'] and au['electrical_model_converged_repeats'] == au['repeats']
    assert au['inputs'][str(run/'manifest.json')] == sha256(run/'manifest.json')
    graph, footprint, mapping = map(Path, (rm['command'][1], rm['command'][3], rm['command'][4]))
    fm = json.loads((footprint.parent/'manifest.json').read_text())
    gm = json.loads((graph.parent/'manifest.json').read_text())
    inputs = dict(au['inputs'])
    inputs[str(audit/'audit.json')] = sha256(audit/'audit.json')
    inputs.update(fm['inputs'])
    tree_path = run/'route/trees.csv'
    expected_pips = au['tree_PIPs_resolved']//au['repeats']
    feedback = None
    if any((a.feedback_run, a.feedback_audit, a.feedback_case)):
        assert all((a.feedback_run, a.feedback_audit, a.feedback_case)), 'all feedback options required'
        fr, fa = a.feedback_run.resolve(), a.feedback_audit.resolve()
        frm = json.loads((fr/'manifest.json').read_text())
        fam = json.loads((fa/'audit.json').read_text())
        assert frm['status'] == 'passed' and frm['inputs_unchanged']
        assert fam['schema'] == 'dieroute.native_timing_feedback_audit.v1' and fam['passed'] and fam['inputs_unchanged']
        assert frm['cohort'] == str(run) and frm['cohort_audit'] == str(audit)
        assert fam['inputs'][str(fr/'manifest.json')] == sha256(fr/'manifest.json')
        case = fam['cases'][a.feedback_case]
        assert case['selected_nets'] == au['selected_nets'] and case['tasks'] == au['tasks']
        tree_path = fr/a.feedback_case/'candidate/trees.csv'
        assert sha256(tree_path) == case['candidate_trees_sha256']
        expected_pips = case['tree_pips']
        for path, digest in fam['inputs'].items():
            assert path not in inputs or inputs[path] == digest
            inputs[path] = digest
        inputs[str(fa/'audit.json')] = sha256(fa/'audit.json')
        feedback = dict(run=str(fr), audit=str(fa), case=a.feedback_case,
                        trees_sha256=case['candidate_trees_sha256'], fresh_native_checks_required=True)
    for path, expected in ((footprint/'nets.csv', fm['artifacts']['footprint/nets.csv']),
                           (footprint/'pins.csv', fm['artifacts']['footprint/pins.csv']),
                           (graph/'tiles.csv', gm['artifacts']['graph/tiles.csv'])):
        inputs[str(path)] = expected
    # Freeze SDK and isolated device database along with all transitive input data.
    assert str(a.runtime.resolve()) == fm['runtime']
    assert {str(f) for f in (a.cufr.resolve()/'jars').glob('*.jar')} == set(fm['jars'])
    assert {str(f) for f in (a.cufr.resolve()/'bin').rglob('*.class')} == set(fm['classpath_classes'])
    sdk = {**fm['jars'], **fm['classpath_classes'],
           **{str(f): sha256(f) for f in a.runtime.resolve().rglob('*.dat')}}
    out.mkdir(parents=True, exist_ok=False)
    for name in ('WriteNativeCohort.java', 'write_native_cohort.py', 'run_native_case.py'):
        shutil.copy2(Path(__file__).with_name(name), out/name)
    record = dict(schema='dieroute.native_cohort_writeback.v1', status='running', inputs=inputs,
                  sdk=sdk, started_ns=time.time_ns(), steps=[], board_result=False,
                  native_design_legal=None, scope='audited whole selected nets, physical serialization and reload')
    if feedback is not None:
        record['feedback_candidate'] = feedback
    manifest = out/'manifest.json'

    def save():
        tmp = out/'manifest.tmp'
        tmp.write_text(json.dumps(record, indent=2)+'\n')
        tmp.replace(manifest)

    save()
    try:
        for path, digest in {**inputs, **sdk}.items():
            assert sha256(path) == digest, path
        trees = [dict((k, int(v)) for k, v in r.items()) for r in csv.DictReader(tree_path.open()) if r['repeat'] == '0']
        selected = {r['net'] for r in trees}
        names = {}
        for r in csv.DictReader((footprint/'nets.csv').open()):
            if int(r['id']) in selected:
                assert r['candidate'] == 'true' and int(r['reason_mask']) == 0
                names[int(r['id'])] = r['name']
        assert set(names) == selected and len(selected) == au['selected_nets']
        tiles = {int(r['address']): r['name'] for r in csv.DictReader((graph/'tiles.csv').open())}
        with (graph/'nodes.bin').open('rb') as nf, (graph/'pips.bin').open('rb') as pf, (mapping/'footprint_node_map.bin').open('rb') as mf:
            with mmap.mmap(nf.fileno(), 0, access=mmap.ACCESS_READ) as nodes, mmap.mmap(pf.fileno(), 0, access=mmap.ACCESS_READ) as pips, mmap.mmap(mf.fileno(), 0, access=mmap.ACCESS_READ) as nm:
                def native(n):
                    tile, wire = struct.unpack_from('<II', nodes, n*64+12)
                    return tiles[tile], wire
                prows = []
                for r in trees:
                    if r['parent'] == 0xffffffff:
                        assert r['depth'] == 0 and r['pip_key'] == 0xffffffff
                        continue
                    pid, direction = r['pip_key'] >> 1, r['pip_key'] & 1
                    pp = struct.unpack_from('<8I', pips, pid*32)
                    assert pp[0] == pid and (pp[7] & 2 or direction == pp[7] & 1)
                    assert tuple(pp[1:3][::-1] if direction else pp[1:3]) == (r['parent'], r['node'])
                    prows.append((r['net'], tiles[pp[3]], pp[4], pp[5], str(bool(direction)).lower(), *native(r['parent']), *native(r['node'])))
                pins = []
                for r in csv.DictReader((footprint/'pins.csv').open()):
                    if int(r['net_id']) in selected:
                        n = struct.unpack_from('<I', nm, int(r['node_id'])*4)[0]
                        pins.append((r['net_id'], r['site_inst'], r['pin'], r['output'], *native(n)))
        assert len(prows) == expected_pips
        tsv(out/'nets.tsv', sorted(names.items()))
        tsv(out/'pips.tsv', prows)
        tsv(out/'pins.tsv', pins)
        record.update(selected_nets=len(names), selected_pins=len(pins), written_pips=len(prows), selected_repeat=0)
        cp = str(a.cufr.resolve()/'bin')+':'+str(a.cufr.resolve()/'jars/*')
        (out/'classes').mkdir()
        jdk = a.jdk.resolve()
        dcp, = [path for path in fm['inputs'] if path.endswith('.dcp')]
        edif, = [path for path in fm['inputs'] if path.endswith('.edf')]
        env = dict(os.environ, RAPIDWRIGHT_PATH=str(a.runtime.resolve()), RW_AUTO_GENERATE_READABLE_EDIF='0')
        java = [str(jdk/'bin/java'), '-Xmx'+str(a.heap_gb)+'g', '-XX:ActiveProcessorCount=8', '-cp', str(out/'classes')+':'+cp, 'WriteNativeCohort']

        def step(name, command):
            record.update(active_step=name, command=command)
            with (out/(name+'.log')).open('w') as log:
                proc = subprocess.Popen(command, cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT)
                record['pid'] = proc.pid
                save()
                code = proc.wait()
            record['steps'].append(dict(name=name, command=command, returncode=code))
            save()
            assert code == 0, name+' failed'

        step('compile', [str(jdk/'bin/javac'), '-cp', cp, '-d', str(out/'classes'), str(out/'WriteNativeCohort.java')])
        step('snapshot_selftest', java+['selftest'])
        step('write', java+['write', dcp, edif, str(out), str(out/'write')])
        # Verify the embedded netlist/physical data, not the old explicit EDIF.
        # Only routing metadata files are copied, so expected state is immutable.
        for name in ('nets.tsv',):
            shutil.copy2(out/name, out/'write'/name)
        step('reload', java+['verify', str(out/'write/routed.dcp'), '-', str(out/'write'), str(out/'reload')])
        assert (out/'write/expected.txt').read_bytes() == (out/'reload/snapshot.txt').read_bytes()
        for path, digest in {**inputs, **sdk}.items():
            assert sha256(path) == digest, path
        record.update(status='passed', inputs_unchanged=True, sdk_unchanged=True, physical_reload_equal=True)
    except Exception as exc:
        record.update(status='failed', error=repr(exc))
        raise
    finally:
        record.update(active_step=None, finished_ns=time.time_ns())
        record['artifacts'] = {str(f.relative_to(out)): sha256(f) for f in out.rglob('*') if f.is_file() and f != manifest}
        save()
    print(json.dumps(dict(status=record['status'], manifest=str(manifest))))


if __name__ == '__main__':
    main()
