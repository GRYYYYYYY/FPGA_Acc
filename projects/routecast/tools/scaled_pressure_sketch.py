"""One frozen scaled predictor-demand pressure context; not negotiated congestion.

Costs never change during a search/cohort. New graph/background/alpha/scale requires a
new engine and invalidates all search caches; no dirty-only optimization claim.
"""
import hashlib,json
from collections.abc import Mapping
from compact_indexed_sketch import CompactIndexedSketch

class ScaledPressureSketch(CompactIndexedSketch):
    def __init__(self,graph,background,background_graph_sha256,alpha=256,node_budget=4096,scale=256):
        if background_graph_sha256!=graph.sha256:raise ValueError('background graph identity mismatch')
        if type(alpha) is not int or alpha<0 or type(scale) is not int or scale<1 or not isinstance(background,Mapping):raise ValueError('invalid pressure configuration')
        demand={}
        for n,v in background.items():
            if type(n) is not int or n not in graph.nodes or type(v) is not int or v<0:raise ValueError('invalid background demand')
            if v:demand[n]=v
        self.context_sha256=hashlib.sha256(json.dumps({'graph':graph.sha256,'alpha':alpha,'demand_scale':scale,'channel_demand':sorted(demand.items()),'rule':'ceil(alpha*max(0,scaled_demand-scale*capacity+scale)/(scale*capacity)), channels only'},sort_keys=True).encode()).hexdigest()
        super().__init__(graph,'rr_length_switch',node_budget)
        penalty={}
        for n,node in graph.nodes.items():
            c=node.capacity
            penalty[n]=(alpha*max(0,demand.get(n,0)-scale*c+scale)+scale*c-1)//(scale*c) if c>0 and node.type in {'CHANX','CHANY'} else 0
        self.outgoing={n:tuple((eid,dst,None if weight is None else weight+penalty[dst]) for eid,dst,weight in arcs) for n,arcs in self.outgoing.items()}
