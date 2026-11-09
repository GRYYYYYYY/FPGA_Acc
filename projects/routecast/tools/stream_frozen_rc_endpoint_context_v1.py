"""Build CSR and exact buffered electrical classes from one authenticated XML parse."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from collections import defaultdict
from types import MappingProxyType
from cached_rr_endpoint_context_classes import FrozenNode
from pre_route_endpoints import sha
from path_rc import number
from csr_exact_buffered_rc import ExactBufferedRC
from class_cached_integer_rc_v1 import IntegerRC

def load_endpoints(endpoint_path):
 endpoint=json.loads(Path(endpoint_path).read_text());assert all(sha(v['path'])==v['sha256'] for v in endpoint['inputs'].values());graph=Path(endpoint['inputs']['graph']['path']);digest=sha(graph);assert digest==endpoint['graph_sha256'];nodes=[];switch_elements=[];adj=defaultdict(list);stack=[];frozen_children={};eid=0
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':
   stack.append(e)
   if len(stack)==1 and e.tag!='rr_graph':raise ValueError('Expected RR root')
   continue
  parent=stack[-2].tag if len(stack)>1 else None
  in_nodes=any(x.tag=='rr_nodes' for x in stack)
  if in_nodes and e.tag!='rr_nodes':
   frozen=FrozenNode(e.tag,MappingProxyType(dict(e.attrib)),tuple(frozen_children.pop(id(e),())))
   if parent=='rr_nodes':nodes.append(frozen)
   else:frozen_children.setdefault(id(stack[-2]),[]).append(frozen)
   stack[-2].remove(e);e.clear()
  elif e.tag=='switch' and parent=='switches':
   switch_elements.append(e);stack[-2].remove(e)
  elif e.tag=='edge' and parent=='rr_edges':
   adj[int(e.get('src_node'))].append((int(e.get('sink_node')),int(e.get('switch_id')),eid));eid+=1
   stack[-2].remove(e);e.clear()
  elif e.tag=='segment' and parent=='segments':stack[-2].remove(e);e.clear()
  stack.pop()
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
 for e in switch_elements:
  if e.tag!='switch':continue
  sid=int(e.get('id'));timing=e.find('timing')
  if sid<0 or sid in switches or timing is None:raise ValueError('invalid switch')
  if e.get('type') not in {'buffer','mux','tristate'}:raise ValueError('nonbuffered switch')
  if number(timing.get('Cinternal','0')):raise ValueError('nonzero Cinternal')
  switches[sid]=(number(timing.get('R','0')),number(timing.get('Tdel','0')))
 if not indices or not switches:raise ValueError('empty electrical context')
 if sha(graph)!=digest:raise ValueError('graph changed')
 rc=IntegerRC(ExactBufferedRC(fields,indices,classes,switches));return graph,digest,nodes,fields,rc,endpoint['connections']
