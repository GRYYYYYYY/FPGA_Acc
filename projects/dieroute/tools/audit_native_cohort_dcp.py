#!/usr/bin/env python3
"""Compare native checks after actual cohort rerouting against frozen controls."""
import argparse
import json
from pathlib import Path

from audit_dcp_reports import native_reports
from run_native_case import sha256


def main():
    if not __debug__:
        raise RuntimeError('audit requires assertions')
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'noop', 'routed', 'writeback', 'connectivity', 'members', 'sll', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    wb = a.writeback.resolve()
    wm = json.loads((wb/'manifest.json').read_text())
    assert wm['status'] == 'passed' and wm['physical_reload_equal'] and wm['inputs_unchanged']
    for name, digest in wm['artifacts'].items():
        assert sha256(wb/name) == digest, name
    logical = json.loads((a.connectivity/'provenance.json').read_text())
    assert logical['passed'] and logical['strict_exported_terminal_and_leaf_equality']
    assert logical['writeback_manifest_sha256'] == sha256(wb/'manifest.json')
    assert logical['comparison_sha256'] == sha256(a.connectivity/'audit.json')
    members = json.loads(a.members.read_text())
    assert members['inputs_unchanged'] and members['inputs'][str(wb/'write/routed.dcp')] == sha256(wb/'write/routed.dcp')
    controls = members['members']['control']['raw']
    candidate = members['members']['routed']['raw']
    constraints_equal = {k: v for k, v in controls.items() if not k.endswith('.edf')} == {k: v for k, v in candidate.items() if not k.endswith('.edf')}
    assert constraints_equal, 'constraint/hardware/HDL stub members changed'
    base, noop, routed = map(native_reports, (a.baseline, a.noop, a.routed))
    sll = json.loads(a.sll.read_text())
    assert sll['inputs_unchanged']
    for path, digest in sll['inputs'].items():
        if path in wm['inputs']:
            assert wm['inputs'][path] == digest
    original_sll_equal = sll['original_total'] == base['sll_utilization']['Total SLLs Used']
    final_sll_equal = sll['expected_final_total'] == routed['sll_utilization']['Total SLLs Used']
    def boundary_value(report, boundary):
        ends = sorted(boundary.split(' <-> '))
        values = [v for k, v in report['sll_utilization'].items() if sorted(k.split(' <-> ')) == ends]
        assert len(values) == 1
        return values[0]
    for mask, boundary in sll['mask_boundaries'].items():
        original_sll_equal &= sll['original'].get(mask, 0) == boundary_value(base, boundary)
        final_sll_equal &= sll['expected_final'][mask] == boundary_value(routed, boundary)
    rm = json.loads((a.routed/'manifest.json').read_text())
    assert Path(rm['input']).resolve() == wb/'write/routed.dcp'
    bm = json.loads((a.baseline/'manifest.json').read_text())
    assert wm['inputs'][bm['input']] == bm['input_sha256']
    before = dict(line.split('=', 1) for line in (wb/'write/before.txt').read_text().splitlines())
    after = dict(line.split('=', 1) for line in (wb/'write/expected.txt').read_text().splitlines())
    reloaded = dict(line.split('=', 1) for line in (wb/'reload/snapshot.txt').read_text().splitlines())
    assert after == reloaded
    unchanged = {k: before[k] == after[k] for k in before if k != 'selected_routes'}
    assert all(unchanged.values())
    changes = [line.split('\t') for line in (wb/'write/changed_nets.tsv').read_text().splitlines()]
    assert len(changes) == wm['selected_nets'] and all(len(row) == 6 for row in changes)
    assert len({row[0] for row in changes}) == len(changes)
    changed = sum(row[4] != row[5] for row in changes)
    assert changed > 0 and before['selected_routes'] != after['selected_routes']
    design_equal = all(noop['design'][k] == routed['design'][k] for k in ('part', 'cells', 'nets', 'slrs'))
    checks = dict(fully_routed_without_errors=routed['fully_routed_without_errors'],
                  no_drc_errors_or_critical_warnings=routed['no_drc_errors_or_critical_warnings'],
                  same_design_size_as_noop=design_equal,
                  same_primitive_utilization_as_noop=noop['primitive_utilization'] == routed['primitive_utilization'],
                  independent_original_and_new_sll_match_native=original_sll_equal and final_sll_equal,
                  same_routable_count_as_original=base['route']['routable nets'] == routed['route']['routable nets'])
    deltas = {k: routed['timing'][k]-base['timing'][k] for k in ('wns_ns', 'tns_ns', 'whs_ns', 'ths_ns')}
    sll_delta = routed['sll_utilization']['Total SLLs Used']-base['sll_utilization']['Total SLLs Used']
    result = dict(schema='dieroute.native_cohort_dcp_audit.v1',
                  status='native_checks_passed' if all(checks.values()) else 'native_checks_failed',
                  writeback_manifest_sha256=sha256(wb/'manifest.json'), checks=checks,
                  baseline=base, noop=noop, routed=routed, changed_selected_nets=changed,
                  selected_nets=wm['selected_nets'], changed_routes=True, board_result=False,
                  unchanged_physical_fields=unchanged, serialized_physical_state_equal=True,
                  logical_connectivity=logical, constraints_and_hwdef_and_stubs_byte_equal=constraints_equal,
                  members_audit_sha256=sha256(a.members),
                  sll_electrical_count=sll, sll_audit_sha256=sha256(a.sll),
                  old_selected_pips=sum(int(row[2]) for row in changes),
                  new_selected_pips=sum(int(row[3]) for row in changes),
                  timing_delta_vs_original=deltas, sll_delta_vs_original=sll_delta,
                  wirelength_qor_gate_proven=False,
                  scope='Default native route status, DRC, timing summary and SLL utilization after full selected-net rerouting; no route_design repair',
                  not_proven=['full candidate-design rerouting', 'native bus-skew acceptance',
                              'bitstream acceptance', 'joint physical wirelength/CPD gate',
                              'representative held-out cohort', 'physical board performance or energy'])
    with a.output.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('baseline', 'noop', 'routed')}))
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
