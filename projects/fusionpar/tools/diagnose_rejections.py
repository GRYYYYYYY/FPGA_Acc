#!/usr/bin/env python3
"""Attribute archived native rejection costs without rerunning or selecting moves."""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import struct

from prepare_vpr_bundle import sha
from validate_candidate import read_state


def diagnose(suite, run):
    manifest_path = suite/'bundle/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    metadata = manifest['connections']
    nodes_path = suite/'bundle/graph.nodes'
    lengths = [entry[2] for entry in struct.iter_unpack('<IHH', nodes_path.read_bytes())]
    directory = suite/run
    initial_path = directory/'validation_0/candidate.state'
    initial = read_state(initial_path)
    bindings = [manifest_path, nodes_path, initial_path]
    def timing(path):
        bindings.append(path)
        with path.open(newline='') as f:
            rows = list(csv.DictReader(f))
        result = {int(row['task_id']): {key: int(value) for key, value in row.items()} for row in rows}
        if len(result) != len(rows) or set(result) != set(range(len(metadata))):
            raise ValueError('incomplete or duplicate timing rows')
        return result
    old_timing = timing(directory/'validation_0/timing.output.csv')
    def net_wires(state):
        resources = defaultdict(set)
        for c, route in zip(metadata, state[1]):
            resources[c['net']].update(route['path'])
        return {net: sum(lengths[n] for n in used) for net, used in resources.items()}
    def hpwl(state):
        instances = defaultdict(set)
        for c in metadata:
            instances[c['net']].update((c['source_instance'], c['sink_instance']))
        total = 0
        for members in instances.values():
            sites = [manifest['sites'][state[0][i][0]] for i in members]
            total += max(s['x'] for s in sites)-min(s['x'] for s in sites)
            total += max(s['y'] for s in sites)-min(s['y'] for s in sites)
        return total
    old_wire = net_wires(initial)
    initial_report_path = directory/'validation_0/validation.json'
    bindings.append(initial_report_path)
    baseline = json.loads(initial_report_path.read_text())
    if sum(old_wire.values()) != baseline['wirelength']:
        raise ValueError('initial unique-net RR length differs from native WL')
    reports = []
    for path in sorted(directory.glob('validation_*/validation.json'), key=lambda p: int(p.parent.name.split('_')[-1])):
        if path == initial_report_path:
            continue
        bindings += [path, path.parent/'candidate.state']
        candidate = read_state(path.parent/'candidate.state')
        quality = json.loads(path.read_text())
        now = timing(path.parent/'timing.output.csv')
        wire = net_wires(candidate)
        if sum(wire.values()) != quality['wirelength']:
            raise ValueError('candidate unique-net RR length differs from native WL')
        moved = [i for i, (a, b) in enumerate(zip(initial[0], candidate[0])) if a[0] != b[0]]
        groups = defaultdict(lambda: {'connections': 0, 'delay_increased': 0, 'delay_decreased': 0,
                                      'positive_delay_ps': 0, 'negative_delay_ps': 0,
                                      'connection_path_wire_delta': 0})
        nets = {}
        worst = []
        for i, (c, a, b) in enumerate(zip(metadata, initial[1], candidate[1])):
            if a['version'] == b['version']:
                continue
            key = ('source_changed' if a['source'] != b['source'] else
                   'sink_only_changed' if a['sink'] != b['sink'] else
                   'unchanged_endpoints_path_changed' if a['path'] != b['path'] else 'unchanged_endpoints_same_path')
            change = now[i]['delay_ps']-old_timing[i]['delay_ps']
            item = groups[key]
            item['connections'] += 1
            item['delay_increased'] += change > 0
            item['delay_decreased'] += change < 0
            item['positive_delay_ps'] += max(change, 0)
            item['negative_delay_ps'] += min(change, 0)
            item['connection_path_wire_delta'] += sum(lengths[n] for n in b['path'])-sum(lengths[n] for n in a['path'])
            net = c['net']
            entry = nets.setdefault(net, {'net': net, 'name': c['net_name'], 'wire_before': old_wire[net],
                'wire_after': wire[net], 'wire_delta': wire[net]-old_wire[net], 'connections': 0,
                'endpoint_changed': 0, 'max_native_delay_delta_ps': change})
            entry['connections'] += 1
            entry['endpoint_changed'] += (a['source'], a['sink']) != (b['source'], b['sink'])
            entry['max_native_delay_delta_ps'] = max(entry['max_native_delay_delta_ps'], change)
            if change > 0:
                worst.append({'connection': i, 'net': net, 'group': key,
                              'criticality_q_before': old_timing[i]['criticality_q'],
                              'native_delay_delta_ps': change})
        reports.append({'candidate': str(path.parent), 'moved_instances': moved,
                        'hpwl_delta': hpwl(candidate)-hpwl(initial),
                        'native_WL_delta': quality['wirelength']-baseline['wirelength'],
                        'native_CPD_delta_ns': quality['cpd_ns']-baseline['cpd_ns'],
                        'groups': dict(groups), 'rerouted_nets': len(nets),
                        'positive_net_WL_delta_sum': sum(max(n['wire_delta'], 0) for n in nets.values()),
                        'negative_net_WL_delta_sum': sum(min(n['wire_delta'], 0) for n in nets.values()),
                        'largest_WL_increases': sorted(nets.values(), key=lambda n: (-n['wire_delta'], n['net']))[:10],
                        'critical_delay_increases': sorted(worst, key=lambda n: (-n['criticality_q_before'], -n['native_delay_delta_ps'], n['connection']))[:10]})
    return {'schema': 'FUSIONPAR_REJECTION_ATTRIBUTION_V1', 'suite': str(suite), 'run': run,
            'baseline': {'wirelength': baseline['wirelength'], 'cpd_ns': baseline['cpd_ns']},
            'candidates': reports, 'sources': [{'path': str(p), 'sha256': sha(p)} for p in sorted(set(bindings))],
            'analyzer_sha256': sha(Path(__file__)),
            'limits': ['descriptive attribution, not causal ablation',
                       'per-connection wire/delay sums double-count shared prefixes and are not net WL or CPD',
                       'same-path delay may change through another branch of its net tree',
                       'archived development candidates; no new validation-set performance claim']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('suite', type=Path)
    p.add_argument('--run', default='interleaved_0')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = diagnose(a.suite.resolve(), a.run)
    a.output.write_text(json.dumps(result, indent=2)+'\n')
    for row in result['candidates']:
        print(json.dumps({k: row[k] for k in ('candidate', 'hpwl_delta', 'native_WL_delta', 'native_CPD_delta_ns', 'groups')}))
