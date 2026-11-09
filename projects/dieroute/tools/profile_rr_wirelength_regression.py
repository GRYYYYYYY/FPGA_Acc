"""Attribute native route wirelength changes to nets without altering routing."""
import argparse
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


def routed_nodes(path):
    nets = {}
    current = None
    for line in path.read_text().splitlines():
        match = re.match(r'^Net\s+(\d+)\s+\(', line)
        if match:
            current = int(match[1])
            assert current not in nets
            nets[current] = set()
        node = re.match(r'^\s*Node:\s*(\d+)\s+', line)
        if node:
            assert current is not None
            nets[current].add(int(node[1]))
    return nets


def profile(case, pair):
    baseline = routed_nodes(case / 'circuit.route')
    candidate = routed_nodes(pair / 'downstream_bounded.route')
    assert baseline.keys() == candidate.keys(), 'Route net coverage differs'
    lengths = {}
    for _, node in ET.iterparse(case / 'rr_graph.xml', events=('end',)):
        if node.tag == 'node':
            loc = node.find('loc')
            kind = node.attrib['type']
            length = 0
            if kind in ('CHANX', 'CHANY'):
                axis = 'x' if kind == 'CHANX' else 'y'
                length = int(loc.attrib[axis + 'high']) - int(loc.attrib[axis + 'low']) + 1
            lengths[int(node.attrib['id'])] = length
            node.clear()
    rows = []
    for net in baseline:
        before = sum(lengths[n] for n in baseline[net])
        after = sum(lengths[n] for n in candidate[net])
        rows.append(dict(net_id=net, baseline=before, candidate=after, delta=after-before))
    rows.sort(key=lambda row: (-row['delta'], row['net_id']))
    validation = json.loads((pair / 'downstream_bounded_validation/validation.json').read_text())
    return dict(baseline_wirelength=sum(r['baseline'] for r in rows),
                candidate_wirelength=sum(r['candidate'] for r in rows),
                native_validation=validation, net_deltas=rows,
                scope='Unique CHANX/CHANY geometric span per net; not a CPD model or a QoR acceptance decision')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    audit_path = root / 'experiments/wide_timing_cohort_audit_20261013.json'
    audit = json.loads(audit_path.read_text())
    result = dict(research_complete=False, board_result=False, cases=[])
    result['audit_sha256'] = hashlib.sha256(audit_path.read_bytes()).hexdigest()
    for experiment in audit['experiments']:
        case = Path(experiment['case'])
        pair = Path(experiment['manifest']).parent
        report = profile(case, pair)
        manifest = json.loads((pair / 'pair.json').read_text())
        connections = Path(manifest['reference']) / 'connections.csv'
        fanout = {}
        with connections.open() as stream:
            for row in csv.DictReader(stream):
                net = int(row['net_id'])
                fanout[net] = fanout.get(net, 0) + 1
        for row in report['net_deltas']:
            row['connections'] = fanout.get(row['net_id'], 0)
        report['gross_increase'] = sum(max(0, r['delta']) for r in report['net_deltas'])
        report['gross_decrease'] = sum(min(0, r['delta']) for r in report['net_deltas'])
        report['net_increase'] = report['gross_increase'] + report['gross_decrease']
        expected = experiment['modes']['downstream_bounded']['native_qor']
        assert report['baseline_wirelength'] == expected['baseline_wirelength']
        assert report['candidate_wirelength'] == expected['total_wirelength']
        report['case'] = case.name
        report['input_sha256'] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in (case/'circuit.route', case/'rr_graph.xml',
                                            pair/'downstream_bounded.route', connections)}
        result['cases'].append(report)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps([dict(case=r['case'], baseline=r['baseline_wirelength'],
                           candidate=r['candidate_wirelength'], top=r['net_deltas'][:5])
                      for r in result['cases']]))
