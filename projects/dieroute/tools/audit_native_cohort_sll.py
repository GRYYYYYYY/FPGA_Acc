#!/usr/bin/env python3
"""Predict final physical SLL count from disjoint outside and new tree nodes."""
import argparse
from collections import Counter
import csv
import json
import mmap
from pathlib import Path
import struct

from run_native_case import sha256


def main():
    if not __debug__:
        raise RuntimeError('audit requires assertions')
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('run', 'audit', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--feedback-run', type=Path)
    p.add_argument('--feedback-audit', type=Path)
    p.add_argument('--feedback-case', choices=('zero_floor', 'hold20', 'setup1434'))
    a = p.parse_args()
    run, audit = a.run.resolve(), a.audit.resolve()
    rm = json.loads((run/'manifest.json').read_text())
    am = json.loads((audit/'audit.json').read_text())
    assert am['passed'] and am['inputs'][str(run/'manifest.json')] == sha256(run/'manifest.json')
    assert am['electrical_model_converged_repeats'] == am['repeats']
    graph, footprint = Path(rm['command'][1]), Path(rm['command'][3])
    fm = json.loads((footprint.parent/'manifest.json').read_text())
    gm = json.loads((graph.parent/'manifest.json').read_text())
    inputs = {str(footprint/'nodes.bin'): fm['artifacts']['footprint/nodes.bin'],
              str(graph/'nodes.bin'): rm['inputs'][str(graph/'nodes.bin')],
              str(graph/'intents.csv'): gm['artifacts']['graph/intents.csv'],
              str(run/'route/trees.csv'): rm['artifacts']['route/trees.csv'],
              str(audit/'audit.json'): sha256(audit/'audit.json')}
    tree_path = run/'route/trees.csv'
    if any((a.feedback_run, a.feedback_audit, a.feedback_case)):
        assert all((a.feedback_run, a.feedback_audit, a.feedback_case))
        fr, fa = a.feedback_run.resolve(), a.feedback_audit.resolve()
        frm = json.loads((fr/'manifest.json').read_text())
        fam = json.loads((fa/'audit.json').read_text())
        assert frm['status'] == 'passed' and frm['inputs_unchanged'] and frm['cohort'] == str(run)
        assert fam['schema'] == 'dieroute.native_timing_feedback_audit.v1' and fam['passed'] and fam['inputs_unchanged']
        assert fam['inputs'][str(fr/'manifest.json')] == sha256(fr/'manifest.json')
        assert fam['inputs'][str(run/'manifest.json')] == sha256(run/'manifest.json')
        case = fam['cases'][a.feedback_case]
        assert case['selected_nets'] == am['selected_nets'] and case['tasks'] == am['tasks']
        tree_path = fr/a.feedback_case/'candidate/trees.csv'
        inputs.update({str(fr/'manifest.json'): sha256(fr/'manifest.json'),
                       str(fa/'audit.json'): sha256(fa/'audit.json'),
                       str(tree_path): case['candidate_trees_sha256']})
    for path, digest in inputs.items():
        assert sha256(path) == digest
    intents = {r['name']: int(r['id']) for r in csv.DictReader((graph/'intents.csv').open())}
    laguna = intents['NODE_LAGUNA_DATA']
    trees = [dict((k, int(v)) for k, v in r.items()) for r in csv.DictReader(tree_path.open()) if r['repeat'] == '0']
    selected = {r['net'] for r in trees}
    original, withdrawn, added = Counter(), Counter(), Counter()
    with (footprint/'nodes.bin').open('rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as nodes:
        for row in struct.iter_unpack('<16I', nodes):
            if row[8] and row[5].bit_count() > 1 and row[12] == laguna:
                assert row[8] == 1 and row[5] in (3, 6), 'unexpected SLL sharing/membership'
                original[row[5]] += 1
                if row[7] in selected:
                    withdrawn[row[5]] += 1
    seen = set()
    with (graph/'nodes.bin').open('rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as nodes:
        for r in trees:
            assert r['node'] not in seen
            seen.add(r['node'])
            row = struct.unpack_from('<16I', nodes, r['node']*64)
            if row[5].bit_count() > 1 and row[7] == laguna:
                assert row[5] in (3, 6)
                added[row[5]] += 1
    expected = {mask: original[mask]-withdrawn[mask]+added[mask] for mask in (3, 6)}
    for path, digest in inputs.items():
        assert sha256(path) == digest
    result = dict(schema='dieroute.native_cohort_sll.v1', inputs=inputs, inputs_unchanged=True,
                  original=dict(original), removed_selected=dict(withdrawn), new_selected=dict(added),
                  expected_final=expected, original_total=sum(original.values()), expected_final_total=sum(expected.values()),
                  mask_boundaries={'3': 'SLR0 <-> SLR1', '6': 'SLR1 <-> SLR2'},
                  scope='Exact owned NODE_LAGUNA_DATA electrical nodes with multi-SLR membership; prediction must be checked against native utilization',
                  implementation_intent_ordinal=laguna, source_sha256=sha256(__file__))
    if a.feedback_case:
        result['feedback_candidate'] = dict(run=str(fr), case=a.feedback_case, trees_sha256=sha256(tree_path))
    with a.output.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'inputs'}))


if __name__ == '__main__':
    main()
