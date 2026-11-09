"""Switch-witness lifting and outgoing-signature partition refinement.

Lifting proves one connection has an exact directed physical RR path. It does
not prove multi-net capacity, a legal route tree, or non-configurable closure.
A stable partition has identical (switch, successor-cell) exits for every
positive-capacity member, so any simple quotient path can be lifted.
"""
from collections import defaultdict
from dataclasses import dataclass, replace
import hashlib
import json
from types import MappingProxyType
from connection_golden import integer
from rr_graph import RRGraph, RREdge


@dataclass(frozen=True)
class LiftResult:
    edge_ids: tuple | None
    failed_at: int | None
    frontier_sizes: tuple
    physical_edge_visits: int


class Lifter:
    def __init__(self,physical,pooled,mapping):
        if set(mapping)!=set(physical.nodes):raise ValueError('incomplete physical mapping')
        self.physical=physical;self.pooled=pooled;self.mapping=mapping
        qids={(e.source,e.sink,e.switch_id):i for i,e in enumerate(pooled.edges)}
        if len(qids)!=len(pooled.edges):raise ValueError('duplicate quotient switch arcs')
        self.witness=defaultdict(list)
        for eid,edge in enumerate(physical.edges):
            key=(mapping[edge.source],mapping[edge.sink],edge.switch_id)
            if key not in qids:raise ValueError('physical switch arc absent from quotient')
            self.witness[(qids[key],edge.source)].append(eid)

    def lift(self,source,sink,path):
        if (type(source) is not int or type(sink) is not int or source not in self.physical.nodes or sink not in self.physical.nodes or
            self.physical.nodes[source].type!='SOURCE' or self.physical.nodes[sink].type!='SINK'):
            raise ValueError('invalid physical endpoints')
        current=self.mapping[source];visited={current}
        for qeid in path:
            if not integer(qeid,0,len(self.pooled.edges)-1):raise ValueError('invalid quotient edge ID')
            edge=self.pooled.edges[qeid]
            if edge.source!=current or edge.sink in visited:raise ValueError('quotient path discontinuous or cyclic')
            current=edge.sink;visited.add(current)
        if current!=self.mapping[sink]:raise ValueError('wrong quotient sink')
        states={source:()} if self.physical.nodes[source].capacity else {}
        sizes=[len(states)];visits=0
        if not states:return LiftResult(None,0,tuple(sizes),visits)
        for step,qeid in enumerate(path,1):
            following={}
            for node,prefix in states.items():
                for eid in self.witness[(qeid,node)]:
                    visits+=1;edge=self.physical.edges[eid]
                    if self.physical.nodes[edge.sink].capacity==0:continue
                    candidate=prefix+(eid,)
                    if edge.sink not in following or candidate<following[edge.sink]:following[edge.sink]=candidate
            states=following;sizes.append(len(states))
            if not states:return LiftResult(None,step,tuple(sizes),visits)
        chosen=states.get(sink)
        return LiftResult(chosen,None if chosen is not None else len(path),tuple(sizes),visits)


def signatures(graph,mapping):
    exits={n:set() for n in graph.nodes}
    for edge in graph.edges:
        if graph.nodes[edge.source].capacity and graph.nodes[edge.sink].capacity:
            exits[edge.source].add((edge.switch_id,mapping[edge.sink]))
    return {n:(bool(graph.nodes[n].capacity),tuple(sorted(exits[n]))) for n in graph.nodes}


def stable(graph,mapping):
    sig=signatures(graph,mapping);groups={}
    for n,cell in mapping.items():
        if cell in groups and groups[cell]!=sig[n]:return False
        groups[cell]=sig[n]
    return True


def refine(graph,coarse,mapping,rounds=None):
    if rounds is not None and (type(rounds) is not int or rounds<0):raise ValueError('invalid refinement rounds')
    colors=dict(mapping);performed=0
    while rounds is None or performed<rounds:
        sig=signatures(graph,colors);classes={};following={}
        for nid in sorted(graph.nodes):
            key=(colors[nid],sig[nid])
            if key not in classes:classes[key]=len(classes)
            following[nid]=classes[key]
        performed+=1
        if following==colors:break
        if len(set(following.values()))<len(set(colors.values())):raise AssertionError('refinement merged cells')
        colors=following
        if performed>len(graph.nodes):raise AssertionError('partition did not converge')
    members=defaultdict(list)
    for n,c in sorted(colors.items()):members[c].append(n)
    nodes={}
    for c,ids in members.items():
        first=graph.nodes[ids[0]]
        if first.type=='IPIN':
            # Coarse IPIN cells share one class, retained by monotone refinement.
            capacity=len({int(dict(graph.nodes[n].location)['ptc']) for n in ids})
        else:capacity=sum(graph.nodes[n].capacity for n in ids)
        nodes[c]=replace(first,id=c,capacity=capacity)
    arcs=sorted({(colors[e.source],colors[e.sink],e.switch_id) for e in graph.edges})
    identity=hashlib.sha256(json.dumps({'physical':graph.sha256,'mapping':sorted(colors.items()),'arcs':arcs},sort_keys=True).encode()).hexdigest()
    pooled=RRGraph(MappingProxyType(nodes),tuple(RREdge(s,t,w,()) for s,t,w in arcs),coarse.switches,coarse.segments,
                   MappingProxyType({'scope':'outgoing-switch refined quotient','physical_sha256':graph.sha256}),identity)
    return pooled,MappingProxyType(colors),MappingProxyType({c:tuple(ids) for c,ids in members.items()}),performed,stable(graph,colors)
