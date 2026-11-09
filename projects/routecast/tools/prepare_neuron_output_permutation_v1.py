"""Prepare a reversible LAB complete-crossbar serialization of the frozen route."""
from collections import Counter, defaultdict
import gc
import json
from pathlib import Path
import resource
import sys
import time
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools/native_resume_prototype'))
from pre_route_endpoints import sha, PIN
from source_binding_v2 import closure
from stream_native_NET_occupancy_v1 import NET, NODE
from rooted_native_sink_pin_v1 import root
from rooted_canonical_native_reload_v2 import selected_geometry
from complete_output_port_permutation_v1 import complete_sources, permutation, rewrite, output_spans


def main():
    resource.setrlimit(resource.RLIMIT_AS, (8 * 2**30, 8 * 2**30))
    tick = time.perf_counter()
    src = R / 'experiments/titan23_neuron_native_label_audit_v2_2026-10-15'
    native = R / 'experiments/titan23_neuron_native_cold_label_v1_2026-10-14'
    out = R / 'experiments/neuron_output_permutation_v1_2026-10-15'
    proof = json.loads((src / 'physical_verification.json').read_text())
    assert proof['complete_native_demand_pass']
    for p, h in proof['bindings'].items():
        assert sha(p) == h, p
    cmd = json.loads((native / 'launch.json').read_text())['command']
    graph = Path(cmd[cmd.index('--read_rr_graph') + 1])
    arch = Path(cmd[1])
    packed = native / 'design.net.post_routing'
    identity = src / 'canonical/identity.jsonl'
    assert sha(packed) == sha(src / 'canonical/design.net')
    bindings = {**closure([Path(__file__)]),
                **{str(p): sha(p) for p in [src / 'physical_verification.json', graph, arch,
                   packed, identity, native / 'output.route']}}
    records = {r['name']: r for r in map(json.loads, identity.open())}
    route_opins = defaultdict(set)
    name = None
    for line in (native / 'output.route').open():
        m = NET.match(line)
        if m:
            name = m[2]
        m = NODE.match(line)
        if m and m[2] == 'OPIN':
            assert name in records and not records[name]['ignored']
            route_opins[name].add(int(m[1]))
    assert len(route_opins) == 50767 and all(len(v) == 1 for v in route_opins.values())
    wanted = {n for ns in route_opins.values() for n in ns}
    nodes, grid, classes = selected_geometry(graph, wanted)
    pin_names = {}
    for event, e in ET.iterparse(graph, events=('end',)):
        if e.tag == 'block_type':
            pin_names[int(e.get('id'))] = {int(p.get('ptc')): PIN.fullmatch((p.text or '').strip()).groups()
                                         for c in e.findall('pin_class') for p in c.findall('pin')}
            e.clear()
        if e.tag == 'block_types':
            break
    required = defaultdict(dict)
    witnesses = []
    unchanged_other = 0
    for name, ns in route_opins.items():
        nid = next(iter(ns))
        node = nodes[nid]
        driver = records[name]['pins'][0]
        assert driver['index'] == 0 and node['type'] == 'OPIN'
        tid, x, y, layer = root(node, grid)
        physical = int(node['loc']['ptc'])
        assert (x, y, layer) == (driver['x'], driver['y'], driver['layer'])
        assert classes[tid][physical] == driver['class']
        logical, z, port, bit = pin_names[tid][physical]
        bit = int(bit)
        if logical != 'LAB' or port != 'data_out':
            assert physical == driver['physical_pin'], ('unsupported other output permutation', name)
            unchanged_other += 1
            continue
        assert int(z or 0) == 0 and driver['port'] == 'data_out'
        key = (driver['block'], port)
        assert bit not in required[key]
        required[key][bit] = driver['bit']
        witnesses.append(dict(net=name, block=driver['block'], opin=nid,
                              original_bit=driver['bit'], routed_bit=bit))
    del nodes, grid, classes, records
    gc.collect()
    architecture = ET.parse(arch).getroot()
    lab = next(p for p in architecture.find('complexblocklist').findall('pb_type') if p.get('name') == 'LAB')
    contracts = {}
    for mode in lab.findall('mode'):
        contracts[mode.get('name')] = complete_sources(lab, mode.get('name'), 'data_out')
    root_xml = ET.parse(packed).getroot()
    blocks = {b.get('name'): b for b in root_xml.findall('block')}
    changes = {}
    rows = []
    for (block, port), req in sorted(required.items()):
        b = blocks[block]
        assert b.get('instance').startswith('LAB[')
        width, allowed = contracts[b.get('mode')]
        ports = [p for p in b.findall('outputs/port') if p.get('name') == port]
        assert len(ports) == 1
        old = (ports[0].text or '').split()
        assert len(old) == width
        # Moving top outputs must not invalidate any local feedback reference.
        for child in b.findall('block'):
            for p in child.iter('port'):
                assert 'LAB.data_out[' not in (p.text or '')
        new, mapping = permutation(old, req, allowed)
        if new != old:
            changes[block, port] = (old, new)
        rows.append(dict(block=block, port=port, mode=b.get('mode'),
                         new_to_old=mapping, required_routed_sources=len(req)))
    # Bind every original driver name to its original local output token using
    # the native pin table, independently of the new physical destination.
    records = {r['name']: r for r in map(json.loads, identity.open())}
    for w in witnesses:
        original = records[w['net']]['pins'][0]
        assert original['block'] == w['block'] and original['bit'] == w['original_bit']
        old = (next(p for p in blocks[w['block']].findall('outputs/port')
                    if p.get('name') == 'data_out').text or '').split()
        new = changes.get((w['block'], 'data_out'), (old, old))[1]
        assert new[w['routed_bit']] == old[w['original_bit']] != 'open'
    del root_xml, blocks, records
    gc.collect()
    data = packed.read_bytes()
    rewritten = rewrite(data, changes)
    # Independently invert every changed port; all original bytes outside those
    # text spans must be identical, not merely semantically similar XML trees.
    old_spans = output_spans(data)
    new_spans = output_spans(rewritten)
    a_parts = []; b_parts = []; a_pos = b_pos = 0
    for key in sorted(changes, key=lambda key: old_spans[key][0]):
        a, b = old_spans[key]; c, d = new_spans[key]
        a_parts.append(data[a_pos:a]); b_parts.append(rewritten[b_pos:c])
        assert Counter(data[a:b].split()) == Counter(rewritten[c:d].split())
        a_pos = b; b_pos = d
    a_parts.append(data[a_pos:]); b_parts.append(rewritten[b_pos:])
    assert a_parts == b_parts
    out.mkdir(exist_ok=False)
    (out / 'design.net').write_bytes(rewritten)
    for p, h in bindings.items():
        assert sha(p) == h, p
    result = dict(bindings=bindings, original_net_sha256=sha(packed),
                  derivative_net_sha256=sha(out / 'design.net'),
                  output_file=str(out / 'design.net'), routed_NETs=len(route_opins),
                  complete_crossbar_routed_sources=len(witnesses), other_outputs_unchanged=unchanged_other,
                  blocks_planned=len(rows), blocks_changed=len(changes), rows=rows, witnesses=witnesses,
                  all_driver_tokens_bijectively_preserved=True,
                  all_bytes_outside_changed_top_output_port_text_identical=True,
                  all_routed_OPIN_roots_classes_and_output_crossbar_inputs_checked=True,
                  canonical_reload_pending=True, label_accepted=False,
                  seconds=time.perf_counter() - tick,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  scope='Serialization candidate for the existing original physical route through proven complete top-level output crossbars. No atom, local child route, placement, RR topology, route or SDC change. Requires independent NET-token resolution and native reload before acceptance.')
    (out / 'preparation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('bindings', 'rows', 'witnesses')}, indent=2), flush=True)


if __name__ == '__main__':
    main()
