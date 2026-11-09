"""Consistent bbox-distance A* for terminal-SINK frozen-cost tree reuse.

For nonterminal arcs, alpha <= weight / bbox endpoint displacement bound.
Terminal containment edges have zero heuristic drop to their target. Other
SINKs are dead ends and pruned. Queue order(f,g,hops,path) preserves canonical
cost/hops/edge-tuple choices. Geometry/weights are graph-only, no route labels.
"""
import heapq
from fractions import Fraction
from tree_reuse import TreeReuse,TreeResult

class AStarTreeReuse(TreeReuse):
 def __init__(self,graph,weights,timing):
  super().__init__(graph,weights,timing)
  self.boxes={}
  for n,node in graph.nodes.items():
   loc=dict(node.location);self.boxes[n]=tuple(int(loc[k]) for k in ('xlow','xhigh','ylow','yhigh'))
  ratios=[]
  for eid,e in enumerate(graph.edges):
   if graph.nodes[e.source].type=='SINK':raise ValueError('A* requires terminal SINKs')
   w=self.weights[eid]
   if w is None or not graph.nodes[e.source].capacity or not graph.nodes[e.sink].capacity:continue
   a=self.boxes[e.source];b=self.boxes[e.sink]
   contains=b[0]<=a[0]<=a[1]<=b[1] and b[2]<=a[2]<=a[3]<=b[3]
   if graph.nodes[e.sink].type=='SINK' and contains:continue
   displacement=max(abs(a[0]-b[0]),abs(a[1]-b[1]))+max(abs(a[2]-b[2]),abs(a[3]-b[3]))
   if displacement:ratios.append(w//displacement)
  self.alpha=min(ratios,default=0)
 def heuristic(self,sink):
  target=self.boxes[sink];cache={};alpha=self.alpha;boxes=self.boxes
  def estimate(node):
   if node not in cache:
    b=boxes[node];cache[node]=alpha*(max(target[0]-b[1],b[0]-target[1],0)+max(target[2]-b[3],b[2]-target[3],0))
   return cache[node]
  return estimate
 def route(self,source,sinks,penalties=None):
  g=self.graph;sinks=set(sinks)
  penalties={} if penalties is None else dict(penalties)
  if any(type(n) is not int or n not in g.nodes or type(v) is not int or v<0 for n,v in penalties.items()):raise ValueError('invalid nonnegative destination penalty')
  if type(source) is not int or source not in g.nodes or g.nodes[source].type!='SOURCE' or any(type(s) is not int or s not in g.nodes or g.nodes[s].type!='SINK' for s in sinks):raise ValueError('invalid endpoints')
  if not g.nodes[source].capacity:return TreeResult({}, {},tuple(sorted(sinks)),0,0)
  prefixes={source:()};arrivals={source:Fraction(0)};parents={};paths={};failures=[];visits=0;total_settled=0
  for sink in sorted(sinks):
   if sink in prefixes:paths[sink]=prefixes[sink];continue
   heuristic=self.heuristic(sink)
   best={n:(round(arrivals[n]),len(p),p) for n,p in prefixes.items()};queue=[(score[0]+heuristic(n),*score,n) for n,score in best.items()];heapq.heapify(queue);settled=set();found=None
   while queue:
    _,cost,hops,path,node=heapq.heappop(queue)
    if node in settled or best[node]!=(cost,hops,path):continue
    settled.add(node)
    if node==sink:found=path;break
    for eid,dst,w in self.arcs[node]:
     visits+=1
     if w is None or not g.nodes[dst].capacity or dst in prefixes or dst in settled or (g.nodes[dst].type=='SINK' and dst!=sink):continue
     candidate=(cost+w+penalties.get(dst,0),hops+1,path+(eid,))
     if dst not in best or candidate<best[dst]:best[dst]=candidate;heapq.heappush(queue,(candidate[0]+heuristic(dst),*candidate,dst))
   total_settled+=len(settled)
   if found is None:failures.append(sink);continue
   # Commit only after successful search; every new node has one raw parent.
   node=source;prefix=();arrival=Fraction(0)
   for eid in found:
    edge=g.edges[eid]
    if edge.source!=node:raise AssertionError('discontinuous branch')
    node=edge.sink;prefix+=(eid,);arrival+=self.timing[eid]
    if node in prefixes:
     if prefixes[node]!=prefix:raise AssertionError('tree reconvergence')
    else:prefixes[node]=prefix;arrivals[node]=arrival;parents[node]=eid
   paths[sink]=found
  return TreeResult(paths,parents,tuple(failures),visits,total_settled)
