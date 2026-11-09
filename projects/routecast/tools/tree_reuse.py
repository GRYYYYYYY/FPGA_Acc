"""Frozen-cost, ascending-SINK route-tree reuse reference (not native VPR).

Existing tree nodes seed searches with rounded accumulated timing only. New
arcs pay the frozen full weight. New branches cannot reenter the tree, which
preserves one parent per node. Failed branches leave the committed tree intact.
All-buffered RC validation and units belong to the caller's cost adapter.
"""
from dataclasses import dataclass
from fractions import Fraction
import heapq

@dataclass
class TreeResult:
 paths: dict
 parents: dict
 failures: tuple
 edge_visits: int
 settled_nodes: int

class TreeReuse:
 def __init__(self,graph,weights,timing):
  if len(weights)!=len(graph.edges) or len(timing)!=len(graph.edges):raise ValueError('edge cost cardinality')
  self.graph=graph;self.weights=tuple(weights);self.timing=tuple(timing);self.arcs={n:[] for n in graph.nodes}
  for eid,edge in enumerate(graph.edges):
   w=self.weights[eid];t=self.timing[eid]
   if w is not None and (type(w) is not int or w<0):raise ValueError('invalid full edge weight')
   if type(t) not in (int,Fraction) or t<0:raise ValueError('invalid timing weight')
   self.arcs[edge.source].append((eid,edge.sink,w))
  self.arcs={n:tuple(a) for n,a in self.arcs.items()}
 def route(self,source,sinks):
  g=self.graph;sinks=set(sinks)
  if type(source) is not int or source not in g.nodes or g.nodes[source].type!='SOURCE' or any(type(s) is not int or s not in g.nodes or g.nodes[s].type!='SINK' for s in sinks):raise ValueError('invalid endpoints')
  if not g.nodes[source].capacity:return TreeResult({}, {},tuple(sorted(sinks)),0,0)
  prefixes={source:()};arrivals={source:Fraction(0)};parents={};paths={};failures=[];visits=0;total_settled=0
  for sink in sorted(sinks):
   if sink in prefixes:paths[sink]=prefixes[sink];continue
   best={n:(round(arrivals[n]),len(p),p) for n,p in prefixes.items()};queue=[(*score,n) for n,score in best.items()];heapq.heapify(queue);settled=set();found=None
   while queue:
    cost,hops,path,node=heapq.heappop(queue)
    if node in settled or best[node]!=(cost,hops,path):continue
    settled.add(node)
    if node==sink:found=path;break
    for eid,dst,w in self.arcs[node]:
     visits+=1
     if w is None or not g.nodes[dst].capacity or dst in prefixes or dst in settled:continue
     candidate=(cost+w,hops+1,path+(eid,))
     if dst not in best or candidate<best[dst]:best[dst]=candidate;heapq.heappush(queue,(*candidate,dst))
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
