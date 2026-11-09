"""Build CSR and exact buffered electrical classes from one authenticated XML parse."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from collections import defaultdict
from pre_route_endpoints import sha
from path_rc import number
from csr_exact_buffered_rc import ExactBufferedRC
from direct_index_integer_rc_v1 import IntegerRC

def load_endpoints(endpoint_path):
 endpoint=json.loads(Path(endpoint_path).read_text());assert all(sha(v['path'])==v['sha256'] for v in endpoint['inputs'].values());graph=Path(endpoint['inputs']['graph']['path']);digest=sha(graph);assert digest==endpoint['graph_sha256'];xml=ET.parse(graph).getroot();assert xml.tag=='rr_graph';nodes=list(xml.find('rr_nodes'));adj=defaultdict(list)
 for eid,e in enumerate(xml.find('rr_edges')):adj[int(e.get('src_node'))].append((int(e.get('sink_node')),int(e.get('switch_id')),eid))
 fields={name:array('Q') for name in ('node_ids','row_offsets','dest_ranks','edge_ids','switch_ids','costs','capacities')};fields['node_ids'].extend(range(len(nodes)));fields['capacities'].extend(int(n.get('capacity')) for n in nodes);fields['row_offsets'].append(0)
 for u in range(len(nodes)):
  for v,s,eid in adj[u]:fields['dest_ranks'].append(v);fields['switch_ids'].append(s);fields['edge_ids'].append(eid);fields['costs'].append(1)
  fields['row_offsets'].append(len(fields['edge_ids']))
 indices=array('Q');classes=[];lookup={};switches={}
 for i,node in enumerate(nodes):
  if node.get('id')!=str(i):raise ValueError('contiguous node IDs required')
  timing=node.find('timing')
  if timing is None or not {'R','C'}<=set(timing.attrib):raise ValueError('missing node RC')
  key=(timing.get('R'),timing.get('C'))
  if key not in lookup:lookup[key]=len(classes);classes.append(tuple(map(number,key)))
  indices.append(lookup[key])
 for e in xml.find('switches'):
  if e.tag!='switch':continue
  sid=int(e.get('id'));timing=e.find('timing')
  if sid<0 or sid in switches or timing is None:raise ValueError('invalid switch')
  if e.get('type') not in {'buffer','mux','tristate'}:raise ValueError('nonbuffered switch')
  if number(timing.get('Cinternal','0')):raise ValueError('nonzero Cinternal')
  switches[sid]=(number(timing.get('R','0')),number(timing.get('Tdel','0')))
 if not indices or not switches:raise ValueError('empty electrical context')
 if sha(graph)!=digest:raise ValueError('graph changed')
 rc=IntegerRC(ExactBufferedRC(fields,indices,classes,switches));return graph,digest,nodes,fields,rc,endpoint['connections']
