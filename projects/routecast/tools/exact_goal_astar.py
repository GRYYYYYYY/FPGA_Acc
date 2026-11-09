"""Canonical independent-source A* on immutable full-budget arc snapshots.

Directed bbox expansion bounds heuristic drop. A fixed >16-target fallback
uses zero heuristic to avoid expensive many-target minima, changing work only.
No costs, endpoint order, route-tree prefix semantics or labels are changed.
"""
import heapq
from types import MappingProxyType
from semantic_sketch import SearchResult

class ExactGoalAStar:
 def __init__(self,engine):
  g=engine.graph
  if engine.node_budget<len(g.nodes):raise ValueError('exact wrapper requires full physical node budget')
  self.graph=g;self.outgoing=MappingProxyType(dict(engine.outgoing));self.boxes={};pool={};alpha=None
  for n,node in g.nodes.items():
   loc=dict(node.location);box=tuple(int(loc[k]) for k in ('xlow','xhigh','ylow','yhigh'));self.boxes[n]=pool.setdefault(box,box)
  for n,arcs in self.outgoing.items():
   if g.nodes[n].type=='SINK' and arcs:raise ValueError('terminal SINKs required')
   a=self.boxes[n]
   for eid,dst,w in arcs:
    if w is not None and (type(w) is not int or w<0):raise ValueError('invalid frozen edge weight')
    if w is None or not g.nodes[n].capacity or not g.nodes[dst].capacity:continue
    b=self.boxes[dst]
    # If the terminal target contains its predecessor, both heuristics are zero.
    if g.nodes[dst].type=='SINK' and b[0]<=a[0]<=a[1]<=b[1] and b[2]<=a[2]<=a[3]<=b[3]:continue
    displacement=max(a[0]-b[0],b[1]-a[1],0)+max(a[2]-b[2],b[3]-a[3],0)
    if displacement:alpha=w//displacement if alpha is None else min(alpha,w//displacement)
  self.alpha=alpha or 0;self.bbox_classes=len(pool)
 def heuristic(self,sinks):
  if self.alpha==0 or len(sinks)>16:return lambda n:0
  targets=[self.boxes[n] for n in sorted(sinks)];cache={};alpha=self.alpha
  def h(n):
   b=self.boxes[n]
   if b not in cache:cache[b]=alpha*min(max(t[0]-b[1],b[0]-t[1],0)+max(t[2]-b[3],b[2]-t[3],0) for t in targets)
   return cache[b]
  return h
 def search(self,source,sinks):
  g=self.graph;sinks=set(sinks)
  if source not in g.nodes or g.nodes[source].type!='SOURCE' or any(s not in g.nodes or g.nodes[s].type!='SINK' for s in sinks):raise ValueError('invalid endpoints')
  if not g.nodes[source].capacity or not sinks:return SearchResult({},0,0,False)
  h=self.heuristic(sinks);best={source:(0,0,())};queue=[(h(source),0,0,(),source)];settled=set();paths={};visits=0
  while queue:
   _,cost,hops,path,node=heapq.heappop(queue)
   if node in settled or best[node]!=(cost,hops,path):continue
   settled.add(node)
   if node in sinks:
    paths[node]=path
    if len(paths)==len(sinks):break
   for eid,dst,w in self.outgoing[node]:
    visits+=1
    if w is None or dst in settled or (g.nodes[dst].type=='SINK' and dst not in sinks):continue
    candidate=(cost+w,hops+1,path+(eid,))
    if dst not in best or candidate<best[dst]:best[dst]=candidate;heapq.heappush(queue,(candidate[0]+h(dst),*candidate,dst))
  return SearchResult(paths,len(settled),visits,False)
