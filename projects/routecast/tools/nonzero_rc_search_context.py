"""Full original XML nonzero-RC diagnostic context, without filesystem writes."""
import csv,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from collections import defaultdict
from pre_route_endpoints import sha
from buffered_rc_node_classes import read
from csr_exact_buffered_rc import ExactBufferedRC
from integer_rc_context import IntegerRC

def load(root):
 work=Path(root)/'work/nonzero_rc_fanout_observable64_2026-10-06';graph=work/'rr_graph.xml';xml=ET.parse(graph).getroot();nodes=list(xml.find('rr_nodes'));adj=defaultdict(list)
 for eid,e in enumerate(xml.find('rr_edges')):adj[int(e.get('src_node'))].append((int(e.get('sink_node')),int(e.get('switch_id')),eid))
 fields={name:array('Q') for name in ('node_ids','row_offsets','dest_ranks','edge_ids','switch_ids','costs','capacities')};fields['node_ids'].extend(range(len(nodes)));fields['capacities'].extend(int(n.get('capacity')) for n in nodes);fields['row_offsets'].append(0)
 for u in range(len(nodes)):
  for v,s,eid in adj[u]:fields['dest_ranks'].append(v);fields['switch_ids'].append(s);fields['edge_ids'].append(eid);fields['costs'].append(1)
  fields['row_offsets'].append(len(fields['edge_ids']))
 rc=IntegerRC(ExactBufferedRC(fields,*read(graph)[:3]));rows=list(csv.DictReader((work/'before_sync.delays.tsv').open(),delimiter='\t'));unions=defaultdict(set);roots={};queries=[]
 for row in rows:
  net=int(row['net']);node=int(row['node']);unions[net].add(node)
  if nodes[node].get('type')=='SOURCE':assert net not in roots;roots[net]=node
  if int(row['pin'])>0:queries.append({'net_id':net,'pin_index':int(row['pin']),'source':None,'sink':node})
 for q in queries:q['source']=roots[q['net_id']]
 return graph,sha(graph),nodes,fields,rc,sorted(queries,key=lambda q:(q['net_id'],q['pin_index'])),unions
