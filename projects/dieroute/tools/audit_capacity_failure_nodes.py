"""Reconstruct the printed failed-baseline resource conflicts by net identity."""
import collections
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[1]
D = R / 'work/native_capacity_coverage_20261017'
O = R / 'work/native_capacity_failure_nodes_20261017'


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for b in iter(lambda: stream.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def main():
    prior = json.loads((D / 'independent_audit.json').read_text())
    cases = []
    sources = {}
    for row in prior['outcomes']:
        if row['native_legal']:
            continue
        folder = D / f"{row['case']}_{row['width']}x{row['height']}_seed1"
        log = folder / 'vpr.log'
        text = log.read_text()
        section = text.split('Routing Failure Diagnostics: Printing Overused Nodes Information', 1)[1].split('Final Net Connection Criticality Histogram:', 1)[0]
        parsed = re.findall(r'^\s*\d+\s+(\d+)\s+(\d+)\s+(\d+)\s+(IPIN|OPIN|CHANX|CHANY|SOURCE|SINK)\s+', section, re.M)
        count = int(re.findall(r'Total number of overused nodes:\s*(\d+)', text)[-1])
        assert len(parsed) == count
        targets = {int(n): dict(node=int(n), printed_occupancy=int(occ), printed_capacity=int(cap), printed_type=kind) for n, occ, cap, kind in parsed}
        owners = {n: set() for n in targets}
        net = None
        route = folder / 'circuit.route'
        for line in route.read_text().splitlines():
            match = re.match(r'Net\s+(\d+)\s+\(', line)
            if match:
                net = int(match[1])
            match = re.match(r'Node:\s*(\d+)\s+', line)
            if match and int(match[1]) in owners:
                assert net is not None
                owners[int(match[1])].add(net)
        graph = folder / 'rr_graph.xml'
        found = {}
        for _, element in ET.iterparse(graph, events=('end',)):
            if element.tag == 'node':
                node = int(element.attrib['id'])
                if node in targets:
                    found[node] = dict(attributes=dict(element.attrib), location=dict(element.find('loc').attrib))
                element.clear()
            elif element.tag == 'edge':
                element.clear()
        assert set(found) == set(targets)
        for node, details in targets.items():
            details.update(graph=found[node], distinct_route_nets=sorted(owners[node]))
            assert len(owners[node]) == details['printed_occupancy']
            assert int(found[node]['attributes']['capacity']) == details['printed_capacity']
            assert found[node]['attributes']['type'] == details['printed_type']
            assert len(owners[node]) > details['printed_capacity']
        cases.append(dict(case=row['case'], width=row['width'], height=row['height'], conflicts=list(targets.values()), types=dict(collections.Counter(v['printed_type'] for v in targets.values()))))
        for path in [log, route, graph]:
            sources[str(path)] = sha(path)
    for path in [D / 'independent_audit.json', Path(__file__).resolve()]:
        sources[str(path)] = sha(path)
    O.mkdir(exist_ok=False)
    report = dict(status='four_failed_routes_printed_conflicts_reconstructed_from_graph_and_net_sets', cases=cases, source_sha256=sources, scope='Only final printed overused nodes; route distinct-net counts and RR type/capacity/location matched. Input-pin conflicts dominate this snapshot, not a unique causal proof, global occupancy reconstruction, pin-equivalence bug proof or impossibility at other settings.', research_complete=False)
    (O / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps([dict(case=r['case'], width=r['width'], types=r['types']) for r in cases]))


if __name__ == '__main__':
    main()
