#!/usr/bin/env python3
"""Export VPR's printed indexed base costs and re-encode only PR edge costs.

No routing algorithm is implemented here. These are rounded ps costs from the
native echo table, not a claim to reproduce VPR's complete routing objective.
"""
import argparse
from collections import Counter
from decimal import Decimal, ROUND_HALF_EVEN
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import xml.etree.ElementTree as ET

from run_native_case import sha256


def read_table(path):
    table = {}
    rows = []
    for line in path.read_text().splitlines()[2:]:
        fields = line.split()
        if not fields:
            continue
        kind = fields[1]
        channel = kind in ('CHANX', 'CHANY')
        if kind not in ('SOURCE', 'SINK', 'OPIN', 'IPIN', 'CHANX', 'CHANY'):
            raise ValueError('unknown indexed resource type')
        offset = 3 if channel else 2
        if len(fields) != offset + 7:
            raise ValueError('unsupported indexed cost table row')
        seg = int(fields[offset + 2])
        if channel != (seg >= 0):
            raise ValueError('invalid indexed segment')
        cost = Decimal(fields[offset]) * Decimal(10**12)
        if not cost.is_finite() or cost < 0 or cost > 65535:
            raise ValueError('base cost does not fit finite nonnegative ps/u16')
        quantized = int(cost.to_integral_value(rounding=ROUND_HALF_EVEN))
        key = (kind, seg)
        if key in table:
            raise ValueError('ambiguous indexed cost mapping')
        table[key] = quantized
        rows.append({'type': kind, 'segment_id': seg, 'echo_base_cost_s': fields[offset],
                     'base_cost_ps_q': quantized, 'rounding_error_ps': float(Decimal(quantized) - cost)})
    if not table or any((k, -1) not in table for k in ('SOURCE', 'SINK', 'OPIN', 'IPIN')):
        raise ValueError('incomplete indexed cost table')
    return table, rows


def map_nodes(rr_graph, table):
    costs = []
    counts = Counter()
    stack = []
    for event, elem in ET.iterparse(rr_graph, events=('start', 'end')):
        if event == 'start':
            stack.append(elem)
            continue
        if elem.tag == 'node':
            if int(elem.attrib['id']) != len(costs):
                raise ValueError('RR nodes must be dense')
            kind = elem.attrib['type']
            segment = elem.find('segment')
            if kind in ('CHANX', 'CHANY') and segment is None:
                raise ValueError('channel node lacks segment ID')
            seg = int(segment.attrib['segment_id']) if segment is not None else -1
            if (kind, seg) not in table:
                raise ValueError('node has no unique native indexed cost')
            costs.append(table[kind, seg])
            counts[f'{kind}:{seg}'] += 1
        if elem.tag in ('node', 'edge', 'grid_loc', 'block_type', 'switch') and len(stack) >= 2:
            stack[-2].remove(elem)
            elem.clear()
        stack.pop()
    if not costs:
        raise ValueError('empty RR graph')
    return costs, dict(sorted(counts.items()))


def verify_export(directory, case=None):
    manifest = directory / 'costs.json'
    d = json.loads(manifest.read_text())
    if d['status'] != 'passed' or d['exit_code'] != 0:
        raise ValueError('native cost export failed')
    native_case = Path(d['case'])
    if case is not None and native_case != case.resolve():
        raise ValueError('cost export belongs to another case')
    for rel, expected in d['case_sha256'].items():
        if sha256(native_case / rel) != expected:
            raise ValueError('native cost input changed')
    if sha256(Path(d['command'][0])) != d['vpr_sha256']:
        raise ValueError('native cost VPR changed')
    for rel, expected in d['artifacts'].items():
        if sha256(directory / rel) != expected:
            raise ValueError('native cost artifact changed')
    table, _ = read_table(directory / 'rr_indexed_data.echo')
    mapped, _ = map_nodes(native_case / 'rr_graph.xml', table)
    encoded = [x[0] for x in struct.iter_unpack('<H', (directory / 'node_base_cost').read_bytes())]
    if mapped != encoded or len(mapped) != d['node_count']:
        raise ValueError('native node costs differ from the echoed type/segment mapping')
    return d


def export(case, out):
    case, out = case.resolve(), out.resolve()
    native = json.loads((case / 'run.json').read_text())
    if native['status'] != 'passed':
        raise ValueError('native baseline is not complete')
    for rel, info in native['artifacts'].items():
        if sha256(case / rel) != info['sha256']:
            raise ValueError('native baseline artifact changed')
    binary = Path(native['sources']['vpr']['path'])
    if sha256(binary) != native['sources']['vpr']['sha256']:
        raise ValueError('native VPR changed')
    out.mkdir(parents=True, exist_ok=False)
    for name in ('circuit.net', 'circuit.place', 'circuit.route'):
        shutil.copyfile(case / name, out / name)
    width = native['command'][native['command'].index('--route_chan_width') + 1]
    cmd = [str(binary), str(case / 'architecture.xml'), str(case / 'circuit.blif'), '--analysis',
           '--net_file', 'circuit.net', '--place_file', 'circuit.place', '--route_file', 'circuit.route',
           '--read_rr_graph', str(case / 'rr_graph.xml'), '--route_chan_width', width,
           '--echo_file', 'on', '--num_workers', '1']
    d = {'schema': 'dieroute.native_base_costs.v1', 'status': 'running', 'case': str(case),
         'command': cmd, 'vpr_sha256': sha256(binary),
         'case_sha256': {rel: sha256(case / rel) for rel in ['run.json', *native['artifacts']]}}
    manifest = out / 'costs.json'
    def save():
        manifest.write_text(json.dumps(d, indent=2) + '\n')
    try:
        env = {k: v for k, v in os.environ.items() if not k.startswith(('DIEROUTE_', 'PERSISTROUTE_'))}
        with (out / 'vpr.log').open('w') as stream:
            child = subprocess.Popen(cmd, cwd=out, env=env, stdout=stream, stderr=subprocess.STDOUT)
            d['pid'] = child.pid
            save()
            d['exit_code'] = child.wait()
        log = (out / 'vpr.log').read_text()
        if d['exit_code'] or any(marker not in log for marker in (
                'VPR succeeded', 'Completed routing consistency check successfully.',
                'Circuit successfully routed', 'RouterOpts.base_cost_type: DELAY_NORMALIZED_LENGTH')):
            raise ValueError('native analysis or expected base-cost mode failed')
        table, rows = read_table(out / 'rr_indexed_data.echo')
        costs, counts = map_nodes(case / 'rr_graph.xml', table)
        with (out / 'node_base_cost').open('wb') as stream:
            for cost in costs:
                stream.write(struct.pack('<H', cost))
        d.update(status='passed', rows=rows, node_count=len(costs), nodes_by_type_segment=counts,
                 encoding='little-endian u16 ps; rounded native printed indexed base costs',
                 limitation='Echo precision and integer rounding; no change to congestion, criticality weighting, RC model or non-configurable-set semantics',
                 artifacts={p: sha256(out / p) for p in ('vpr.log', 'rr_indexed_data.echo', 'node_base_cost')})
    except Exception as error:
        d.update(status='failed', error=str(error))
        raise
    finally:
        save()
    verify_export(out, case)
    return d


def rebase(cost_dir, source, output):
    d = verify_export(cost_dir)
    original_manifest = json.loads(Path(str(source) + '.manifest.json').read_text())
    if original_manifest['rr_graph_sha256'] != d['case_sha256']['rr_graph.xml']:
        raise ValueError('cost export does not describe the original input graph')
    for ext in ('nodes', 'edges', 'resources', 'tasks'):
        if sha256(Path(str(source) + '.' + ext)) != original_manifest['files'][ext]['sha256']:
            raise ValueError('original binary input differs from its manifest')
    costs = [x[0] for x in struct.iter_unpack('<H', (cost_dir / 'node_base_cost').read_bytes())]
    if len(costs) != d['node_count'] or Path(str(source) + '.nodes').stat().st_size != len(costs) * 8:
        raise ValueError('node count differs from cost mapping')
    for ext in ('nodes', 'edges', 'resources', 'tasks', 'costs.json'):
        if Path(str(output) + '.' + ext).exists():
            raise FileExistsError(str(output) + '.' + ext)
    original = Path(str(source) + '.edges').read_bytes()
    encoded = bytearray()
    for dst, base, delay in struct.iter_unpack('<IHH', original):
        if dst >= len(costs):
            raise ValueError('edge destination outside cost mapping')
        encoded.extend(struct.pack('<IHH', dst, costs[dst], delay))
    output.parent.mkdir(parents=True, exist_ok=True)
    for ext in ('nodes', 'resources', 'tasks'):
        shutil.copyfile(str(source) + '.' + ext, str(output) + '.' + ext)
    Path(str(output) + '.edges').write_bytes(encoded)
    meta = {'schema': 'dieroute.rebased_inputs.v1', 'cost_export': str(cost_dir.resolve()),
            'cost_export_sha256': sha256(cost_dir / 'costs.json'), 'original_prefix': str(source.resolve()),
            'artifacts': {ext: sha256(Path(str(output) + '.' + ext)) for ext in ('nodes', 'edges', 'resources', 'tasks')}}
    Path(str(output) + '.costs.json').write_text(json.dumps(meta, indent=2) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='action', required=True)
    e = sub.add_parser('export')
    e.add_argument('case', type=Path)
    e.add_argument('output', type=Path)
    r = sub.add_parser('rebase')
    r.add_argument('cost_directory', type=Path)
    r.add_argument('source', type=Path)
    r.add_argument('output', type=Path)
    a = p.parse_args()
    if a.action == 'export':
        export(a.case, a.output)
    else:
        rebase(a.cost_directory, a.source, a.output)
