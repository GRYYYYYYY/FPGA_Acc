"""One frozen channel-pressure pass on normalized RC+base; own net included.

Add round(scale/2 * base/norm * max(0,demand-capacity+1)). Pressure factor=1,
channel destinations only. No history or moving demand; not native router parity.
"""
from fractions import Fraction
from types import MappingProxyType
import hashlib,json
from normalized_rc_base import NormalizedRCBaseSketch
from native_indexed_cost import parse_cost_echo

class NormalizedRCPressureSketch(NormalizedRCBaseSketch):
 def __init__(self,graph,text,table_graph_sha256,demand,demand_graph_sha256,scale=10**6):
  if demand_graph_sha256!=graph.sha256:raise ValueError('demand graph mismatch')
  snapshot={}
  for nid,value in demand.items():
   if type(nid) is not int or nid not in graph.nodes or type(value) is not int or value<0:raise ValueError('invalid demand')
   if value:snapshot[nid]=value
  super().__init__(graph,text,table_graph_sha256,scale)
  norm,rows=parse_cost_echo(text);base={r['type']:Fraction(r['base'])/Fraction(norm) for r in rows.values()}
  penalties={n:round(base[node.type]*max(0,snapshot.get(n,0)-node.capacity+1)*scale/2) if node.type in {'CHANX','CHANY'} and node.capacity else 0 for n,node in graph.nodes.items()}
  self.outgoing={n:tuple((eid,dst,None if weight is None else weight+penalties[dst]) for eid,dst,weight in arcs) for n,arcs in self.outgoing.items()}
  self.demand=MappingProxyType(snapshot)
  context={'graph':graph.sha256,'table':hashlib.sha256(text.encode()).hexdigest(),'scale':scale,'rule':'halfbase_times_max0_demand-cap+1_channel_factor1_selfincluded','demand':sorted(snapshot.items())}
  self.context_sha256=hashlib.sha256(json.dumps(context,sort_keys=True).encode()).hexdigest()
