"""Measure terminal-path wirelength and unique-tree wirelength on audited routes."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from audit_rr_experiments import audit


def native_parents(path):
    trees = {};net = previous = None
    for line in path.read_text().splitlines():
        match = re.match(r'^\s*Net\s+(\d+)\s+\(',line)
        if match:
            net = int(match[1]);trees[net] = {};previous = None
        node = re.match(r'^\s*Node:\s*(\d+)\s+',line)
        if not node:continue
        ident = int(node[1]);switch = re.search(r'\bSwitch:\s*(-?\d+)',line)
        assert net is not None and switch
        parent = trees[net]
        if previous is None:
            if not parent:parent[ident] = None
            else:assert ident in parent,'Unknown native branch anchor'
        elif ident in parent:assert parent[ident] == previous,'Multiple native parents'
        else:parent[ident] = previous
        previous = None if int(switch[1]) == -1 else ident
    return trees


def measure(trees,tasks,spans):
    rows = {}
    for task in tasks:
        net = int(task['net_id']);source = int(task['source']);node = int(task['sink'])
        parent = trees[net];seen = set();length = 0
        while node != source:
            assert node not in seen and node in parent and parent[node] is not None,'Invalid terminal parent chain'
            seen.add(node);length += spans.get(node,0);node = parent[node]
        row = rows.setdefault(net,dict(net_id=net,connections=0,path_wirelength=0,
                                       tree_wirelength=sum(spans.get(n,0) for n in parent)))
        row['connections'] += 1;row['path_wirelength'] += length
    return dict(path_wirelength=sum(r['path_wirelength'] for r in rows.values()),
                tree_wirelength=sum(r['tree_wirelength'] for r in rows.values()),nets=list(rows.values()))


def profile(path,mode):
    verified = audit(path);m = json.loads(path.read_text());assert verified['modes'][mode]['status'] == 'passed'
    case = Path(m['case']);reference = Path(m['reference'])
    with (reference/'connections.csv').open() as stream:tasks = list(csv.DictReader(stream))
    spans = {}
    for _,node in ET.iterparse(case/'rr_graph.xml',events=('end',)):
        if node.tag == 'node':
            if node.attrib['type'] in ('CHANX','CHANY'):
                loc = node.find('loc');axis = 'x' if node.attrib['type'] == 'CHANX' else 'y'
                spans[int(node.attrib['id'])] = int(loc.attrib[axis+'high'])-int(loc.attrib[axis+'low'])+1
            node.clear()
    baseline = measure(native_parents(case/'circuit.route'),tasks,spans)
    candidate = {}
    with (path.parent/f'{mode}_0.route_trees.csv').open() as stream:
        for row in csv.DictReader(stream):
            net,source,parent,child = [int(row[k]) for k in ('net_id','source','parent','child')]
            tree = candidate.setdefault(net,{source:None});assert child not in tree
            tree[child] = parent
    result = measure(candidate,tasks,spans)
    q = verified['modes'][mode]['native_qor']
    assert baseline['tree_wirelength'] == q['baseline_wirelength']
    assert result['tree_wirelength'] == q['total_wirelength']
    for item in (baseline,result):item['path_per_unique_tree_ratio'] = item['path_wirelength']/item['tree_wirelength']
    return dict(manifest=str(path),manifest_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                mode=mode,baseline=baseline,candidate=result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifests',nargs='+',type=Path)
    parser.add_argument('--mode',default='downstream_bounded')
    parser.add_argument('--output',required=True,type=Path)
    args = parser.parse_args()
    rows = [profile(path.resolve(),args.mode) for path in args.manifests]
    report = dict(status='measured_audited_routes',cases=rows,
                  scope='Terminal-path geometric span multiplicity versus unique per-net tree span; descriptive, not causal or board evidence',
                  research_complete=False,board_result=False)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps([dict(manifest=r['manifest'],baseline_path=r['baseline']['path_wirelength'],
                           candidate_path=r['candidate']['path_wirelength'],baseline_reuse=r['baseline']['path_per_unique_tree_ratio'],
                           candidate_reuse=r['candidate']['path_per_unique_tree_ratio']) for r in rows]))
