#!/usr/bin/env python3
"""Convert a legal native VPR snapshot to the FusionPAR C++ v1 contract.

This is conversion only. Placement proposals, routing and acceptance run in C++.
Restricted to single-layer, direct logical/physical pin-name mappings supported
by the existing RouteCast extractor. Unsupported clocks/mappings fail closed.
"""
import argparse
from collections import defaultdict, deque
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import time
import rr_export_cache

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT.parent
sys.path[:0] = [str(PROJECTS / p / 'tools') for p in ('persistroute', 'tileplace', 'routecast')]
import pre_route_endpoints as endpoints
import tileplace_vpr as tp
import write_vpr_route as writer


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def binding(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha(path)}


def trace_paths(section):
    prefixes = {}
    result = []
    current = []
    for node, kind, pin in section['nodes']:
        if kind == 'SOURCE':
            if current:
                raise ValueError('repeated source in native trace')
            current = [node]
        elif node in prefixes:
            current = prefixes[node][:]
        else:
            if not current or node in current:
                raise ValueError('invalid native trace branch')
            current = current + [node]
        if node in prefixes and prefixes[node] != current:
            raise ValueError('native trace has multiple parents')
        prefixes[node] = current[:]
        if kind == 'SINK':
            if pin is None:
                raise ValueError('missing native net pin index')
            result.append((pin, current[:]))
    return result


def prepare(args):
    if args.output.exists():
        raise ValueError('output exists; use a fresh directory')
    paths = {k: binding(getattr(args, k)) for k in ('net', 'place', 'route', 'graph', 'vpr', 'arch', 'circuit')}
    if getattr(args, 'timing_vpr', None):
        paths['timing_vpr'] = binding(args.timing_vpr)
    manifest, blocks, sites, _ = tp.load_contract(args.contract)
    if manifest['inputs']['packed_netlist']['sha256'] != paths['net']['sha256']:
        raise ValueError('contract/net mismatch')
    tp.validate_contract(args.contract, args.place)
    if any(s['layer'] != 0 for s in sites):
        raise ValueError('v1 importer supports a single layer only')
    blocks.sort(key=lambda b: b['block_id'])
    if [b['block_id'] for b in blocks] != list(range(len(blocks))):
        raise ValueError('non-dense clustered block IDs')
    original = writer.parse_original(args.route)
    lines, _, _, routed, _, _, _ = original
    if f"Placement_ID: SHA256:{paths['place']['sha256']}" not in lines[0]:
        raise ValueError('native route/placement identity mismatch')
    extracted, mapping = endpoints.extract(args.net, args.place, args.graph)
    if extracted['excluded_nets']:
        raise ValueError('v1 importer does not silently omit root clock nets')
    types, grid, nodes = endpoints.physical_maps(args.graph)
    pin_keys = sorted({(blocks[p['block_id']]['logical_type'], p['port'], p['bit'], p['role']) for p in mapping['pin_details']})
    pin_id = {key: i for i, key in enumerate(pin_keys)}
    type_ids = {name: i for i, name in enumerate(sorted({s['physical_type'] for s in sites}))}
    loc_to_site = {tp.location(s): i for i, s in enumerate(sites)}
    place_rows = endpoints.placements(args.place, paths['net']['sha256'])
    source_pins = {}
    sink_pins = defaultdict(deque)
    for p in mapping['pin_details']:
        key = (blocks[p['block_id']]['logical_type'], p['port'], p['bit'], p['role'])
        record = {**p, 'pin_id': pin_id[key]}
        if p['role'] == 'SOURCE':
            source_pins[p['net']] = record
        else:
            sink_pins[p['net'], p['rr_node']].append(record)
    records = []
    routed_names = set()
    for net, section in sorted(routed.items()):
        if not section['nodes']:
            continue
        name = section['name']
        routed_names.add(name)
        if name not in source_pins:
            raise ValueError(f'routed net missing pre-route driver: {name}')
        source = source_pins[name]
        for pin_index, path in trace_paths(section):
            if path[0] != source['rr_node'] or not sink_pins[name, path[-1]]:
                raise ValueError('route/pre-route terminal mismatch')
            sink = sink_pins[name, path[-1]].popleft()
            records.append({'id': len(records), 'net': net, 'net_name': name, 'net_pin_index': pin_index,
                            'source_instance': source['block_id'], 'source_pin': source['pin_id'],
                            'sink_instance': sink['block_id'], 'sink_pin': sink['pin_id'],
                            'source': path[0], 'sink': path[-1], 'path': path[1:]})
    if any(queue for queue in sink_pins.values()) or len(records) != len(extracted['connections']):
        raise ValueError('not every pre-route connection has a native routed path')
    for record in records:
        record['priority'] = record['id']
    reference_path = getattr(args, 'priority_reference', None)
    if reference_path:
        paths['priority_reference'] = binding(reference_path)
        reference = json.loads(Path(reference_path).read_text())
        if reference['inputs']['net']['sha256'] != paths['net']['sha256']:
            raise ValueError('priority reference packed netlist differs')
        keyed = {(c['net'], c['net_pin_index']): c for c in reference['connections']}
        if len(keyed) != len(reference['connections']) or set(keyed) != {(c['net'], c['net_pin_index']) for c in records}:
            raise ValueError('priority reference connection identities differ')
        priorities = set()
        for record in records:
            old = keyed[record['net'], record['net_pin_index']]
            if any(record[k] != old[k] for k in ('net_name', 'source_instance', 'sink_instance')):
                raise ValueError('priority reference logical endpoint identity differs')
            priority = old.get('priority', old['id'])
            if not isinstance(priority, int) or not 0 <= priority < 2**32 or priority in priorities:
                raise ValueError('invalid/duplicate reference priority')
            priorities.add(priority)
            record['priority'] = priority
    args.output.mkdir(parents=True)
    graph_manifest = json.loads(args.graph_prefix.with_suffix('.manifest.json').read_text())
    if graph_manifest['schema'] != 'PERSISTROUTE_XRT_INPUT_V1' or graph_manifest['rr_graph_sha256'] != paths['graph']['sha256']:
        raise ValueError('PR graph manifest mismatch')
    for name, size in [('nodes', 8), ('edges', 8), ('resources', 16)]:
        entry = graph_manifest['files'][name]
        src = args.graph_prefix.parent / entry['path']
        if entry['record_bytes'] != size or src.stat().st_size != entry['bytes'] or sha(src) != entry['sha256']:
            raise ValueError(f'PR ABI input mismatch: {name}')
        shutil.copyfile(src, args.output / f'graph.{name}')
    with (args.output / 'design.txt').open('w') as out:
        def row(*values):
            out.write(' '.join(map(str, values)) + '\n')
        row('FUSIONPAR_TEXT_V1')
        row(len(sites))
        for site in sites:
            x, y, z, layer = tp.location(site)
            tid, wo, ho = grid[x, y, layer]
            if wo or ho:
                raise ValueError('non-root site in contract')
            terminals = []
            for logical, port, bit, role in pin_keys:
                if logical != site['physical_type']:
                    continue
                physical = types[tid]['pins'].get((logical, z, port, bit))
                if physical is None:
                    continue
                cls, direction, _ = physical
                if direction != ('OUTPUT' if role == 'SOURCE' else 'INPUT'):
                    raise ValueError('physical pin direction mismatch')
                node = nodes.get((x, y, layer, cls, role))
                if node is None:
                    raise ValueError('missing site terminal')
                terminals += [pin_id[logical, port, bit, role], node, int(role == 'SOURCE')]
            row(x, y, z, type_ids[site['physical_type']], len(terminals)//3, *terminals)
        row(len(blocks))
        for block in blocks:
            allowed = [i for i, site in enumerate(sites) if site['physical_type'] == block['logical_type']
                       and tp.in_region(block, tp.location(site)) and tp.matches_fixed(block, tp.location(site))]
            x, y, z, layer, _ = place_rows[block['name']]
            row(type_ids[block['logical_type']], int(block['fixed']), len(allowed), *allowed, loc_to_site[x, y, z, layer], 0)
        macros = defaultdict(list)
        for b in blocks:
            if b['macro']:
                macros[b['macro']['id']].append(b)
        row(len(macros))
        for _, members in sorted(macros.items()):
            anchor = members[0]
            a = anchor['macro']
            data = []
            for member in members:
                m = member['macro']
                if m['dlayer'] != a['dlayer']:
                    raise ValueError('multi-layer macro unsupported')
                data += [member['block_id'], m['dx']-a['dx'], m['dy']-a['dy'], m['dsubtile']-a['dsubtile']]
            row(anchor['block_id'], len(members), *data)
        row(len(records))
        for c in records:
            row(c['net'], c['source_instance'], c['source_pin'], c['sink_instance'], c['sink_pin'],
                65535, c['priority'], 0, c['source'], c['sink'], 0, len(c['path']), *c['path'])
    contract = args.output / 'placement_contract'
    contract.mkdir()
    for name in ('manifest.json', 'blocks.jsonl', 'sites.jsonl', 'nets.jsonl'):
        shutil.copyfile(args.contract / name, contract / name)
    rr_export = {'backend': getattr(args, 'rr_export_backend', 'xml')}
    if rr_export['backend'] == 'sqlite':
        start = time.perf_counter_ns()
        rr_export['metadata'] = rr_export_cache.build(args.graph, args.output/'graph.nodes',
            args.output/'graph.edges', args.output/'rr_export.sqlite', writer)
        rr_export['preparation_ns'] = time.perf_counter_ns() - start
    elif rr_export['backend'] != 'xml':
        raise ValueError('unsupported RR export backend')
    static = [Path(__file__), Path(endpoints.__file__), Path(tp.__file__), Path(writer.__file__),
              ROOT / 'tools/validate_candidate.py', Path(rr_export_cache.__file__),
              PROJECTS / 'persistroute/tools/validate_vpr_route.py']
    if 'timing_vpr' in paths:
        static.append(PROJECTS / 'persistroute/tools/vpr_timing_analyzer.py')
    result = {'schema': 'FUSIONPAR_VPR_BUNDLE_V1', 'inputs': paths,
              'preparation_command': [sys.executable, *sys.argv],
              'sources': [binding(p) for p in static], 'channel_width': args.channel_width,
              'blocks': blocks, 'sites': sites,
              'connections': [{k: v for k, v in c.items() if k != 'path'} for c in records],
              'scope': 'single-layer local refinement; no root-clock nets',
              'timing': 'native_barriers' if 'timing_vpr' in paths else 'frozen_zero',
              'graph_cost_model': graph_manifest['edge_delay_model'], 'rr_export': rr_export,
              'files': {str(p.relative_to(args.output)): binding(p) for p in sorted(args.output.rglob('*')) if p.is_file()}}
    for entry in list(paths.values()) + result['sources']:
        if sha(entry['path']) != entry['sha256']:
            raise ValueError('input/source changed during conversion')
    (args.output / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    return {'bundle': str(args.output.resolve()), 'blocks': len(blocks), 'sites': len(sites), 'connections': len(records)}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('net', 'place', 'route', 'graph', 'graph-prefix', 'contract', 'vpr', 'arch', 'circuit', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--channel-width', type=int, required=True)
    p.add_argument('--timing-vpr', type=Path)
    p.add_argument('--priority-reference', type=Path, help='Bound bundle manifest defining stable logical-connection priorities')
    p.add_argument('--rr-export-backend', choices=('xml', 'sqlite'), default='xml')
    print(json.dumps(prepare(p.parse_args()), indent=2))
