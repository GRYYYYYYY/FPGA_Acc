"""Per-net own union exclusion, same frozen normalized halfbase pressure rule."""
from fractions import Fraction
import hashlib
from normalized_rc_base import NormalizedRCBaseSketch
from native_indexed_cost import parse_cost_echo
from net_pressure_sketch import NetPressure,net_union

class NormalizedRCNetPressure(NetPressure):
 def __init__(self,graph,text,table_graph_sha256,prediction,scale=10**6):
  self.users,self.demand=net_union(graph,prediction)
  self.roots={r['net_id']:r['source'] for r in prediction['connections']}
  self.base=NormalizedRCBaseSketch(graph,text,table_graph_sha256,scale)
  norm,rows=parse_cost_echo(text);base={r['type']:Fraction(r['base'])/Fraction(norm) for r in rows.values()}
  self.full={};self.reduced={}
  for n,node in graph.nodes.items():
   channel=node.capacity>0 and node.type in {'CHANX','CHANY'};d=self.demand.get(n,0)
   self.full[n]=round(base[node.type]*max(0,d-node.capacity+1)*scale/2) if channel else 0
   self.reduced[n]=round(base[node.type]*max(0,max(0,d-1)-node.capacity+1)*scale/2) if channel else 0
  self.identity={'graph':graph.sha256,'table':hashlib.sha256(text.encode()).hexdigest(),'scale':scale,'rule':'halfbase_channel_factor1_frozen','demand':sorted(self.demand.items())}
 def query(self,net,source,sinks,exclude=True):
  if net not in self.roots or source!=self.roots[net]:raise ValueError('net source mismatch')
  return super().query(net,source,sinks,exclude)
