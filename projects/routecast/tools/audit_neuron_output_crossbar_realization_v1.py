"""Complete fanout-aware physical OPIN/packed-driver crossbar certificate.

This is post-label development diagnosis. It does not waive the rejected old
canonical gate and does not create or admit native truth labels by itself.
"""
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
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
from complete_output_port_permutation_v1 import complete_sources
from packed_pin_net_resolver_v1 import Resolver


def main():
    resource.setrlimit(resource.RLIMIT_AS, (8 * 2**30, 8 * 2**30))
    tick = time.perf_counter()
    src = R / 'experiments/titan23_neuron_native_label_audit_v2_2026-10-15'
    native = R / 'experiments/titan23_neuron_native_cold_label_v1_2026-10-14'
    out = R / 'experiments/neuron_output_crossbar_realization_v1_2026-10-15'
    physical_proof = json.loads((src / 'physical_verification.json').read_text())
    assert physical_proof['complete_native_demand_pass']
    for p, h in physical_proof['bindings'].items():
        assert sha(p) == h, p
    cmd = json.loads((native / 'launch.json').read_text())['command']
    graph = Path(cmd[cmd.index('--read_rr_graph') + 1]); arch = Path(cmd[1])
    identity = src / 'canonical/identity.jsonl'
    packed = src / 'canonical/design.net'
    assert sha(packed) == sha(native / 'design.net.post_routing')
    bindings = {**closure([Path(__file__)]),
                **{str(p): sha(p) for p in [src / 'physical_verification.json', graph, arch,
                identity, packed, native / 'output.route', src / 'canonical/reload.log',
                src / 'canonical/stages.json', src / 'canonical/design.net.post_routing']}}
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
    assert len(route_opins) == physical_proof['routed_nets']
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
    architecture = ET.parse(arch).getroot()
    lab = next(p for p in architecture.find('complexblocklist').findall('pb_type') if p.get('name') == 'LAB')
    contracts = {m.get('name'): complete_sources(lab, m.get('name'), 'data_out') for m in lab.findall('mode')}
    packed_root = ET.parse(packed).getroot()
    blocks = {b.get('name'): b for b in packed_root.findall('block')}
    resolver = Resolver(packed_root)
    driven = {}; witnesses = []; exact_other = 0; output_NETs = set()
    for name, ns in route_opins.items():
        driver = records[name]['pins'][0]
        assert driver['index'] == 0
        block = blocks[driver['block']]
        # Resolve the original logical driver all the way through its unchanged
        # packed local references to the original atom NET.
        assert resolver.resolve(block, driver['port'], driver['bit']) == name
        for nid in sorted(ns):
            node = nodes[nid]
            tid, x, y, layer = root(node, grid)
            physical = int(node['loc']['ptc'])
            assert node['type'] == 'OPIN'
            assert (x, y, layer) == (driver['x'], driver['y'], driver['layer'])
            assert classes[tid][physical] == driver['class']
            logical, z, port, bit = pin_names[tid][physical]; bit = int(bit)
            if logical != 'LAB' or port != 'data_out':
                assert physical == driver['physical_pin'], ('unsupported other output permutation', name)
                exact_other += 1
                continue
            assert block.get('instance').startswith('LAB[') and driver['port'] == 'data_out' and int(z or 0) == 0
            width, allowed = contracts[block.get('mode')]
            ports = [p for p in block.findall('outputs/port') if p.get('name') == 'data_out']
            assert len(ports) == 1
            tokens = (ports[0].text or '').split()
            assert len(tokens) == width and 0 <= bit < width
            token = tokens[driver['bit']]
            assert token in allowed
            # A complete interconnect permits one original child driver to feed
            # several distinct OPIN destinations; never collapse them to one.
            key = (driver['block'], bit)
            assert key not in driven or driven[key] == name
            driven[key] = name
            output_NETs.add(name)
            witnesses.append(dict(net=name, block=driver['block'], opin=nid, routed_bit=bit,
                                  original_bit=driver['bit'], original_local_driver_token=token))
    original_outputs = {}
    for name, record in records.items():
        p = record['pins'][0]
        if blocks[p['block']].get('instance').startswith('LAB[') and p['port'] == 'data_out':
            key = (p['block'], p['bit'])
            assert key not in original_outputs
            assert resolver.resolve(blocks[p['block']], p['port'], p['bit']) == name
            original_outputs[key] = name
    expected = Counter()
    # Rebuild the whole original native mismatch predicate from the route and
    # pin table, including originally open pins and no-sink local reservations.
    block_locations = {p['block']: (p['x'], p['y'], p['layer'])
                       for r in records.values() for p in r['pins']}
    for block, b in blocks.items():
        if not b.get('instance').startswith('LAB['):
            continue
        width, _ = contracts[b.get('mode')]
        x, y, layer = block_locations[block]
        for bit in range(width):
            old = original_outputs.get((block, bit), 'unmapped')
            new = driven.get((block, bit), 'unmapped')
            if old != 'unmapped' and len(records[old]['pins']) == 1:
                continue
            if old != new:
                expected[new, block, x, y, 'LAB', 'data_out', bit, layer, old] += 1
    text = (src / 'canonical/reload.log').read_text()
    pattern = re.compile(r"Fixed up net '([^']*)' mapping mismatch at clustered block '(.*)' pin 'grid\[(\d+)\]\[(\d+)\]\.([^.]*)\.([^\[]*)\[(\d+)\] - layer (\d+)' \(was net '([^']*)'\)")
    observed = Counter(); ignored = Counter()
    for m in pattern.finditer(text):
        routed, block, x, y, tile, port, bit, layer, old = m.groups()
        key = routed, block, int(x), int(y), tile, port, int(bit), int(layer), old
        if tile == 'LAB' and port == 'data_out':
            observed[key] += 1
        else:
            assert routed == 'unmapped' and old in records and records[old]['ignored']
            ignored[old, block, int(x), int(y), int(layer), port, int(bit)] += 1
    assert expected == observed, ('output mismatch multiset differs', sum((expected-observed).values()), sum((observed-expected).values()))
    allowed = Counter((r['name'], p['block'], p['x'], p['y'], p['layer'], p['port'], p['bit'])
                      for r in records.values() if r['ignored'] for p in r['pins'] if p['index'] > 0)
    assert not ignored - allowed
    mismatch_count = int(re.search(r'Found (\d+) mismatches', text)[1])
    assert sum(observed.values()) + sum(ignored.values()) == mismatch_count
    assert sha(packed) == sha(src / 'canonical/design.net.post_routing')
    for p, h in bindings.items():
        assert sha(p) == h, p
    result = dict(bindings=bindings, all_pass=True, routed_NETs=len(route_opins),
                  actual_OPINs=sum(map(len, route_opins.values())),
                  OPIN_count_histogram=dict(Counter(map(len, route_opins.values()))),
                  complete_crossbar_NETs=len(output_NETs), complete_crossbar_OPINs=len(witnesses),
                  exact_other_OPINs=exact_other, output_mismatch_pins=sum(observed.values()),
                  mapped_NET_to_NET_output_changes=sum(v for k, v in observed.items() if k[0]!='unmapped' and k[-1]!='unmapped'),
                  previously_open_output_pins_used=sum(v for k, v in observed.items() if k[-1]=='unmapped'),
                  previously_mapped_output_pins_unused=sum(v for k, v in observed.items() if k[0]=='unmapped'),
                  independently_matched_ignored_sink_mismatches=sum(ignored.values()),
                  all_native_mismatch_records_exhaustively_reproduced=True,
                  original_atom_driver_NETs_independently_resolved=True,
                  original_packed_netlist_byte_identical=True, witnesses=witnesses,
                  label_accepted=False, old_ignored_only_gate_pass=False,
                  independent_certificate_review_pending=True, post_label_development_diagnosis=True,
                  seconds=time.perf_counter()-tick,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  scope='Complete original route OPIN existence/driver/crossbar-fanout certificate and exact native mismatch reproduction. No serialized output permutation, gate waiver, label admission, prediction-quality, heldout or end-to-end gain claim.')
    out.mkdir(exist_ok=False)
    (out / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('bindings','witnesses')}, indent=2), flush=True)


if __name__ == '__main__':
    main()
