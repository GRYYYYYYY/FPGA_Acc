"""Export VPR channel lengths and compare full-tree sums with native reports."""
from pathlib import Path
import argparse
import array
import collections
import csv
import hashlib
import json
import sys
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rr_graph', type=Path)
    parser.add_argument('nodes', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--case', nargs=2, action='append', required=True)
    args = parser.parse_args()
    args.output.mkdir()
    refs = {}

    def sha(path):
        path = Path(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        refs[str(path.resolve())] = digest
        return digest

    assert args.nodes.stat().st_size % 8 == 0
    count = args.nodes.stat().st_size // 8
    weights = array.array('H', [0]) * count
    seen = set()
    parent = None
    for event, element in ET.iterparse(args.rr_graph, events=('start', 'end')):
        if event == 'start' and element.tag == 'rr_nodes':
            parent = element
        elif event == 'end' and element.tag == 'node' and parent is not None:
            node = int(element.attrib['id'])
            assert 0 <= node < count and node not in seen
            seen.add(node)
            if element.attrib['type'] in ['CHANX', 'CHANY']:
                loc = element.find('loc').attrib
                if element.attrib.get('direction') != 'NONE':
                    weights[node] = 1 + int(loc['xhigh']) - int(loc['xlow']) + int(loc['yhigh']) - int(loc['ylow'])
            element.clear()
            parent.remove(element)
        elif event == 'end' and element.tag == 'rr_nodes':
            break
    assert len(seen) == count
    graph_hash = sha(args.rr_graph)
    results = []
    for tree_name, validation_name in args.case:
        nets = collections.defaultdict(set)
        with Path(tree_name).open() as stream:
            for row in csv.DictReader(stream):
                nets[int(row['net_id'])].update(int(row[k]) for k in ['source', 'parent', 'child'])
        computed = sum(weights[node] for nodes in nets.values() for node in nodes)
        validation = json.loads(Path(validation_name).read_text())
        assert validation['legal'] and validation['inputs']['rr_graph_sha256'] == graph_hash
        assert computed == validation['total_wirelength'], (tree_name, computed, validation['total_wirelength'])
        results.append({'tree': tree_name, 'computed_wirelength': computed,
                        'native_wirelength': validation['total_wirelength']})
        sha(tree_name)
        sha(validation_name)
    if sys.byteorder != 'little':
        weights.byteswap()
    target = args.output / 'node_wirelength.u16'
    target.write_bytes(weights.tobytes())
    sha(target)
    sha(args.nodes)
    sha(Path(__file__).resolve())
    source = Path(__file__).resolve().parents[1] / 'work/vpr_source_bound_four_layer_build_20261020/source_vtr'
    for name in ['vpr/src/base/stats.cpp', 'libs/librrgraph/src/base/rr_graph_view.h']:
        sha(source / name)
    result = {'status': 'RR_channel_weights_match_all_observed_native_wirelengths',
              'nodes': count, 'cases': results, 'weights': str(target.resolve()),
              'source_sha256': refs, 'research_complete': False,
              'scope': 'VPR CHANX/CHANY node_length including NONE-direction zero wires. Net-deduplicated full-tree sums on specified native legal routes. Not proof of search quality or all-input equivalence.'}
    (args.output / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'nodes': count, 'cases': results}))


if __name__ == '__main__':
    main()
