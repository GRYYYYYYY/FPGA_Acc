"""Inspect unused IPIN predecessors of the conflicted routes' exact RR SINKs."""
import collections
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[1]
D = R / 'work/native_capacity_coverage_20261017'
O = R / 'work/native_capacity_pin_alternatives_20261017'


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for b in iter(lambda: stream.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def main():
    prior_path = R / 'work/native_capacity_failure_nodes_20261017/audit.json'
    prior = json.loads(prior_path.read_text())
    records = []
    sources = {str(prior_path): sha(prior_path)}
    for case in prior['cases']:
        folder = D / f"{case['case']}_{case['width']}x{case['height']}_seed1"
        targets = {v['node'] for v in case['conflicts'] if v['printed_type'] == 'IPIN'}
        occupancy = collections.defaultdict(set)
        connections = set()
        previous = None
        net = None
        route = folder / 'circuit.route'
        for line in route.read_text().splitlines():
            match = re.match(r'Net\s+(\d+)\s+\(', line)
            if match:
                net = int(match[1]); previous = None
            match = re.match(r'Node:\s*(\d+)\s+(\w+)', line)
            if not match:
                continue
            node, kind = int(match[1]), match[2]
            if kind == 'IPIN':
                occupancy[node].add(net)
            if previous in targets:
                assert kind == 'SINK', (previous, kind)
                connections.add((net, previous, node))
            previous = node
        assert {pin for _, pin, _ in connections} == targets
        sinks = {sink for _, _, sink in connections}
        predecessors = collections.defaultdict(set)
        ipin_capacity = {}
        sink_details = {}
        graph = folder / 'rr_graph.xml'
        for _, element in ET.iterparse(graph, events=('end',)):
            if element.tag == 'node':
                node = int(element.attrib['id'])
                if element.attrib['type'] == 'IPIN':
                    ipin_capacity[node] = int(element.attrib['capacity'])
                if node in sinks:
                    assert element.attrib['type'] == 'SINK'
                    sink_details[node] = dict(capacity=int(element.attrib['capacity']), location=dict(element.find('loc').attrib))
                element.clear()
            elif element.tag == 'edge':
                dest = int(element.attrib['sink_node'])
                src = int(element.attrib['src_node'])
                if dest in sinks and src in ipin_capacity:
                    predecessors[dest].add(src)
                element.clear()
        rows = []
        for net, pin, sink in sorted(connections):
            assert pin in predecessors[sink]
            unused = sorted(n for n in predecessors[sink] if not occupancy[n])
            rows.append(dict(net=net, conflicted_ipin=pin, sink=sink, sink_details=sink_details[sink],
                             direct_ipin_predecessors=len(predecessors[sink]), unused_ipin_predecessors=unused))
        records.append(dict(case=case['case'], width=case['width'], height=case['height'], connections=rows))
        for p in [route, graph]:
            sources[str(p)] = sha(p)
    sources[str(Path(__file__).resolve())] = sha(Path(__file__).resolve())
    O.mkdir(exist_ok=False)
    result = dict(status='exact_sink_unused_direct_IPIN_predecessors_inspected', cases=records, source_sha256=sources,
                  scope='Necessary local availability only: an unoccupied IPIN feeding the exact RR SINK need not be reachable from the existing route or logically interchangeable under packed-pin constraints. No rerouting, feasibility proof or unique root cause.', research_complete=False)
    (O / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps([dict(case=c['case'], width=c['width'], connections=len(c['connections']), with_unused=sum(bool(r['unused_ipin_predecessors']) for r in c['connections'])) for c in records]))


if __name__ == '__main__':
    main()
