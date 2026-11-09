"""Frozen-cost RR development sketches; consumes graph and endpoints only.

These are software baselines, not final RouteCast algorithms. No congestion cost,
placement feedback, full pin-class model or non-configurable closure is provided.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import heapq
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class SearchResult:
    paths: dict
    settled_nodes: int
    edge_visits: int
    budget_exhausted: bool


class Sketch:
    def __init__(self, graph, mode='rr_length_switch', node_budget=4096):
        if mode not in {'rr_hop','rr_length_switch'} or type(node_budget) is not int or node_budget<1:
            raise ValueError('invalid sketch configuration')
        self.graph=graph; self.mode=mode; self.node_budget=node_budget
        self.adjacency={nid:[] for nid in graph.nodes}
        delays={}
        for sid,xml in graph.switches.items():
            switch=ET.fromstring(xml)
            # Cannot silently ignore electrically mandatory closure resources.
            if switch.attrib.get('type') in {'short','buffer'}:
                raise ValueError('non-configurable switch closure is not implemented')
            timing=switch.find('timing')
            delay=Decimal(timing.attrib.get('Tdel','0')) if timing is not None else Decimal(0)
            if not delay.is_finite() or delay<0: raise ValueError('invalid switch delay')
            delays[sid]=int((delay*Decimal(10**12)).to_integral_value(rounding=ROUND_HALF_UP))
        self.costs=[]
        for eid,edge in enumerate(graph.edges):
            dst=graph.nodes[edge.sink]; loc=dict(dst.location)
            length=(max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1
                    if dst.type in {'CHANX','CHANY'} else 0)
            # Development-only uncalibrated integer weighting: 256 units/tile,
            # plus switch delay in ps. It is not a timing estimator.
            self.costs.append(1 if mode=='rr_hop' else 1+256*length+delays[edge.switch_id])
            self.adjacency[edge.source].append(eid)
        self.costs=tuple(self.costs)

    def search(self, source, sinks):
        sinks=set(sinks)
        if (source not in self.graph.nodes or self.graph.nodes[source].type!='SOURCE' or
            any(s not in self.graph.nodes or self.graph.nodes[s].type!='SINK' for s in sinks)):
            raise ValueError('invalid endpoints')
        if self.graph.nodes[source].capacity==0:
            return SearchResult({},0,0,False)
        if not sinks: return SearchResult({},0,0,False)
        best={source:(0,0,())}; queue=[(0,0,(),source)]; settled=set(); paths={}; visits=0
        while queue and len(settled)<self.node_budget:
            cost,hops,path,node=heapq.heappop(queue)
            if node in settled or best[node]!=(cost,hops,path): continue
            settled.add(node)
            if node in sinks:
                paths[node]=path
                if len(paths)==len(sinks): break
            for eid in self.adjacency[node]:
                visits+=1; edge=self.graph.edges[eid]
                if edge.sink in settled or self.graph.nodes[edge.sink].capacity==0: continue
                candidate=(cost+self.costs[eid],hops+1,path+(eid,))
                if edge.sink not in best or candidate<best[edge.sink]:
                    best[edge.sink]=candidate
                    heapq.heappush(queue,(*candidate,edge.sink))
        exhausted=(len(paths)<len(sinks) and len(settled)>=self.node_budget and bool(queue))
        return SearchResult(paths,len(settled),visits,exhausted)
