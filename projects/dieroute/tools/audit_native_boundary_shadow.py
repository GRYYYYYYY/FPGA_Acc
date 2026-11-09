#!/usr/bin/env python3
"""Check native shadow decision journals and equivalence to direct authority.

This checks the CPU serial-boundary-overlay protocol, not distributed routing,
physical communication traffic or hardware performance.
"""
import argparse
from collections import defaultdict
import csv
import json
import mmap
from pathlib import Path
import struct
import time
from run_native_case import sha256


def rows(path):
    with path.open() as stream:
        return [{k: int(v) for k, v in r.items()} for r in csv.DictReader(stream)]


def journal_hash(observer, net, present, reads):
    h = 1469598103934665603
    words = [0, observer, net, present]  # fresh per-repeat checkpoint epoch
    for r in reads:
        words.extend([r['node'], r['observed_occupancy'], r['observed_history'], r['observed_version']])
    for word in words:
        for byte in struct.pack('<Q', word):
            h = ((h ^ byte) * 1099511628211) & ((1 << 64)-1)
    return h


def verify(baseline, candidate):
    bm = json.loads((baseline/'manifest.json').read_text())
    cm = json.loads((candidate/'manifest.json').read_text())
    for m in (bm, cm):
        assert m['status'] == 'passed' and m['inputs_unchanged'] and m['electrical_model_converged']
    assert len(bm['command']) == 12
    assert len(cm['command']) == 13
    assert bm['inputs'] == cm['inputs']
    assert bm['command'][1:7] == cm['command'][1:7] and bm['command'][8:12] == cm['command'][8:12]
    assert bm['source_sha256'] == cm['source_sha256'], 'compare same implementation and executable'
    period = int(cm['command'][12]); assert period > 0
    repeats = int(cm['command'][11])
    inputs = dict(cm['inputs'])
    for directory, manifest in ((baseline, bm), (candidate, cm)):
        inputs[str(directory/'manifest.json')] = sha256(directory/'manifest.json')
        for name, digest in manifest['artifacts'].items():
            inputs[str(directory/name)] = digest
    for path, digest in inputs.items():
        assert sha256(path) == digest, path
    # Exact physical trees, selected task closure, ownership/history/version and
    # every shared-prefix PIP must agree, not just a total path-length metric.
    equal_files = ['selection.csv', 'trees.csv', 'usage.csv', 'paths.csv', 'connections.csv']
    for name in equal_files:
        assert (baseline/'route'/name).read_bytes() == (candidate/'route'/name).read_bytes(), name
    selection = {r['task']: r for r in rows(candidate/'route/selection.csv')}
    direct_iters = rows(baseline/'route/iterations.csv')
    shadow_iters = rows(candidate/'route/iterations.csv')
    assert len(direct_iters) == len(shadow_iters)
    if period == 1: assert direct_iters == shadow_iters
    work_fields = {'expanded', 'edge_visits', 'max_labels'}
    for direct, shadow in zip(direct_iters, shadow_iters):
        assert {k: v for k, v in direct.items() if k not in work_fields} == {k: v for k, v in shadow.items() if k not in work_fields}
    present = {(r['repeat'], r['iteration']): r['present'] for r in shadow_iters}
    trace = rows(candidate/'route/shadow_trace.csv')
    metrics = rows(candidate/'route/shadow_metrics.csv')
    direct_metrics = rows(baseline/'route/shadow_metrics.csv')
    reads = defaultdict(list)
    read_rows = rows(candidate/'route/shadow_reads.csv')
    for r in read_rows:
        reads[(r['repeat'], r['search'])].append(r)
    graph = Path(cm['command'][1]); footprint = Path(cm['command'][3])
    task_data = (footprint/'tasks.bin').read_bytes()
    dies = 1 + max(max(t[4:6]) for t in struct.iter_unpack('<8I', task_data))
    seen = set(); differing = 0; unused_differing = 0
    with (graph/'nodes.bin').open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as nodes:
        # Native format supports eight SLR membership bits. The graph domain can
        # include dies absent from the workload's source/sink pairs.
        dies = max(dies, max(memoryview(nodes)[20::64]).bit_length())
        for t in trace:
            key = (t['repeat'], t['search']); assert key not in seen; seen.add(key)
            assert 0 <= t['repeat'] < repeats and t['task'] in selection
            task = struct.unpack_from('<8I', task_data, t['task']*32)
            assert t['observer'] == task[4]
            journal = reads.pop(key, [])
            assert len(journal) == t['remote_reads']
            assert [r['node'] for r in journal] == sorted({r['node'] for r in journal})
            stale = False
            for r in journal:
                mask = struct.unpack_from('<I', nodes, r['node']*64+20)[0]
                assert 0 < mask < (1 << dies) and mask & (mask-1)
                assert (mask & -mask) != (1 << t['observer'])
                old = tuple(r['observed_'+k] for k in ('occupancy', 'history', 'version'))
                new = tuple(r['current_'+k] for k in ('occupancy', 'history', 'version'))
                assert old[2] <= new[2]
                assert old[2] != new[2] or old == new
                if old != new:
                    stale = True; differing += 1; unused_differing += new[0] == 0
            assert bool(t['stale']) == stale
            assert t['read_hash'] == journal_hash(t['observer'], task[1], present[(t['repeat'], t['iteration'])], journal)
            assert t['initial_status'] in (-1, 0, 1, 2, 3) and t['final_status'] in (0, 1, 2, 3)
            assert bool(t['overflow']) == (t['initial_status'] == -1)
            if t['overflow']: assert stale
            if stale: assert t['replay_expanded'] > 0
            else: assert t['replay_expanded'] == 0 and t['initial_status'] == t['final_status']
        expected = {}
        for r in rows(candidate/'route/usage.csv'):
            mask = struct.unpack_from('<I', nodes, r['node']*64+20)[0]
            if not mask & (mask-1): continue
            key = (r['repeat'], r['node'])
            value = expected.setdefault(key, dict(repeat=r['repeat'], node=r['node'], occupancy=0, history=r['history'], version=r['version']))
            assert value['history'] == r['history'] and value['version'] == r['version']
            value['occupancy'] += r['net'] != 0xffffffff
        final = rows(candidate/'route/shadow_final.csv')
        assert final == [expected[k] for k in sorted(expected)], 'final publication must drain every boundary update/tombstone'
    assert not reads
    assert len(metrics) == len(direct_metrics) == repeats
    for rep, (m, direct) in enumerate(zip(metrics, direct_metrics)):
        assert m['repeat'] == direct['repeat'] == rep and m['sync_searches'] == period
        part = [t for t in trace if t['repeat'] == rep]
        assert [t['search'] for t in part] == list(range(m['searches']))
        assert m['searches'] == direct['searches']
        assert m['replays'] == sum(t['stale'] for t in part)
        assert m['remote_reads'] == sum(t['remote_reads'] for t in part)
        assert m['publications'] == (m['searches']+period-1)//period+1  # final drain
        assert m['logical_deliveries'] == m['changed_summaries']*(dies-1)
        assert m['retained_summaries'] == sum(r['repeat'] == rep for r in final)
        assert sum(t['initial_expanded']+t['replay_expanded'] for t in part) == sum(r['expanded'] for r in shadow_iters if r['repeat'] == rep)
        if period == 1: assert m['replays'] == 0
        for dataset in (metrics, trace, read_rows, final):
            assert [{k: v for k, v in r.items() if k != 'repeat'} for r in dataset if r['repeat'] == rep] == [{k: v for k, v in r.items() if k != 'repeat'} for r in dataset if r['repeat'] == 0]
    for path, digest in inputs.items():
        assert sha256(path) == digest, path
    return dict(schema='dieroute.native_boundary_shadow_audit.v1', passed=True,
                inputs=inputs, inputs_unchanged=True, repeats=repeats, sync_searches=period,
                exact_route_files_equal=equal_files, repeated_trace_and_metrics_equal=True,
                changed_read_observations=differing, changed_reads_currently_unoccupied=unused_differing,
                metrics=metrics, direct_expanded=sum(r['expanded'] for r in direct_iters),
                shadow_expanded=sum(r['expanded'] for r in shadow_iters),
                direct_edge_visits=sum(r['edge_visits'] for r in direct_iters),
                shadow_edge_visits=sum(r['edge_visits'] for r in shadow_iters),
                board_result=False, distributed_authority=False,
                scope='Serial CPU authority with boundary summary overlays; complete decision-read journals and fresh serial replay. Logical deliveries are modeled broadcast counts, not measured traffic.',
                finished_ns=time.time_ns())


def main():
    if not __debug__: raise RuntimeError('audit requires assertions')
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline-run', type=Path, required=True)
    p.add_argument('--shadow-run', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); out = a.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    result = verify(a.baseline_run.resolve(), a.shadow_run.resolve())
    (out/'audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'inputs'}))


if __name__ == '__main__': main()
