"""Compare selected terminal geometry against uncongested shortest-span bounds."""
import csv
import hashlib
import heapq
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from profile_rr_tree_reuse import native_parents

root=Path(__file__).resolve().parents[1]
diagnostic=root/'work/rr_cleanup_limits_profile_20261014.json'
limits=json.loads(diagnostic.read_text())
selected=[r['net_id'] for r in limits['net_deltas'][:5]]
pair=root/'work/rr_pair_ex5p_wide_cleanup_v1_20261014'
manifest=pair/'pair.json'
m=json.loads(manifest.read_text());case=Path(m['case'])
connections=Path(m['reference'])/'connections.csv'
with connections.open() as f:tasks=[r for r in csv.DictReader(f) if int(r['net_id']) in selected]
spans={};adj={}
for _,element in ET.iterparse(case/'rr_graph.xml',events=('end',)):
    if element.tag=='node':
        node=int(element.attrib['id']);span=0
        if element.attrib['type'] in ('CHANX','CHANY'):
            axis='x' if element.attrib['type']=='CHANX' else 'y';loc=element.find('loc')
            span=int(loc.attrib[axis+'high'])-int(loc.attrib[axis+'low'])+1
        spans[node]=span;element.clear()
    elif element.tag=='edge':
        adj.setdefault(int(element.attrib['src_node']),set()).add(int(element.attrib['sink_node']))
        element.clear()
baseline=native_parents(case/'circuit.route')
candidate=native_parents(pair/'downstream_bounded.route')

def chain_length(tree,source,sink):
    seen=set();length=0;node=sink
    while node!=source:
        assert node not in seen and node in tree
        seen.add(node);parent=tree[node]
        assert parent is not None and node in adj.get(parent,set())
        length+=spans[node];node=parent
    return length

rows=[]
for net in selected:
    group=[t for t in tasks if int(t['net_id'])==net]
    sources={int(t['source']) for t in group};assert len(sources)==1
    source=sources.pop();distance={source:0};queue=[(0,source)];predecessor={}
    while queue:
        cost,node=heapq.heappop(queue)
        if cost!=distance[node]:continue
        for child in adj.get(node,()):
            trial=cost+spans[child]
            if trial<distance.get(child,float('inf')):
                distance[child]=trial;predecessor[child]=node;heapq.heappush(queue,(trial,child))
    # Bellman inequalities plus actual shortest-path witnesses certify the bound.
    checked_arcs=0
    for node,cost in distance.items():
        for child in adj.get(node,()):
            assert child in distance and distance[child]<=cost+spans[child]
            checked_arcs+=1
    terminal=[]
    for task in group:
        sink=int(task['sink']);bound=distance[sink]
        witness=chain_length(predecessor,source,sink)
        assert witness==bound
        old=chain_length(baseline[net],source,sink)
        new=chain_length(candidate[net],source,sink)
        assert old>=bound and new>=bound
        terminal.append(dict(task_id=int(task['id']),sink=sink,lower_bound=bound,
                             baseline_span=old,candidate_span=new,delta=new-old))
    terminal.sort(key=lambda r:(-r['delta'],r['task_id']))
    rows.append(dict(net_id=net,connections=len(group),
                     baseline_path_sum=sum(r['baseline_span'] for r in terminal),
                     candidate_path_sum=sum(r['candidate_span'] for r in terminal),
                     uncongested_lower_bound_sum=sum(r['lower_bound'] for r in terminal),
                     longer=sum(r['delta']>0 for r in terminal),shorter=sum(r['delta']<0 for r in terminal),
                     bound_checked_arcs=checked_arcs,terminals=terminal))
files=[Path(__file__),root/'tools/profile_rr_tree_reuse.py',diagnostic,manifest,
       case/'rr_graph.xml',case/'circuit.route',pair/'downstream_bounded.route',connections]
report=dict(status='native_paths_and_shortest_span_bounds_verified',nets=rows,
            scope='Five largest excess-wirelength nets selected on ex5p development data. Directed graph bound ignores timing, congestion, sharing and die restrictions; it is not a legal joint routing solution or an optimality claim.',
            source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            research_complete=False,board_result=False)
output=root/'work/rr_ex5p_path_detours_certified_20261014.json'
assert not output.exists()
output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items() if k!='terminals'} for r in rows]))
