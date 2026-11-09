#!/usr/bin/env python3
"""Reconstruct existing site connectivity and bind native delays to physical tasks."""
import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import shutil
import struct
from audit_native_timing import rows, read_run, number
from run_native_case import sha256


class SiteConnectivity:
    """Trace only exported, already-used wires/PIPs; never choose a new route."""
    def __init__(self, wires, pips):
        self.pins = {};self.drivers = defaultdict(list);self.pips = {}
        for r in wires:
            key = (int(r['net_id']), r['site_inst'], r['bel'], r['pin'])
            assert key not in self.pins, 'duplicate BEL pin'
            assert r['direction'] in ('INPUT', 'OUTPUT'), 'bidirectional site pin unsupported'
            self.pins[key] = r
            if r['direction'] == 'OUTPUT':
                self.drivers[key[:2]+(r['wire'],)].append(r)
        for r in pips:
            prefix = (int(r['net_id']), r['site_inst'])
            source = prefix+(r['bel'], r['input_pin'])
            target = prefix+(r['bel'], r['output_pin'])
            assert self.pins[source]['direction'] == 'INPUT' and self.pins[target]['direction'] == 'OUTPUT'
            assert self.pins[source]['wire'] == r['input_wire'] and self.pins[target]['wire'] == r['output_wire']
            assert self.pins[source]['bel_class'] == self.pins[target]['bel_class'] == 'RBEL'
            assert target not in self.pips, 'multiple enabled site PIPs for one mux output'
            self.pips[target] = source

    def trace(self, net, site, wire):
        prefix = (net, site);seen = set();proof = []
        while True:
            assert wire not in seen, 'cycle in used site connectivity'
            seen.add(wire)
            drivers = self.drivers[prefix+(wire,)]
            assert len(drivers) == 1, 'missing/ambiguous site-wire driver'
            r = drivers[0];key = prefix+(r['bel'], r['pin'])
            proof.append(dict(wire=wire, bel=r['bel'], pin=r['pin'], bel_class=r['bel_class']))
            if r['site_port'] == 'true':
                assert r['bel_class'] == 'PORT'
                return 'site_input', r['pin'], proof
            if r['bel_class'] == 'RBEL':
                assert key in self.pips, 'unselected site mux'
                source = self.pins[self.pips[key]];wire = source['wire']
                continue
            assert r['bel_class'] == 'BEL' and r['cell'] and r['logical_pin'] and r['routethru'] == 'false', 'unsupported internal driver'
            return 'internal_driver', (r['cell'], r['logical_pin']), proof


def verified(directory):
    m = json.loads((directory/'manifest.json').read_text())
    assert m['status'] == 'passed' and m['inputs_unchanged']
    for path, digest in m['inputs'].items():
        assert sha256(path) == digest, path
    for name, digest in m['artifacts'].items():
        assert sha256(directory/name) == digest, name
    return m


def main():
    if not __debug__:
        raise RuntimeError('verification requires assertions')
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('pin-run', 'cohort-run', 'writeback-run', 'original', 'routed', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    pin = a.pin_run.resolve();cohort = a.cohort_run.resolve();writeback = a.writeback_run.resolve()
    pm = verified(pin);wm = verified(writeback)
    cm = json.loads((cohort/'manifest.json').read_text())
    assert cm['status'] == 'passed' and cm['inputs_unchanged'] and cm['electrical_model_converged']
    for m in (pm, wm):
        assert m['inputs'][str(cohort/'manifest.json')] == sha256(cohort/'manifest.json')
    old = read_run(a.original.resolve());new = read_run(a.routed.resolve())
    assert old[1] == new[1] and old[4].keys() == new[4].keys()
    assert pm['inputs'][str(a.original.resolve()/'manifest.json')] == sha256(a.original/'manifest.json')
    assert new[0]['inputs'][str(writeback/'write/routed.dcp')] == wm['artifacts']['write/routed.dcp']
    # Site wires, BEL pin maps and physical pins were fingerprinted before/after
    # writeback and again after reloading its serialized DCP.
    before = (writeback/'write/before.txt').read_text().splitlines()
    after = (writeback/'write/expected.txt').read_text().splitlines()
    assert before[:9] == after[:9] and after == (writeback/'reload/snapshot.txt').read_text().splitlines()
    assert wm['physical_reload_equal'] and wm['sdk_unchanged']
    data = pin/'pins';logical = rows(data/'logical_pins.tsv');sdk = rows(data/'sdk_site_pins.tsv')
    sitepins = rows(data/'net_site_pins.tsv');wires = rows(data/'site_wires.tsv');pips = rows(data/'site_pips.tsv')
    graph = SiteConnectivity(wires, pips)
    expected = {(n, to) for n, mode, to in old[4] if mode == 'total'}
    assert {(int(r['net_id']), r['to_pin']) for r in logical} == expected
    assert all(old[1][int(r['net_id'])] == r['net_name'] for r in logical)
    physical = {}
    for r in sitepins:
        key = (int(r['net_id']), r['site_inst'], r['pin'])
        assert key not in physical;physical[key] = r
    prepared = set()
    for line in (writeback/'pins.tsv').read_text().splitlines():
        n, site, sp, output, tile, wire = line.split('\t')
        prepared.add((int(n), site, sp, output, tile, wire))
    assert prepared == {(n, si, sp, r['output'], r['tile'], r['wire']) for (n, si, sp), r in physical.items()}
    footprint = Path(cm['command'][3]);selection = list(csv.DictReader((cohort/'route/selection.csv').open()))
    assert sha256(cohort/'route/selection.csv') == cm['artifacts']['route/selection.csv']
    task_pins = {}
    with (footprint/'tasks.bin').open('rb') as f:
        for r in selection:
            tid = int(r['task']);f.seek(tid*32);record = struct.unpack('<8I', f.read(32))
            assert record[0] == tid and record[1] == int(r['net'])
            assert record[7] not in task_pins;task_pins[record[7]] = (tid, record[1], record[3])
    task_by_pin = {}
    for r in csv.DictReader((footprint/'pins.csv').open()):
        pid = int(r['id'])
        if pid not in task_pins:
            continue
        tid, n, node = task_pins[pid]
        assert int(r['net_id']) == n and int(r['node_id']) == node and r['output'] == 'false'
        key = (n, r['site_inst'], r['pin']);assert key not in task_by_pin
        assert physical[key]['site'] == r['site'];task_by_pin[key] = tid
    assert set(task_by_pin) == {k for k, r in physical.items() if r['output'] == 'false'}
    assert len(task_by_pin) == len(selection)
    sdk_keys = defaultdict(set)
    for r in sdk:
        key = (int(r['net_id']), r['to_pin'], r['physical_pin'])
        sp = physical[(key[0], r['site_inst'], r['site_pin'])]
        assert (r['tile'], r['wire']) == (sp['tile'], sp['wire']) and sp['output'] == 'false'
        assert (r['site_inst'], r['site_pin']) not in sdk_keys[key]
        sdk_keys[key].add((r['site_inst'], r['site_pin']))
    mappings = [];keys = set();delay_rows = []
    for r in logical:
        n = int(r['net_id']);site = r['site_inst'];key = (n, r['to_pin'], r['physical_pin'])
        assert key not in keys;keys.add(key)
        bp = graph.pins[(n, site, r['bel'], r['physical_pin'])]
        assert (bp['wire'], bp['cell'], bp['logical_pin'], bp['direction']) == (r['wire'], r['cell'], r['logical_pin'], 'INPUT')
        kind, terminal, proof = graph.trace(n, site, r['wire'])
        task = None
        if kind == 'site_input':
            assert sdk_keys[key] == {(site, terminal)}, 'SDK/independent site-pin mismatch'
            task = task_by_pin[n, site, terminal]
        else:
            assert not sdk_keys[key], 'intrasite load mapped to intersite input by SDK'
            sources = [sp for (sn, ss, _), sp in physical.items() if (sn, ss) == (n, site) and sp['output'] == 'true']
            assert len(sources) == 1, 'internal driver lacks matching source site pin'
            ports = [bp for k, bp in graph.pins.items() if k[:2] == (n, site) and bp['site_port'] == 'true' and bp['pin'] == sources[0]['pin']]
            assert len(ports) == 1 and ports[0]['direction'] == 'INPUT'
            source_kind, source_driver, source_proof = graph.trace(n, site, ports[0]['wire'])
            assert source_kind == 'internal_driver' and source_driver == terminal, 'internal load is not driven by net source'
            proof.append(dict(source_site_pin=sources[0]['pin'], source_proof=source_proof))
        mappings.append(dict(net_id=n, to_pin=r['to_pin'], physical_pin=r['physical_pin'], site_inst=site,
                             classification=kind, terminal=terminal, task=task, proof=proof))
        dr = dict(net_id=n, net_name=r['net_name'], to_pin=r['to_pin'], physical_pin=r['physical_pin'],
                  task='' if task is None else task, classification=kind)
        for corner in old[4][n, 'total', r['to_pin']]:
            before = old[4][n, 'total', r['to_pin']][corner];after = new[4][n, 'total', r['to_pin']][corner]
            dr[corner+'_before_ps']=before;dr[corner+'_after_ps']=after;dr[corner+'_delta_ps']=str(number(after)-number(before))
        delay_rows.append(dr)
    assert set(sdk_keys) <= keys, 'orphan SDK mapping'
    mapped_tasks = Counter(m['task'] for m in mappings if m['task'] is not None)
    assert set(mapped_tasks) == set(task_by_pin.values()), 'physical tasks missing logical delay coverage'
    out = a.output.resolve();out.mkdir(parents=True, exist_ok=False)
    shutil.copy2(__file__, out/'auditor.py')
    (out/'mapping.json').write_text(json.dumps(mappings, indent=2)+'\n')
    with (out/'task_delay_observations.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(delay_rows[0]));writer.writeheader();writer.writerows(delay_rows)
    result = dict(schema='dieroute.native_timing_pin_audit.v1', passed=True, logical_loads=len(expected),
                  physical_bel_loads=len(logical), mapped_logical_loads=sum(m['task'] is not None for m in mappings),
                  site_local_loads=sum(m['task'] is None for m in mappings), physical_tasks=len(mapped_tasks),
                  logical_loads_per_task_histogram=dict(sorted(Counter(mapped_tasks.values()).items())),
                  all_task_delays_covered=True, sdk_matches_independent_used_site_connectivity=True,
                  original_to_routed_site_state_unchanged=True, changes_routes=False, board_result=False,
                  manifests={str(d.resolve()/'manifest.json'):sha256(d/'manifest.json') for d in (pin,cohort,writeback,a.original,a.routed)},
                  artifacts={f.name:sha256(f) for f in out.iterdir() if f.is_file()},
                  scope='Existing directed site connectivity to exact physical task IDs; paired four-corner total net delay observations',
                  limits=['Per-load total delays include site portions and cannot be substituted for static additive PIP delays.',
                          'Clock/skew and full-path slack are separate from net delay; no timing acceptance or hardware claim.'])
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__ == '__main__':
    main()
