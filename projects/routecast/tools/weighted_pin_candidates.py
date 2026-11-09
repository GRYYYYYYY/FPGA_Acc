"""Dijkstra candidates under explicit immutable nonnegative integer arc costs."""
import heapq
from reachable_pin_candidates import ReachablePins

class WeightedPins(ReachablePins):
 def query(self,source,sink,source_ptc,edge_costs,blocked_nodes=(),blocked_edges=(),target_pins=None):
  if type(source) is not int or source not in self.catalog.sources:raise ValueError('invalid SOURCE')
  if type(sink) is not int or sink not in self.catalog.sinks:raise ValueError('invalid SINK')
  if type(source_ptc) is not int or source_ptc not in self.catalog.sources[source].physical_pins:raise ValueError('invalid source pin')
  blocked=frozenset(blocked_nodes)
  if any(type(n) is not int or n not in self.graph.nodes or self.graph.nodes[n].type not in {'CHANX','CHANY'} for n in blocked):raise ValueError('blocked resource must be a known channel')
  forbidden=frozenset(blocked_edges)
  if any(type(e) is not int or not 0<=e<len(self.graph.edges) for e in forbidden):raise ValueError("blocked arc must be a known edge ID")
  costs=tuple(edge_costs)
  if len(costs)!=len(self.graph.edges) or any(type(c) is not int or c<0 for c in costs):raise ValueError('invalid arc costs')
  opins=set(self.catalog.sources[source].physical_pins[source_ptc]);targets={rr:p for p,facets in self.catalog.sinks[sink].physical_pins.items() for rr in facets}
  requested=None if target_pins is None else frozenset(target_pins)
  if requested is not None and (not requested or any(type(p) is not int or p not in self.catalog.sinks[sink].physical_pins for p in requested)):raise ValueError('target pins must be nonempty known physical pin IDs')
  if requested is not None:targets={n:p for n,p in targets.items() if p in requested}
  # Sink arcs are charged too; each facet is a terminal, not transit resource.
  terminal={}
  for n in targets:
   arcs=[(costs[e],e) for e in self.outgoing[n] if self.graph.edges[e].sink==sink and e not in forbidden]
   if arcs:terminal[n]=min(arcs)
  targets={n:p for n,p in targets.items() if n in terminal}
  dist={source:0};parent={};queue=[(0,source)];settled=set();best={};examined=0
  while queue:
   # Nonnegative terminal costs: no unsettled distance above every best
   # terminal cost can improve a requested pin. Exhaust equal-cost frontier
   # to preserve the deterministic facet/terminal tie rule.
   if requested is not None and requested<=best.keys() and queue[0][0]>max(best[p][0] for p in requested):break
   value,node=heapq.heappop(queue)
   if node in settled or dist[node]!=value:continue
   settled.add(node)
   if node in targets:
    p=targets[node];tail,eid=terminal[node];key=(value+tail,node,eid)
    if p not in best or key<best[p]:best[p]=key
    continue
   for eid in self.outgoing[node]:
    if eid in forbidden:continue
    examined+=1;edge=self.graph.edges[eid];dest=edge.sink;kind=self.graph.nodes[dest].type
    allowed=dest in opins if node==source else kind in {'CHANX','CHANY'} or dest in targets
    if not allowed or dest in blocked or self.graph.nodes[dest].capacity<=0 or dest in settled:continue
    candidate=value+costs[eid]
    if dest not in dist or candidate<dist[dest]:
     dist[dest]=candidate;parent[dest]=eid;heapq.heappush(queue,(candidate,dest))
  paths={};values={}
  for p,(value,node,tail) in sorted(best.items()):
   path=[tail];cursor=node
   while cursor!=source:
    eid=parent[cursor];path.append(eid);cursor=self.graph.edges[eid].source
   path.reverse();w=self.catalog.witness(source,sink,path);assert w['selected_opin_ptc']==source_ptc and w['selected_ipin_ptc']==p
   assert sum(costs[e] for e in path)==value;paths[p]=path;values[p]=value
  return {'paths':paths,'costs':values,'settled_nodes':len(settled),'examined_edges':examined,'scope':'fixed SOURCE pin, minimal supplied additive arc costs per physical target pin; no joint congestion or timing legality'}
