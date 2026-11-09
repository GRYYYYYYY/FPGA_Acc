#!/usr/bin/env python3
"""Serialize and independently check one private FP candidate with native VPR."""
import argparse
import csv
from collections import defaultdict
import json
import re
import hashlib
import os
from pathlib import Path
import sys
import subprocess
import time
import rr_export_cache

from prepare_vpr_bundle import sha, tp, writer, PROJECTS
import validate_vpr_route as native


def read_state(path):
    words = iter(path.read_text().split())
    if next(words) != 'FUSIONPAR_STATE_V1':
        raise ValueError('unsupported candidate schema')
    def number():
        value = int(next(words))
        if value < 0:
            raise ValueError('negative state value')
        return value
    placement = []
    for i in range(number()):
        if number() != i:
            raise ValueError('placement ID order mismatch')
        placement.append((number(), number()))
    routes = []
    for i in range(number()):
        if number() != i:
            raise ValueError('connection ID order mismatch')
        source, sink, version = number(), number(), number()
        routes.append({'source': source, 'sink': sink, 'version': version, 'path': [number() for _ in range(number())]})
    resources = [[number() for _ in range(6)] for _ in range(number())]
    revision, epoch, basis = number(), number(), number()
    criticalities = [number() for _ in range(number())]
    site_versions = [number() for _ in range(number())]
    if list(words):
        raise ValueError('trailing state data')
    return placement, routes, resources, (revision, epoch, basis), criticalities, site_versions


def physical_digest(state):
    placement, routes, resources, _, _, _ = state
    payload = {'placement': [p[0] for p in placement],
               'routes': [{k: r[k] for k in ('source', 'sink', 'path')} for r in routes],
               'resources': [r[:3] for r in resources]}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class CostProfile:
    def __init__(self):
        self.start = self.previous = time.perf_counter_ns()
        self.phases = []

    def mark(self, name):
        now = time.perf_counter_ns()
        self.phases.append({'phase': name, 'wall_ns': now - self.previous})
        self.previous = now


def validate(bundle, state_path, work):
    profile = CostProfile()
    complete = False
    try:
        result = validate_profiled(bundle, state_path, work, profile)
        complete = True
        return result
    finally:
        profile.mark('tail_or_failure')
        report = {'schema': 'FUSIONPAR_VALIDATION_COST_V1', 'complete': complete,
                  'phases': profile.phases, 'total_ns': profile.previous - profile.start,
                  'limits': ['Contiguous non-overlapping Python validation-body wall intervals',
                             'Native check includes upstream wrapper setup, VPR and its own hashes',
                             'Timing export includes wrapper setup, VPR, parsing and bridge output',
                             'Excludes Python startup/imports, host state serialization, cost-report write and CLI stdout',
                             'Failure tail contains the unfinished phase; do not compare it as a successful phase']}
        (work/'costs.json').write_text(json.dumps(report, indent=2)+'\n')


def validate_profiled(bundle, state_path, work, profile):
    manifest = json.loads((bundle / 'manifest.json').read_text())
    if manifest['schema'] != 'FUSIONPAR_VPR_BUNDLE_V1':
        raise ValueError('bundle schema mismatch')
    profile.mark('manifest_read')
    bindings = list(manifest['inputs'].values()) + manifest['sources'] + list(manifest['files'].values())
    for entry in bindings:
        if sha(entry['path']) != entry['sha256']:
            raise ValueError('changed bound input/source: ' + entry['path'])
    rr_export = manifest.get('rr_export', {'backend': 'xml'})
    if rr_export['backend'] == 'sqlite':
        cache_binding = manifest['files']['rr_export.sqlite']
        if Path(cache_binding['path']).resolve() != (bundle/'rr_export.sqlite').resolve():
            raise ValueError('RR cache file binding points outside bundle')
        expected = rr_export['metadata']['bindings']
        identities = {'rr_graph': manifest['inputs']['graph']['sha256'],
                      'csr_nodes': manifest['files']['graph.nodes']['sha256'],
                      'csr_edges': manifest['files']['graph.edges']['sha256'],
                      'native_reader': sha(writer.__file__), 'cache_implementation': sha(rr_export_cache.__file__)}
        if set(expected) != set(identities) or any(expected[k]['sha256'] != v for k, v in identities.items()):
            raise ValueError('RR cache is bound to a different graph/implementation')
    elif rr_export['backend'] != 'xml':
        raise ValueError('unsupported RR export backend')
    profile.mark('bindings_before')
    before_state = sha(state_path)
    state = read_state(state_path)
    placement, routes, resources, _, _, _ = state
    if len(placement) != len(manifest['blocks']) or len(routes) != len(manifest['connections']):
        raise ValueError('candidate object count mismatch')
    profile.mark('candidate_read')
    paths = {k: Path(v['path']) for k, v in manifest['inputs'].items()}
    place = work / 'candidate.place'
    baseline_lines = paths['place'].read_text().splitlines()
    lines = baseline_lines[:5]
    # Native validation copies the netlist into its private directory and uses
    # its basename. Match VPR print_place before computing Placement_ID, even
    # when the imported placer wrote an absolute Netlist_File path.
    lines[0] = f"Netlist_File: {paths['net'].name} Netlist_ID: SHA256:{sha(paths['net'])}"
    for block, (site_id, _) in zip(manifest['blocks'], placement):
        site = manifest['sites'][site_id]
        name = block['name']
        padding = '\t\t' if len(name.encode('utf-8')) < 8 else '\t'
        lines.append(f"{name}{padding}{site['x']}\t{site['y']}\t{site['subtile']}\t{site['layer']}\t#{block['block_id']}")
    place.write_text('\n'.join(lines) + '\n')
    place_check = tp.validate_contract(bundle / 'placement_contract', place)
    profile.mark('placement_export_and_contract_check')
    original = writer.parse_original(paths['route'])
    lines, prefix_end, sections, original_nets, templates, pin_templates, dimensions = original
    net_edges = defaultdict(set)
    connections = defaultdict(list)
    net_sources = {}
    owners = defaultdict(set)
    for metadata, route in zip(manifest['connections'], routes):
        net = metadata['net']
        if not route['path'] or route['path'][-1] != route['sink']:
            raise ValueError('missing sink in candidate')
        if net in net_sources and net_sources[net] != route['source']:
            raise ValueError('inconsistent source')
        net_sources[net] = route['source']
        current = route['source']
        for node in route['path']:
            net_edges[net].add((current, node))
            owners[node].add(net)
            current = node
        connections[net].append({'source': route['source'], 'sink': route['sink'], 'net_pin_index': metadata['net_pin_index']})
    for node, resource in enumerate(resources):
        use = owners[node]
        if resource[0] != len(use) or resource[0] > resource[1] or resource[2] != (next(iter(use)) if len(use) == 1 else 0xffffffff):
            raise ValueError('independent resource accounting mismatch')
    if any(node >= len(resources) for node in owners):
        raise ValueError('resource outside state')
    edges = {edge for rows in net_edges.values() for edge in rows}
    nodes_used = {n for edge in edges for n in edge}
    profile.mark('route_decode_and_accounting')
    if rr_export['backend'] == 'sqlite':
        nodes, switches, ambiguous = rr_export_cache.load(bundle/'rr_export.sqlite', rr_export['metadata'],
                                                         nodes_used, edges, writer.Node)
    else:
        nodes, switches, ambiguous = writer.load_rr_graph(paths['graph'], nodes_used, edges)
    if ambiguous:
        raise ValueError('ambiguous physical switch identity')
    profile.mark('rr_metadata_lookup' if rr_export['backend'] == 'sqlite' else 'rr_graph_decode')
    # Learn actual I/O physical types from native Pad descriptions. VPR rejects
    # logical pb-pin names on I/O nodes; the upstream fixed-endpoint serializer
    # can add such a name when a move reaches a previously unused I/O node.
    # Use the physical type, not a chip-boundary heuristic or a hardcoded name.
    site_types = {(s['x'], s['y'], s['layer']): s['physical_type'] for s in manifest['sites']}
    io_types = set()
    for prefix in templates.values():
        if not re.search(r'\bPad:', prefix):
            continue
        match = re.search(r'\((\d+),\s*(\d+)(?:,\s*(\d+))?\)', prefix)
        if not match:
            raise ValueError('native Pad template lacks coordinates')
        coordinate = (int(match[1]), int(match[2]), int(match[3] or 0))
        if coordinate not in site_types:
            raise ValueError('native Pad template has no physical site type')
        io_types.add(site_types[coordinate])
    # Also add explicit class descriptions for moved non-I/O SOURCE/SINK nodes.
    for nid, node in nodes.items():
        if node.kind in ('SOURCE', 'SINK', 'IPIN', 'OPIN') and site_types.get((node.xlow, node.ylow, node.layer)) in io_types:
            templates[nid] = f'Node: {nid} {node.kind} ({node.xlow},{node.ylow},{node.layer}) Pad: {node.ptc} Switch:'
        elif node.kind in ('SOURCE', 'SINK'):
            templates[nid] = f'Node: {nid} {node.kind} ({node.xlow},{node.ylow},{node.layer}) Class: {node.ptc} Switch:'
    generated = {}
    for net, rows in connections.items():
        generated[net] = writer.serialize_net(net, original_nets[net]['name'], net_sources[net],
            sorted(net_edges[net]), rows, nodes, switches, templates, pin_templates, dimensions)
    out = lines[:prefix_end]
    out[0] = f'Placement_File: candidate.place Placement_ID: SHA256:{sha(place)}'
    for _, _, match, section in sections:
        net = int(match.group(1)) if match else None
        out.extend(generated.get(net, section))
    route_path = work / 'candidate.route'
    route_path.write_text('\n'.join(out).rstrip() + '\n')
    args = argparse.Namespace(vpr=paths['vpr'], arch=paths['arch'], circuit=paths['circuit'], sdc=None,
        net=paths['net'], place=place, route=route_path, rr_graph=paths['graph'],
        channel_width=manifest['channel_width'], work_dir=work/'native', report=work/'native.json',
        baseline_wirelength=None, baseline_cpd_ns=None)
    profile.mark('route_export')
    result = native.validate(args)
    if sha(args.work_dir / place.name) != sha(place):
        raise ValueError('native loader changed serialized placement identity')
    profile.mark('native_check')
    timing_report = None
    if 'timing_vpr' in paths:
        timing_input, timing_output = work/'timing.input.csv', work/'timing.output.csv'
        with timing_input.open('w', newline='') as stream:
            csv_writer = csv.writer(stream)
            csv_writer.writerow(('iteration', 'task_id', 'net_id', 'source', 'sink', 'routed', 'delay_ps', 'criticality_q'))
            for metadata, route in zip(manifest['connections'], routes):
                # routed=0 retains the loaded native RC tree delay.
                csv_writer.writerow((0xffffffff, metadata['id'], metadata['net'], route['source'], route['sink'], 0, 0, 0))
        env = {k: v for k, v in os.environ.items() if not k.startswith('PERSISTROUTE_')}
        for key, path in {'BIN': paths['timing_vpr'], 'ARCH': paths['arch'], 'CIRCUIT': paths['circuit'],
                          'NET': paths['net'], 'PLACE': place, 'ROUTE': route_path, 'RR_GRAPH': paths['graph']}.items():
            env['PERSISTROUTE_VPR_' + key] = str(path.resolve())
        env['PERSISTROUTE_VPR_CHAN_WIDTH'] = str(manifest['channel_width'])
        command = [sys.executable, str(PROJECTS/'persistroute/tools/vpr_timing_analyzer.py'), '0', str(timing_input), str(timing_output)]
        completed = subprocess.run(command, env=env, capture_output=True, text=True)
        (work/'timing.stdout.log').write_text(completed.stdout)
        (work/'timing.stderr.log').write_text(completed.stderr)
        if completed.returncode:
            raise RuntimeError('native timing exporter failed')
        with timing_output.open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        by_id = {int(row['task_id']): row for row in rows}
        if len(rows) != len(routes) or len(by_id) != len(rows) or set(by_id) != set(range(len(routes))):
            raise ValueError('incomplete/duplicate timing connection coverage')
        criticalities = [int(by_id[i]['criticality_q']) for i in range(len(routes))]
        if any(q < 0 or q > 65535 for q in criticalities):
            raise ValueError('invalid timing criticality range')
        cpd = {int(row['critical_path_delay_ps']) for row in rows}
        if len(cpd) != 1 or abs(next(iter(cpd)) - result['critical_path_delay_ns']*1000) > 1.0:
            raise ValueError('timing exporter CPD differs from independent native STA')
        (work/'timing.txt').write_text(str(len(criticalities))+' '+' '.join(map(str, criticalities))+'\n')
        delays = [int(by_id[i]['delay_ps']) for i in range(len(routes))]
        if any(delay < 0 or delay >= 2**64 for delay in delays):
            raise ValueError('native connection delay out of range')
        (work/'connection_delays.txt').write_text(str(len(delays))+' '+' '.join(map(str, delays))+'\n')
        timing_report = {'input_sha256': sha(timing_input), 'output_sha256': sha(timing_output),
                         'delays_path': str(work/'connection_delays.txt'),
                         'delays_sha256': sha(work/'connection_delays.txt'),
                         'criticalities_path': str(work/'timing.txt'),
                         'criticalities_sha256': sha(work/'timing.txt'), 'connections': len(rows),
                         'unmapped_connections': sum(int(row.get('timing_pin_mapped', '1')) == 0 for row in rows),
                         'cpd_ps': next(iter(cpd)), 'command': command}
    profile.mark('timing_export')
    for entry in bindings:
        if sha(entry['path']) != entry['sha256']:
            raise ValueError('input/source changed during validation')
    if sha(state_path) != before_state:
        raise ValueError('private candidate changed during validation')
    profile.mark('bindings_after')
    report = {'schema': 'FUSIONPAR_NATIVE_GATE_V1', 'legal': result['legal'],
              'rr_export_backend': rr_export['backend'],
              'placement': place_check, 'candidate_sha256': before_state,
              'physical_state_sha256': physical_digest(state), 'timing': timing_report,
              'bundle_manifest_sha256': sha(bundle/'manifest.json'),
              'native_report_sha256': sha(work/'native.json'),
              'cpd_ns': result['critical_path_delay_ns'], 'wirelength': result['total_wirelength']}
    (work/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
    # Narrow machine-readable bridge for the C++ acceptance policy. The complete
    # independent native report remains archived alongside it.
    (work/'quality.txt').write_text(f"{report['cpd_ns']:.12g} {report['wirelength']}\n")
    profile.mark('certificate_and_bridge_write')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('bundle', type=Path)
    p.add_argument('state', type=Path)
    p.add_argument('work', type=Path)
    a = p.parse_args()
    print(json.dumps(validate(a.bundle, a.state, a.work), indent=2))
