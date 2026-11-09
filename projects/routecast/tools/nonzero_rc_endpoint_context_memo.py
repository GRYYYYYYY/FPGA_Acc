"""Full original XML nonzero-RC diagnostic context, without filesystem writes."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from collections import defaultdict
from pre_route_endpoints import sha
from buffered_rc_node_classes import read
from csr_exact_buffered_rc import ExactBufferedRC
from integer_rc_context_memo import IntegerRC

def load_endpoints(endpoint_path):
 endpoint=json.loads(Path(endpoint_path).read_text());assert all(sha(v['path'])==v['sha256'] for v in endpoint['inputs'].values());graph=Path(endpoint['inputs']['graph']['path']);assert sha(graph)==endpoint['graph_sha256'];xml=ET.parse(graph).getroot();nodes=list(xml.find('rr_nodes'));adj=defaultdict(list)
 for eid,e in enumerate(xml.find('rr_edges')):adj[int(e.get('src_node'))].append((int(e.get('sink_node')),int(e.get('switch_id')),eid))
 fields={name:array('Q') for name in ('node_ids','row_offsets','dest_ranks','edge_ids','switch_ids','costs','capacities')};fields['node_ids'].extend(range(len(nodes)));fields['capacities'].extend(int(n.get('capacity')) for n in nodes);fields['row_offsets'].append(0)
 for u in range(len(nodes)):
  for v,s,eid in adj[u]:fields['dest_ranks'].append(v);fields['switch_ids'].append(s);fields['edge_ids'].append(eid);fields['costs'].append(1)
  fields['row_offsets'].append(len(fields['edge_ids']))
 rc=IntegerRC(ExactBufferedRC(fields,*read(graph)[:3]));queries=endpoint['connections'];assert all(n.get('id')==str(i) for i,n in enumerate(nodes));return graph,sha(graph),nodes,fields,rc,queries
