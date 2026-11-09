"""Find graph witnesses for zero-delay direct-connect lookahead candidates.

This reads archived inputs only; it does not reconstruct the sampled MAP table.
"""
import collections
import csv
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'work/vpr_source_bound_initial_observation_build_20261015'

def main():
    graph_path = BUILD / 'native_repeat_0/rr_graph.xml'
    csv_path = BUILD / 'initial_timing_0.csv'
    graph = ET.parse(graph_path).getroot()
    nodes = {int(n.attrib['id']): n for n in graph.find('rr_nodes')}
    types = {i: n.attrib['type'] for i, n in nodes.items()}
    delays = {int(s.attrib['id']): float(s.find('timing').attrib.get('Tdel', 0))
              for s in graph.find('switches')}
    adjacent = collections.defaultdict(list)
    for edge in graph.find('rr_edges'):
        a = edge.attrib
        u, v, switch = (int(a[k]) for k in ['src_node', 'sink_node', 'switch_id'])
        if delays[switch] == 0 and types[u] in ['SOURCE', 'OPIN', 'IPIN'] and types[v] in ['OPIN', 'IPIN', 'SINK']:
            adjacent[u].append((v, switch))
    rows = list(csv.DictReader(csv_path.open()))
    assert len(rows) == 1920 and all(float(r['lookahead_delay_s']) == 0 for r in rows)
    witnesses = []
    uncovered = []
    for source in sorted({int(r['source_rr']) for r in rows}):
        assert types[source] == 'SOURCE'
        queue = collections.deque([source])
        parents = {source: None}
        reached = None
        while queue:
            u = queue.popleft()
            if types[u] == 'SINK':
                reached = u
                break
            for v, switch in adjacent[u]:
                if v not in parents:
                    parents[v] = (u, switch)
                    queue.append(v)
        if reached is None:
            uncovered.append(source)
            continue
        path, switches = [reached], []
        while path[-1] != source:
            parent, switch = parents[path[-1]]
            path.append(parent)
            switches.append(switch)
        path.reverse()
        switches.reverse()
        assert all(delays[s] == 0 for s in switches)
        witnesses.append({'source': source, 'sink': reached, 'path': path,
                          'types': [types[n] for n in path], 'switches': switches})
    files = [graph_path, csv_path, BUILD / 'native_repeat_0/vpr.log',
             BUILD / 'source_vtr/vpr/src/route/router_lookahead_map_utils.cpp',
             BUILD / 'source_vtr/vpr/src/route/router_lookahead_map.cpp',
             BUILD / 'source_vtr/vpr/src/route/route_net.cpp',
             BUILD / 'source_vtr/vpr/src/route/route_common.cpp', Path(__file__).resolve()]
    result = {'status': 'archived_graph_zero_switch_delay_direct_path_witnesses',
              'connections': len(rows), 'unique_sources': len(witnesses) + len(uncovered),
              'sources_with_witness': len(witnesses), 'witnesses': witnesses,
              'sources_without_witness': uncovered,
              'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
              'interpretation': 'MAP source/OPIN lookup considers direct SINK entries with zero wire cost, independent of queried target identity or displacement. Graph witnesses identify possible zero-delay candidates, not which entries were actually sampled into the runtime table.',
              'scope': 'Not a runtime table dump or complete causal explanation for all 1920 zeros. Switch Tdel only, not routed RC delay. No claim of zero physical delay, route legality, calibrated timing or changed live policy.',
              'research_complete': False}
    out = ROOT / 'work/initial_lookahead_zero_path_diagnosis_20261018'
    out.mkdir(exist_ok=False)
    (out / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['connections', 'unique_sources', 'sources_with_witness', 'sources_without_witness']}))

if __name__ == '__main__':
    main()
