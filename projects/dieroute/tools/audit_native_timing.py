#!/usr/bin/env python3
"""Audit paired native bus-skew coverage and routed net-delay observations."""
import argparse
from collections import Counter, defaultdict
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import shutil

from run_native_case import sha256


def unescape(value):
    out = [];i = 0
    while i < len(value):
        if value[i] == '\\':
            i += 1
            if i == len(value) or value[i] not in '\\tnr':
                raise ValueError('invalid TSV field escape')
            out.append({'\\': '\\', 't': '\t', 'n': '\n', 'r': '\r'}[value[i]])
        else:
            out.append(value[i])
        i += 1
    return ''.join(out)


def rows(path):
    with path.open() as f:
        return [{k: unescape(v) for k, v in r.items()} for r in csv.DictReader(f, delimiter='\t')]


def number(value):
    n = Decimal(value)
    if not n.is_finite():
        raise ValueError('nonfinite numeric timing value')
    return n


def collection_identity(expression):
    """Normalize only a literal get_cells collection, never evaluate report Tcl.

    Collection order is immaterial to set_bus_skew -from/-to. Preserve duplicates
    as a multiset and keep the two directions separate. Other expressions retain
    exact text, so unsupported syntax cannot silently become equivalent.
    """
    match = re.fullmatch(r'\[get_cells \[list (\{[^{}\\]+\}(?: \{[^{}\\]+\})*)\]\]', expression)
    if match:
        return ['literal_get_cells', sorted(re.findall(r'\{([^{}\\]+)\}', match[1]))]
    return ['exact_expression', expression]


def checked_delays(props, net_name):
    assert props['CLASS'] == 'net_delay' and props['ESTIMATED'] == '0' and props['NET'] == net_name
    delay = {k: str(number(props[k])) for k in ('FAST_MIN', 'FAST_MAX', 'SLOW_MIN', 'SLOW_MAX')}
    assert all(number(v) >= 0 for v in delay.values())
    assert number(delay['FAST_MIN']) <= number(delay['FAST_MAX']) and number(delay['SLOW_MIN']) <= number(delay['SLOW_MAX'])
    return delay


def bus_comparison(original, routed):
    signature = lambda row: (row['identity_sha256'], row['classification'], row['endpoints'], row['corner'], row['actual_ns'], row['slack_ns'])
    assert Counter(r['identity_sha256'] for r in original) == Counter(r['identity_sha256'] for r in routed), 'bus constraint identity/coverage mismatch'
    finite = [r for r in routed if r['slack_ns'] is not None]
    assert finite, 'no evaluated bus constraints'
    return dict(constraints=len(routed), evaluated=len(finite), single_endpoint_no_comparison=len(routed)-len(finite),
                violations=sum(number(r['slack_ns']) < 0 for r in finite),
                minimum_slack_ns=str(min(number(r['slack_ns']) for r in finite)),
                all_coverage_and_reported_values_equal=Counter(map(signature, original)) == Counter(map(signature, routed)))


def bus_rows(summary, detailed):
    blocks = re.findall(r'^Id:\s*(\d+)\n(.*?)(?=^Id:|\Z)', detailed, re.M | re.S)
    detail = {int(i): block for i, block in blocks}
    assert len(detail) == len(blocks), 'duplicate detailed constraint'
    lines = summary.splitlines()
    header = next(i for i, line in enumerate(lines) if re.match(r'^Id\s+Position\s+From\s+To\s+Corner', line))
    result = [];current = None
    for line in lines[header+2:]:
        if not line.strip():
            continue
        start = re.match(r'^(\d+)\s+(\d+)\s+(.+)$', line)
        end = re.fullmatch(r'\s*(Slow|Fast|NA)\s+([\d.]+)\s+(NA|[-\d.]+)\s+(NA|[-\d.]+)\s*', line)
        if start:
            assert current is None, 'unfinished bus row'
            current = dict(id=int(start[1]), position=int(start[2]), definition=[start[3]])
        elif end:
            assert current is not None
            corner, requirement, actual, slack = end.groups()
            block = detail[current['id']]
            endpoints = int(re.search(r'^Endpoints:\s+(\d+)$', block, re.M)[1])
            assert number(re.search(r'^Requirement:\s+([\d.]+)ns$', block, re.M)[1]) == number(requirement)
            current.update(corner=corner, requirement_ns=requirement, endpoints=endpoints)
            if corner == 'NA':
                assert actual == slack == 'NA' and endpoints == 1 and 'No bus skew paths found.' in block
                current.update(actual_ns=None, slack_ns=None, classification='single_endpoint_no_comparison')
            else:
                assert actual != 'NA' and slack != 'NA' and endpoints > 1
                assert abs(number(requirement)-number(actual)-number(slack)) <= Decimal('0.002')
                current.update(actual_ns=actual, slack_ns=slack, classification='evaluated')
            # Position is source-file metadata and can shift after SDK reload.
            definitions = re.sub(r'[ \t]*\\\n[ \t]*', ' ', '\n'.join(current['definition'])).splitlines()
            assert len(definitions) == 2, 'expected separate From and To expressions'
            identity = json.dumps([*[collection_identity(x) for x in definitions],
                                   str(number(requirement).normalize())], separators=(',', ':'))
            current['identity_sha256'] = hashlib.sha256(identity.encode()).hexdigest()
            result.append(current);current = None
        else:
            assert current is not None, 'unrecognized bus report content'
            current['definition'].append(line.strip())
    assert current is None and result and len({r['id'] for r in result}) == len(result)
    assert set(detail) == {r['id'] for r in result}, 'summary/detailed constraint coverage mismatch'
    return result


def read_run(directory):
    m = json.loads((directory/'manifest.json').read_text())
    assert m['status'] == 'reports_generated' and m['returncode'] == 0 and m['inputs_unchanged']
    for name, digest in m['artifacts'].items():
        assert sha256(directory/name) == digest, name
    for path, digest in m['inputs'].items():
        assert sha256(path) == digest, path
    reports = directory/'reports'
    assert (reports/'completed.txt').read_text() == 'queries_failed=0\nroutes_changed=false\n'
    names = dict((int(i), name) for i, name in (line.split('\t') for line in (directory/'nets.tsv').read_text().splitlines()))
    targets = dict((r[0], r[1:]) for r in (line.split('\t') for line in (directory/'targets.tsv').read_text().splitlines()))
    status = rows(reports/'query_status.tsv')
    expected = {('net', str(n)+'_'+mode) for n in names for mode in ('total', 'interconnect')} | {('path', name+'_'+kind) for name in targets for kind in ('min', 'max')}
    assert len(status) == len(expected) and {(r['kind'], r['id']) for r in status} == expected
    assert all(r['status'] == 'resolved' and int(r['object_count']) > 0 for r in status)
    assert all(int(r['object_count']) == 1 for r in status if r['kind'] == 'path')
    objects = defaultdict(dict)
    for r in rows(reports/'net_delays.tsv'):
        n = int(r['net_id']);assert names[n] == r['net_name'] and r['mode'] in ('total', 'interconnect')
        key = (n, r['mode'], int(r['object_index']));assert r['property'] not in objects[key]
        objects[key][r['property']] = r['value']
    delays = {};indices = defaultdict(list)
    for (n, mode, index), props in objects.items():
        key = (n, mode, props['TO_PIN']);assert key not in delays
        delays[key] = checked_delays(props, names[n]);indices[(n, mode)].append(index)
    assert {(n, pin) for n, mode, pin in delays if mode == 'total'} == {(n, pin) for n, mode, pin in delays if mode == 'interconnect'}
    for (n, mode, pin), delay in delays.items():
        if mode == 'total':
            assert all(number(value) >= number(delays[n, 'interconnect', pin][corner]) for corner, value in delay.items())
    assert set(indices) == {(n, mode) for n in names for mode in ('total', 'interconnect')}
    for r in status:
        if r['kind'] == 'net':
            n, mode = r['id'].split('_', 1)
            assert sorted(indices[(int(n), mode)]) == list(range(int(r['object_count'])))
    paths = {}
    for name, (src, dst) in targets.items():
        for kind in ('min', 'max'):
            pr = rows(reports/('target_'+name+'_'+kind+'.tsv'))
            props = {r['property']: r['value'] for r in pr};assert len(props) == len(pr)
            assert props['STARTPOINT_PIN'] == src and props['ENDPOINT_PIN'] == dst and props['DELAY_TYPE'] == kind
            paths[name+'_'+kind] = {k: props[k] for k in ('STARTPOINT_PIN', 'ENDPOINT_PIN', 'DELAY_TYPE', 'CORNER', 'SLACK', 'DATAPATH_DELAY', 'DATAPATH_LOGIC_DELAY', 'DATAPATH_NET_DELAY', 'REQUIRED_TIME', 'REQUIREMENT', 'STARTPOINT_CLOCK_DELAY', 'ENDPOINT_CLOCK_DELAY')}
            for prop, value in paths[name+'_'+kind].items():
                if prop not in ('STARTPOINT_PIN', 'ENDPOINT_PIN', 'DELAY_TYPE', 'CORNER'):
                    number(value)
    bus = bus_rows((reports/'bus_skew_summary.rpt').read_text(), (reports/'bus_skew_paths.rpt').read_text())
    return m, names, targets, bus, delays, paths


def main():
    if not __debug__:
        raise RuntimeError('audit requires assertions')
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('original', 'routed', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    old = read_run(a.original.resolve());new = read_run(a.routed.resolve())
    assert old[1] == new[1] and old[2] == new[2]
    assert old[0]['artifacts']['check_native_timing.tcl'] == new[0]['artifacts']['check_native_timing.tcl']
    out = a.output.resolve();out.mkdir(parents=True, exist_ok=False)
    shutil.copy2(__file__, out/'auditor.py')
    oldbus, newbus = old[3], new[3]
    bus_result = bus_comparison(oldbus, newbus)
    assert old[4].keys() == new[4].keys(), 'changed native logical-pin delay coverage'
    deltas = [];stats = {}
    for key in sorted(old[4]):
        n, mode, pin = key
        row = dict(net_id=n, net_name=old[1][n], mode=mode, to_pin=pin)
        for corner in old[4][key]:
            before, after = number(old[4][key][corner]), number(new[4][key][corner])
            row[corner+'_before_ps'] = str(before);row[corner+'_after_ps'] = str(after);row[corner+'_delta_ps'] = str(after-before)
        deltas.append(row)
    with (out/'net_delay_deltas.csv').open('w') as f:
        w = csv.DictWriter(f, fieldnames=list(deltas[0]));w.writeheader();w.writerows(deltas)
    for mode in ('total', 'interconnect'):
        stats[mode] = {}
        for corner in ('FAST_MIN', 'FAST_MAX', 'SLOW_MIN', 'SLOW_MAX'):
            values = [number(r[corner+'_delta_ps']) for r in deltas if r['mode'] == mode]
            stats[mode][corner] = dict(decreased=sum(x<0 for x in values), increased=sum(x>0 for x in values), unchanged=sum(x==0 for x in values), min_delta_ps=str(min(values)), max_delta_ps=str(max(values)))
    for name, bus in (('original', oldbus), ('routed', newbus)):
        (out/(name+'_bus_rows.json')).write_text(json.dumps(bus, indent=2)+'\n')
    result = dict(schema='dieroute.native_extended_timing_audit.v1',
                  status='passed' if bus_result['all_coverage_and_reported_values_equal'] and bus_result['violations'] == 0 else 'bus_skew_gate_failed',
                  manifests={str(d.resolve()/'manifest.json'): sha256(d/'manifest.json') for d in (a.original, a.routed)},
                  auditor_sha256=sha256(out/'auditor.py'),
                  constraint_identity='direction-preserving literal get_cells member multiset; exact text for other expressions; normalized numeric requirement; source position excluded',
                  bus_skew=bus_result,
                  selected_nets=len(old[1]), logical_load_pins_per_mode=len(deltas)//2, native_delay_objects=len(deltas),
                  estimated_delays_accepted=False, net_delay_units='ps', timing_path_units='ns',
                  net_delay_changes=stats, targeted_paths=dict(original=old[5], routed=new[5]),
                  board_result=False, changes_routes=False,
                  scope='Native min/max net delays at both process corners and whole-design bus skew, plus paired setup/hold timing of two explicitly selected paths',
                  limits=['Logical load-pin delays are not yet mapped one-to-one to physical site-pin ConnectionTasks.',
                          'Native route net delays depend on route, fanout and corner; they are not a static per-PIP additive model.',
                          'No bitstream acceptance, joint physical wirelength/CPD proof or board performance claim.'])
    (out/'audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'targeted_paths'}))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
