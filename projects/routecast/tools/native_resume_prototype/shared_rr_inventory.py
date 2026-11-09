"""Graph-bound physical inventory sharing an initialized exact CSR context."""
import xml.etree.ElementTree as ET
from types import MappingProxyType
from native_route_audit_cache import Snapshot
from pre_route_endpoints import sha
class SharedRRInventory:
 def __init__(self,ctx):
  self.graph=ctx.graph;self.digest=ctx.digest
  if sha(self.graph)!=self.digest:raise ValueError('graph changed')
  nodes={};switches=set();stack=[]
  for event,e in ET.iterparse(self.graph,events=('start','end')):
   if event=='start':stack.append(e);continue
   parent=stack[-2].tag if len(stack)>1 else None
   if e.tag=='node' and parent=='rr_nodes':
    nid=int(e.get('id'))
    if nid in nodes or nid>=ctx.n or int(e.get('capacity'))!=ctx.fields['capacities'][nid]:raise ValueError('node identity/capacity')
    nodes[nid]=(e.get('type'),MappingProxyType(dict(e.find('loc').attrib)))
   if e.tag=='switch' and parent=='switches':switches.add(int(e.get('id')))
   if (e.tag,parent) in {('node','rr_nodes'),('edge','rr_edges'),('switch','switches')}:stack[-2].remove(e);e.clear()
   stack.pop()
  if set(nodes)!=set(range(ctx.n)):raise ValueError('node coverage')
  f=ctx.fields;edges=[None]*len(f['edge_ids']);arcs={}
  for u in range(ctx.n):
   for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    eid=f['edge_ids'][slot];arc=(u,f['dest_ranks'][slot],f['switch_ids'][slot])
    if eid>=len(edges) or edges[eid] is not None or arc[2] not in switches:raise ValueError('edge identity')
    edges[eid]=arc;arcs[arc]=min(eid,arcs.get(arc,eid))
  if any(edge is None for edge in edges) or sha(self.graph)!=self.digest:raise ValueError('edge coverage/graph changed')
  self.nodes=MappingProxyType(nodes);self.edges=tuple(edges);self.snapshot=Snapshot(MappingProxyType({n:(kind,f['capacities'][n]) for n,(kind,loc) in nodes.items()}),frozenset(),MappingProxyType(arcs),frozenset(switches),len(edges))
 def validate(self,graph,digest):
  if str(graph)!=str(self.graph) or digest!=self.digest or sha(graph)!=digest:raise ValueError('inventory graph mismatch')
