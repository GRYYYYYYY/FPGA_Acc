"""Independent original-XML endpoint audit including multi-height hard blocks."""
from collections import Counter
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as E

sys.path.insert(0, str(Path(__file__).resolve().parent / 'native_resume_prototype'))
from pre_route_endpoints import sha, placements
from source_binding_v2 import closure
from rooted_rr_endpoint_geometry_v1 import validate


def audit(directory, receipt_path, output):
    directory, receipt_path, output = [Path(p).resolve() for p in [directory, receipt_path, output]]
    assert not output.exists()
    receipt = json.loads(receipt_path.read_text())
    assert all(sha(p) == h for p, h in receipt['bindings'].items())
    row = next(r for r in receipt['rows'] if r['name'] == directory.name)
    assert row['status'] == 'GRAPH_AND_ENDPOINTS_CAPTURED' and row['exit_code'] == 1
    assert all(sha(p) == h for p, h in row['files'].items())
    ep_path, map_path, graph = [directory / p for p in ['endpoints.json', 'mapping.json', 'rr_graph.xml']]
    ep, mapping = [json.loads(p.read_text()) for p in [ep_path, map_path]]
    assert sha(graph) == ep['graph_sha256'] and all(sha(v['path']) == v['sha256'] for v in ep['inputs'].values())
    pos = placements(directory / 'design.place', sha(directory / 'design.net'))
    root = E.parse(directory / 'design.net').getroot()
    logical = {b.get('name'): re.sub(r'\[\d+\]$', '', b.get('instance')) for b in root.findall('block')}
    assert set(logical) == set(pos)
    wanted = {p['rr_node'] for p in mapping['pin_details']}
    nodes, grid, dimensions, pins = {}, {}, {}, {}
    stack = []
    for event, el in E.iterparse(graph, events=('start', 'end')):
        if event == 'start':
            stack.append(el)
            continue
        parent = stack[-2].tag if len(stack) > 1 else None
        if el.tag == 'block_type' and parent == 'block_types':
            tid = int(el.get('id'))
            assert tid not in dimensions
            dimensions[tid] = int(el.get('width', 1)), int(el.get('height', 1))
            pins[tid] = {}
            for cid, cls in enumerate(el.findall('pin_class')):
                for pin in cls.findall('pin'):
                    ptc = int(pin.get('ptc'))
                    assert ptc not in pins[tid]
                    head, tail = pin.text.strip().rsplit('.', 1)
                    if head.endswith(']'):
                        physical, ztext = head[:-1].rsplit('[', 1)
                        z = int(ztext)
                    else:
                        physical, z = head, 0
                    port, bit = tail[:-1].rsplit('[', 1)
                    pins[tid][ptc] = cid, cls.get('type'), physical, z, port, int(bit)
            stack[-2].remove(el)
            el.clear()
        elif el.tag == 'grid_loc' and parent == 'grid':
            key = int(el.get('x')), int(el.get('y')), int(el.get('layer', 0))
            assert key not in grid
            grid[key] = tuple(int(el.get(k)) for k in ['block_type_id', 'width_offset', 'height_offset'])
            stack[-2].remove(el)
            el.clear()
        elif el.tag == 'node' and parent == 'rr_nodes':
            node = int(el.get('id'))
            if node in wanted:
                assert node not in nodes
                nodes[node] = el.get('type'), int(el.get('capacity')), dict(el.find('loc').attrib)
            stack[-2].remove(el)
            el.clear()
        if el.tag == 'rr_nodes':
            break
        stack.pop()
    assert set(nodes) == wanted
    assert ep['clock_policy'] == 'exclude_root_clocks'
    excluded = {r['net_id'] for r in ep['excluded_nets']}
    sources, sinks = {}, Counter()
    offset_pins, examples = Counter(), []
    for p in mapping['pin_details']:
        typ, cap, loc = nodes[p['rr_node']]
        assert typ == p['role'] and cap > 0 and int(loc['ptc']) == p['class_id']
        position = pos[p['block']]
        assert position[4] == p['block_id']
        tid = validate(loc, position, grid, dimensions)
        cid, direction, physical, z, port, bit = pins[tid][p['physical_pin_ptc']]
        assert (cid, physical, z, port, bit) == (p['class_id'], logical[p['block']], position[2], p['port'], p['bit'])
        assert direction == ('OUTPUT' if typ == 'SOURCE' else 'INPUT')
        assert ep['net_names'][str(p['net_id'])] == p['net']
        if not (int(loc['xlow']) <= position[0] <= int(loc['xhigh']) and int(loc['ylow']) <= position[1] <= int(loc['yhigh'])):
            offset_pins[physical] += 1
            if len(examples) < 8:
                examples.append(dict(block=p['block'], type=physical, placement=position, rr_node=p['rr_node'], bbox=loc))
        if p['net_id'] in excluded:
            continue
        if typ == 'SOURCE':
            assert p['net_id'] not in sources or sources[p['net_id']] == p['rr_node']
            sources[p['net_id']] = p['rr_node']
        else:
            assert typ == 'SINK'
            sinks[p['net_id'], p['rr_node']] += 1
    queries = ep['connections']
    assert [q['connection_id'] for q in queries] == list(range(len(queries)))
    assert Counter((q['net_id'], q['sink']) for q in queries) == sinks
    assert all(q['source'] == sources[q['net_id']] for q in queries)
    assert len(queries) == mapping['connections'] == row['connections']
    assert not list(directory.glob('*.route'))
    bindings = {**closure([Path(__file__)]), **receipt['bindings'], **row['files'], str(receipt_path): sha(receipt_path)}
    assert all(sha(p) == h for p, h in bindings.items())
    result = dict(bindings=bindings, connections=len(queries), physical_endpoint_nodes=len(nodes), complete_manifest_query_partition_and_original_XML_node_type_class_capacity_bbox_pass=True, original_XML_pin_membership_and_full_rooted_tile_footprints_pass=True, pin_occurrences_outside_root_point_bbox=dict(offset_pins), offset_examples=examples, scope='Independent full query coverage, physical pin/class membership, positive endpoint capacity and original-grid rooted footprint. A multi-height endpoint bbox may exclude the placement root but every covered grid cell must belong to that exact physical tile. No route-derived fallback or omitted query; native ignored flags, live criticality and full prediction remain separate gates.')
    with output.open('x') as f:
        f.write(json.dumps(result, indent=2) + '\n')
    print('ROOTED ENDPOINT AUDIT PASS', len(queries), len(nodes), dict(offset_pins), flush=True)


if __name__ == '__main__':
    audit(sys.argv[1], sys.argv[2], sys.argv[3])
