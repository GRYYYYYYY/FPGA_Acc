"""Independent original XML/Fraction SCC certificate, no native partition calls."""
import json
import sys
import xml.etree.ElementTree as ET
from array import array
from collections import Counter, deque
from pathlib import Path
from pre_route_endpoints import sha
from buffered_rc_node_classes import read, arc_delay

R = Path(__file__).resolve().parents[1]
D = R/'experiments/real_zero_rc_scc_v1_2026-10-08'/sys.argv[1]
receipt = json.loads((D/'receipt.json').read_text())
bindings = {**receipt['bindings'], **receipt['files'],
            str(D/'receipt.json'):sha(D/'receipt.json'),str(Path(__file__)):sha(Path(__file__))}
assert all(sha(p)==h for p,h in bindings.items())
graph = next(Path(p) for p in receipt['bindings'] if p.endswith('.xml'))
ids, classes, switches, digest = read(graph)
assert digest == bindings[str(graph)]
xml = ET.parse(graph).getroot()
cap = [int(n.get('capacity')) for n in xml.find('rr_nodes')]
labels = array('Q')
with (D/'components.bin').open('rb') as f:
    labels.fromfile(f,len(cap))
assert receipt['result']['byteorder']==sys.byteorder
assert (D/'components.bin').stat().st_size==len(cap)*labels.itemsize
groups = {}
for u,c in enumerate(cap):
    if c:
        groups.setdefault(labels[u],[]).append(u)
    else:
        assert labels[u] == 2**64-1
count = len(groups)
assert set(groups)==set(range(count))
forward, reverse = [[] for _ in cap], [[] for _ in cap]
dag = [set() for _ in range(count)]
zero_edges = internal_edges = 0
for edge in xml.find('rr_edges'):
    u,v,sid = (int(edge.get(k)) for k in ['src_node','sink_node','switch_id'])
    if not cap[u] or not cap[v] or arc_delay(classes,switches,ids[v],sid)!=0:
        continue
    zero_edges += 1
    a,b = labels[u],labels[v]
    if a==b:
        internal_edges += 1
        forward[u].append(v)
        reverse[v].append(u)
    else:
        dag[a].add(b)
for component,members in groups.items():
    for adjacency in [forward,reverse]:
        seen,todo = {members[0]},[members[0]]
        while todo:
            for v in adjacency[todo.pop()]:
                if v not in seen:
                    seen.add(v)
                    todo.append(v)
        assert len(seen)==len(members),component
indegree = [0]*count
for targets in dag:
    for v in targets:
        indegree[v] += 1
todo = deque(u for u,d in enumerate(indegree) if d==0)
visited = 0
while todo:
    u = todo.popleft()
    visited += 1
    for v in dag[u]:
        indegree[v] -= 1
        if indegree[v]==0:
            todo.append(v)
assert visited==count
sizes = [len(x) for x in groups.values()]
observed = dict(nodes=len(cap),enabled_nodes=sum(sizes),components=count,
    nontrivial_components=sum(s>1 for s in sizes),
    nodes_in_nontrivial_components=sum(s for s in sizes if s>1),
    largest_component=max(sizes,default=0),zero_edges=zero_edges,internal_zero_edges=internal_edges)
assert all(receipt['result'][k]==v for k,v in observed.items())
assert all(sha(p)==h for p,h in bindings.items())
result = dict(bindings=bindings, original_XML_fraction_partition_pass=True,
              all_components_strongly_connected=True, condensation_acyclic=True,
              census=observed, condensation_arcs=sum(map(len,dag)),
              scope='All original effective zero-cost arcs audited; physical path lifting and feedback-weighted quotient remain unproved')
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2))
