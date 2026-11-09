"""Exact buffered RC/base cost cache by physical equivalence classes.

Only preparation changes: each edge is still checked, including disabled arcs.
The key includes switch ID, source R, destination R/C and explicit cost index.
Normalization, scale, table and graph are fixed for the model instance.
"""
from fractions import Fraction
from bound_indexed_cost import BoundIndexedCost
from path_rc import PathRC,State

class CachedBoundRC(BoundIndexedCost):
 def __init__(self,graph,text,bindings_csv,identity,scale=10**6):
  super().__init__(graph,text,bindings_csv,identity,scale);rc=PathRC(graph)
  if any(not s[0] for s in rc.switches.values()):raise ValueError('nonbuffered graph requires resistance state')
  source_classes={};destination_classes={};source_ids={};destination_ids={}
  for n,(r,c) in rc.nodes.items():
   source_ids[n]=source_classes.setdefault(r,len(source_classes));destination_ids[n]=destination_classes.setdefault((r,c),len(destination_classes))
  cache={};bases={i:Fraction(row['base']) for i,row in self.rows.items()};zero=State(Fraction(0),Fraction(0));queries=0
  def cost(eid):
   nonlocal queries
   queries+=1;e=graph.edges[eid];index=self.indices[e.sink];key=(e.switch_id,source_ids[e.source],destination_ids[e.sink],index)
   if key not in cache:
    delay=rc.step(zero,eid).delay
    if delay<0:raise ValueError('negative RC increment')
    cache[key]=round((delay+bases[index])/self.normalization*scale/2)
   return cache[key]
  outgoing={}
  for n,arcs in self.outgoing.items():
   result=[]
   for eid,dst,w in arcs:
    value=cost(eid);result.append((eid,dst,None if w is None else value))
   outgoing[n]=tuple(result)
  self.outgoing=outgoing;self.cache_entries=len(cache);self.edge_cost_queries=queries;self.source_R_classes=len(source_classes);self.destination_RC_classes=len(destination_classes)
  if queries!=len(graph.edges):raise AssertionError('edge coverage mismatch')
