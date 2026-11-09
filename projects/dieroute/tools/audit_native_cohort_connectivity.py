#!/usr/bin/env python3
"""Prove selected-route writeback retains the baseline readable EDIF semantics."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from audit_edif_connectivity import compare
from run_native_case import sha256


def main():
    if not __debug__:
        raise RuntimeError('audit requires assertions')
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline-run', 'routed-run', 'writeback', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    baseline, routed, wb = a.baseline_run.resolve(), a.routed_run.resolve(), a.writeback.resolve()
    bm, rm, wm = [json.loads((x/'manifest.json').read_text()) for x in (baseline, routed, wb)]
    assert all(m['status'] == 'passed' and m['inputs_unchanged'] for m in (bm, rm, wm))
    assert bm['source_sha256'] == rm['source_sha256'] == sha256(routed/'EdifConnectivityProbe.java')
    original = bm['runs']['baseline']
    assert wm['inputs'][original['input']] == original['input_sha256'] == sha256(original['input'])
    embedded = rm['runs']['routed']
    h = hashlib.sha256()
    dcp = wb/'write/routed.dcp'
    assert sha256(dcp) == wm['artifacts']['write/routed.dcp']
    with zipfile.ZipFile(dcp) as z:
        names = [n for n in z.namelist() if n.endswith('.edf')]
        assert len(names) == 1
        with z.open(names[0]) as f:
            for data in iter(lambda: f.read(8*1024*1024), b''):
                h.update(data)
    assert h.hexdigest() == embedded['input_sha256'] == sha256(embedded['input'])
    for root, manifest, label in ((baseline, bm, 'baseline'), (routed, rm, 'routed')):
        for name in ('leaves.csv', 'endpoints.csv', 'summary.json'):
            assert sha256(root/label/name) == manifest['artifacts'][label+'/'+name]
    result = compare(baseline/'baseline', routed/'routed', a.output)
    strict = result['strict_exported_terminal_and_leaf_equality']
    record = dict(schema='dieroute.native_cohort_connectivity.v1', passed=strict,
                  strict_exported_terminal_and_leaf_equality=strict,
                  leaf_instances=result['leaves']['unchanged'], endpoints=result['endpoints']['unchanged'],
                  source_archive_member_sha256=h.hexdigest(),
                  writeback_manifest=str(wb/'manifest.json'), writeback_manifest_sha256=sha256(wb/'manifest.json'),
                  parent_manifests={str(x/'manifest.json'): sha256(x/'manifest.json') for x in (baseline, routed)},
                  comparison_sha256=sha256(a.output/'audit.json'),
                  scope=result['scope'], not_proven=['encrypted cell internal equivalence'])
    (a.output/'provenance.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record))
    return 0 if strict else 1


if __name__ == '__main__':
    raise SystemExit(main())
