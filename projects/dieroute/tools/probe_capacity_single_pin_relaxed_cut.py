"""Posterior single-conflict reachability probe; not a general router or holdout."""
import collections
import heapq
import csv
import hashlib
import json
from pathlib import Path
import sys
import time
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[1]
T = R / 'work/sb_development_roundtrip_preflight_20261015/tools'
sys.path.insert(0, str(T))
from export_native_vpr_tree import extract
from vpr_route_connections import convert
from write_vpr_route import write_route


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for b in iter(lambda: stream.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def main():
    started = time.monotonic_ns()
    case = R / 'work/native_capacity_coverage_20261017/frisc_20x16_seed1'
    out = R / 'work/native_single_pin_relaxed_cut_probe_20261017'
    out.mkdir(exist_ok=False)
    prior_file = R / 'work/native_capacity_failure_nodes_20261017/audit.json'
    prior = json.loads(prior_file.read_text())['cases'][0]
    assert prior['case'] == 'frisc' and prior['width'] == 20
    assert len(prior['conflicts']) == 1 and prior['conflicts'][0]['printed_type'] == 'IPIN'
    conflict = prior['conflicts'][0]['node']
    net = max(prior['conflicts'][0]['distinct_route_nets'])
    files = [case / n for n in ['circuit.route', 'rr_graph.xml', 'circuit.net', 'circuit.place', 'architecture.xml', 'circuit.blif']]
    files += [prior_file, Path(__file__).resolve(), *[T / n for n in ['export_native_vpr_tree.py', 'vpr_route_connections.py', 'write_vpr_route.py']]]
    protocol = dict(status='frozen_before_probe',conflict=conflict,net=net,rule='One printed IPIN conflict; retain smaller net ID, reroute larger net ID via deterministic multi-source BFS from its existing tree to an unused IPIN feeding the same SINK. Relax other-net full resources with unit cost per saturated resource entry; still exclude other terminals and the conflicted IPIN. Minimize this entry count, not distinct nets. Do not change any other net.',source_sha256={str(p):sha(p) for p in files},scope=__doc__,research_complete=False)
    (out / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    trees = extract(case / 'circuit.route')
    occupancy = collections.defaultdict(set)
    for n, tree in trees.items():
        for node in {tree['source']} | {v for edge in tree['edges'] for v in edge[:2]}:
            occupancy[node].add(n)
    tree = trees[net]
    successors = [b for a,b,_ in tree['edges'] if a == conflict]
    assert len(successors) == 1
    sink = successors[0]
    adjacency = collections.defaultdict(list)
    kind = {}
    capacity = {}
    for _, element in ET.iterparse(case / 'rr_graph.xml', events=('end',)):
        if element.tag == 'node':
            n = int(element.attrib['id']); kind[n] = element.attrib['type']; capacity[n] = int(element.attrib['capacity']); element.clear()
        elif element.tag == 'edge':
            a,b,s = [int(element.attrib[k]) for k in ['src_node','sink_node','switch_id']]
            adjacency[a].append((b,s)); element.clear()
    assert kind[sink] == 'SINK'
    goals = {a for a,edges in adjacency.items() if kind[a] == 'IPIN' and not occupancy[a] and any(b == sink for b,_ in edges)}
    assert goals
    original = list(tree['edges'])
    remaining = [(a,b,s) for a,b,s in original if a != conflict and b != conflict and b != sink]
    starts = {tree['source']} | {v for edge in remaining for v in edge[:2]}
    queue = [(0,n) for n in sorted(starts)]; heapq.heapify(queue)
    previous = {n:None for n in starts}; distance={n:0 for n in starts}; reached=None
    while queue:
        cost,a=heapq.heappop(queue)
        if cost!=distance[a]:continue
        if a in goals:
            reached=a;break
        for b,s in adjacency[a]:
            if b==conflict:continue
            if kind[b] in ['SOURCE','OPIN','SINK'] or (kind[b]=='IPIN' and b not in goals):continue
            trial=cost+int(len(occupancy[b]-{net})>=capacity[b])
            if trial>=distance.get(b,10**30):continue
            distance[b]=trial;previous[b]=(a,s);heapq.heappush(queue,(trial,b))
    result = dict(status='no_path_even_with_relaxed_capacity' if reached is None else 'minimum_saturated_resource_entry_path_found',net=net,conflict=conflict,sink=sink,unused_direct_ipins=len(goals),visited=len(previous),research_complete=False,scope='Posterior one-connection relaxed graph diagnostic. Optimal saturated-entry count under stated terminal restrictions, not minimal distinct blocking nets or a legal repaired route; no writeback.')
    if reached is not None:
        path=[];node=reached
        while previous[node] is not None:
            parent,s=previous[node];path.append((parent,node,s));node=parent
        path.reverse()
        blockers=[dict(node=b,type=kind[b],other_nets=sorted(occupancy[b]-{net}),capacity=capacity[b]) for _,b,_ in path if len(occupancy[b]-{net})>=capacity[b]]
        assert len(blockers)==distance[reached]
        result.update(path=path,minimum_saturated_entries=distance[reached],blocking_resources=blockers,blocking_nets=sorted({n for row in blockers for n in row['other_nets']}))
    result['wall_ns']=time.monotonic_ns()-started
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
