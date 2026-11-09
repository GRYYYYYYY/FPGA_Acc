"""Necessary edge region for nonnegative additive RC delay budgets.

Every budget-feasible walk is inside this region. Equal edge costs throughout
it preserve the constrained mathematical optimum, not bounded-search counters
or canonical tie paths. Context authentication and nonnegative costs are caller
responsibilities; this diagnostic caches distances and regions in host memory.
"""
import heapq

class RCFeasibleCostRegion:
 def __init__(self, nodes, edges):
  self.forward=[[] for _ in range(nodes)];self.reverse=[[] for _ in range(nodes)];self.edges=[];self.distances={};self.regions={}
  for u,v,delay,cost in edges:
   if type(u) is not int or type(v) is not int or not 0<=u<nodes or not 0<=v<nodes or type(delay) is not int or delay<0 or type(cost) is not int or cost<0:raise ValueError('invalid exact edge')
   self.edges.append((u,v,delay,cost));self.forward[u].append((v,delay));self.reverse[v].append((u,delay))
 def distance(self,node,reverse=False):
  key=(node,reverse)
  if key not in self.distances:
   adjacency=self.reverse if reverse else self.forward;distance={node:0};heap=[(0,node)]
   while heap:
    value,u=heapq.heappop(heap)
    if distance[u]!=value:continue
    for v,delay in adjacency[u]:
     candidate=value+delay
     if v not in distance or candidate<distance[v]:distance[v]=candidate;heapq.heappush(heap,(candidate,v))
   self.distances[key]=distance
  return self.distances[key]
 def destinations(self,source,sink,initial,budget):
  if any(type(n) is not int or not 0<=n<len(self.forward) for n in (source,sink)) or any(type(x) is not int or x<0 for x in (initial,budget)):raise ValueError('invalid query context')
  key=(source,sink,initial,budget)
  if key not in self.regions:
   a=self.distance(source);b=self.distance(sink,True)
   self.regions[key]=frozenset(v for u,v,d,c in self.edges if c>0 and u in a and v in b and initial+a[u]+d+b[v]<=budget)
  return self.regions[key]

 def prefix_destinations(self,source,initial,budget):
  """All positive-cost destinations read from any budget-reachable prefix.

  Includes edges whose new delay exceeds budget: native arithmetic checks run
  before that rejection. Equal costs here preserve deterministic bounded search
  results/counters for the same sink, limit and immutable context.
  """
  if type(source) is not int or not 0<=source<len(self.forward) or any(type(x) is not int or x<0 for x in (initial,budget)):raise ValueError('invalid query context')
  key=('prefix',source,initial,budget)
  if key not in self.regions:
   a=self.distance(source)
   self.regions[key]=frozenset(v for u,v,d,c in self.edges if c>0 and u in a and initial+a[u]<=budget)
  return self.regions[key]
