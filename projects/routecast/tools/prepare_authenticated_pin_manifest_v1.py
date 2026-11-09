"""Bind each query to its actual logical pin after original-XML endpoint admission."""
import json
from collections import defaultdict
from pathlib import Path
import sys

R = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(R / 'tools'), str(R / 'tools/native_resume_prototype')]
from pre_route_endpoints import sha, placements
from source_binding_v2 import closure


def prepare(demand, physical_proof, mapping, lattice_proof, settings, output):
    demand, physical_proof, mapping, lattice_proof, settings, output = [Path(p).resolve() for p in [demand, physical_proof, mapping, lattice_proof, settings, output]]
    output.mkdir()
    bindings = closure([Path(__file__)])
    for path, flag in [
        (demand / 'verification.json', 'exhaustive_disjoint_partition_exact_original_queries_and_whole_NET_scope_pass'),
        (physical_proof, 'original_XML_pin_membership_and_full_rooted_tile_footprints_pass'),
        (lattice_proof, 'original_XML_all_node_and_edge_identities_and_electrical_values_pass'),
    ]:
        proof = json.loads(path.read_text())
        assert proof[flag] and all(sha(p) == h for p, h in proof['bindings'].items())
        for p, digest in proof['bindings'].items():
            assert p not in bindings or bindings[p] == digest
            bindings[p] = digest
        bindings[str(path)] = sha(path)
    assert bindings[str(mapping)] == sha(mapping)
    ep_path = demand / 'endpoints.json'
    ep = json.loads(ep_path.read_text())
    assert bindings[str(ep_path)] == sha(ep_path)
    assert all(sha(v['path']) == v['sha256'] for v in ep['inputs'].values())
    native = [json.loads(line) for line in Path(ep['inputs']['native_identity']['path']).read_text().splitlines()]
    lookup = {r['name']: r for r in native}
    assert len(lookup) == len(native)
    positions = placements(ep['inputs']['place']['path'], ep['inputs']['net']['sha256'])
    details = json.loads(mapping.read_text())['pin_details']
    sources, sinks = {}, defaultdict(list)
    for pin in details:
        if pin['role'] == 'SOURCE':
            assert pin['net'] not in sources
            sources[pin['net']] = pin
        else:
            assert pin['role'] == 'SINK'
            sinks[pin['net']].append(pin)
    groups = defaultdict(list)
    for q in ep['connections']:
        groups[q['net_id']].append(q)
    lattice = json.loads(lattice_proof.read_text())
    assert lattice['bindings'][ep['inputs']['graph']['path']] == ep['graph_sha256']
    lines = [f"G {lattice['nodes']} {lattice['edges']} {len(ep['connections'])}\n"]
    for r in native:
        lines.append(f"N {r['net_id']} {int(r['ignored'])} {len(r['pins'])}\n")
    alignment = []
    expected_pins = set()
    for net, qs in sorted(groups.items()):
        name = ep['net_names'][str(net)]
        row = lookup[name]
        assert not row['ignored'] and row['net_id'] == net
        pins = row['pins']
        assert [p['index'] for p in pins] == list(range(len(pins)))
        def key(p):
            return p['block'], p['port'], p['bit']
        indexed = {key(p): p for p in pins[1:]}
        assert len(indexed) == len(pins) - 1 == len(qs) == len(sinks[name])
        source = sources[name]
        assert key(source) == key(pins[0])
        def exact_pin(mapping_pin, native_pin):
            pos = positions[mapping_pin['block']]
            assert (native_pin['x'], native_pin['y'], native_pin['layer']) == (pos[0], pos[1], pos[3])
            assert (native_pin['physical_pin'], native_pin['class']) == (mapping_pin['physical_pin_ptc'], mapping_pin['class_id'])
        exact_pin(source, pins[0])
        for q, sink in zip(qs, sinks[name]):
            pin = indexed[key(sink)]
            exact_pin(sink, pin)
            assert (q['source'], q['sink']) == (source['rr_node'], sink['rr_node'])
            identity = net, pin['index']
            assert identity not in expected_pins
            expected_pins.add(identity)
            lines.append(f"Q {q['connection_id']} {net} {pin['index']} {q['source']} {q['sink']}\n")
            alignment.append(dict(connection_id=q['connection_id'], net_id=net, local_sink_pin=pin['index'], block=pin['block'], port=pin['port'], bit=pin['bit'], physical_pin=pin['physical_pin'], rr_node=q['sink']))
    required = {(r['net_id'], p['index']) for r in native if not r['ignored'] for p in r['pins'][1:]}
    assert expected_pins == required and len(alignment) == len(ep['connections'])
    settings_value = json.loads(settings.read_text())
    assert all(sha(p) == h for p, h in settings_value['bindings'].items())
    bindings.update(settings_value['bindings'])
    bindings[str(settings)] = sha(settings)
    manifest = output / 'queries.txt'
    manifest.write_text(''.join(lines))
    alignment_file = output / 'pin_alignment.json'
    alignment_file.write_text(json.dumps(alignment) + '\n')
    for p in [manifest, alignment_file]:
        bindings[str(p)] = sha(p)
    assert all(sha(p) == h for p, h in bindings.items())
    (output / 'verification.json').write_text(json.dumps(dict(bindings=bindings, endpoint=str(ep_path), architecture=settings_value['architecture'], settings=str(settings), connections=len(alignment), nets=len(groups), manifest=str(manifest), complete_native_identity_pin_to_physical_endpoint_assignment_pass=True, logical_pin_key_to_native_index_and_XML_physical_identity_pass=True, scope='Every actual native nonignored sink pin matched by NET/block/port/bit and physical pin/class/position to independently audited original-XML endpoint mapping. Duplicate RR sink classes retain distinct logical pin identities. No native route input, criticality values or routing quality proof.'), indent=2) + '\n')
    print('AUTHENTICATED PIN MANIFEST PASS', len(alignment), 'connections', len(groups), 'NETs', flush=True)


if __name__ == '__main__':
    prepare(*sys.argv[1:])
