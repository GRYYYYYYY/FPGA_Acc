"""Frozen-cost Dijkstra with immutable indexed outgoing arcs.

The ordering, budget, paths and work counters match Sketch.search. This only
moves destination capacity/cost lookups into graph preparation.
"""
import heapq
from semantic_sketch import Sketch,SearchResult

class IndexedSketch(Sketch):
    def __init__(self,graph,mode='rr_length_switch',node_budget=4096):
        super().__init__(graph,mode,node_budget)
        self.outgoing={n:tuple((e,graph.edges[e].sink,self.costs[e],graph.nodes[graph.edges[e].sink].capacity>0) for e in arcs) for n,arcs in self.adjacency.items()}

    def search(self,source,sinks):
        sinks=set(sinks);g=self.graph
        if source not in g.nodes or g.nodes[source].type!='SOURCE' or any(s not in g.nodes or g.nodes[s].type!='SINK' for s in sinks):raise ValueError('invalid endpoints')
        if g.nodes[source].capacity==0 or not sinks:return SearchResult({},0,0,False)
        best={source:(0,0,())};queue=[(0,0,(),source)];settled=set();paths={};visits=0
        while queue and len(settled)<self.node_budget:
            cost,hops,path,node=heapq.heappop(queue)
            if node in settled or best[node]!=(cost,hops,path):continue
            settled.add(node)
            if node in sinks:
                paths[node]=path
                if len(paths)==len(sinks):break
            for eid,dst,weight,enabled in self.outgoing[node]:
                visits+=1
                if dst in settled or not enabled:continue
                candidate=(cost+weight,hops+1,path+(eid,))
                if dst not in best or candidate<best[dst]:
                    best[dst]=candidate;heapq.heappush(queue,(*candidate,dst))
        return SearchResult(paths,len(settled),visits,len(paths)<len(sinks) and len(settled)>=self.node_budget and bool(queue))
