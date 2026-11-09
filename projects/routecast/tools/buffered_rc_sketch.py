"""Fixed-edge RC-only search for wholly buffered graphs; no timing labels.

Integer units are 1e-18 seconds by default, nearest ties to even. The model
rejects all nonbuffered switches and negative expansion increments. No tree
start, congestion, native base cost, criticality or lookahead is included.
"""
from fractions import Fraction
from compact_indexed_sketch import CompactIndexedSketch
from path_rc import PathRC, State

class BufferedRCSketch(CompactIndexedSketch):
    def __init__(self,graph,scale=10**18):
        if type(scale) is not int or scale<1:raise ValueError('invalid scale')
        rc=PathRC(graph)
        if any(not fields[0] for fields in rc.switches.values()):
            raise ValueError('nonbuffered graph requires resistance state')
        weights={}
        for eid in range(len(graph.edges)):
            delay=rc.step(State(Fraction(0),Fraction(0)),eid).delay
            if delay<0:raise ValueError('negative RC expansion weight')
            weights[eid]=round(delay*scale)
        super().__init__(graph,'rr_length_switch',len(graph.nodes))
        self.outgoing={n:tuple((eid,dst,None if cost is None else weights[eid]) for eid,dst,cost in arcs) for n,arcs in self.outgoing.items()}
        self.scale=scale
