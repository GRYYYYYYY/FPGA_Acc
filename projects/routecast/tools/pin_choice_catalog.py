"""Graph class membership and concrete path pin witnesses, not assignment."""
from collections import defaultdict
from types import MappingProxyType
from pin_pools import build_pools,PinPool

class PinChoiceCatalog:
    def __init__(self,graph):
        self.graph=graph;self.sinks,self.ipin_owner=build_pools(graph)
        members=defaultdict(lambda:defaultdict(set));owner={}
        for edge in graph.edges:
            if graph.nodes[edge.source].type!='SOURCE' or graph.nodes[edge.sink].type!='OPIN':continue
            pin=graph.nodes[edge.sink]
            if pin.capacity!=1:raise ValueError('non-unit OPIN unsupported')
            if edge.sink in owner and owner[edge.sink]!=edge.source:raise ValueError('OPIN multiple source classes')
            owner[edge.sink]=edge.source;members[edge.source][int(dict(pin.location)['ptc'])].add(edge.sink)
        pools={}
        for nid,node in graph.nodes.items():
            if node.type!='SOURCE':continue
            pins=members[nid]
            if len(pins)!=node.capacity:raise ValueError('SOURCE physical pin count differs from capacity')
            pools[nid]=PinPool(nid,node.capacity,MappingProxyType({ptc:tuple(sorted(ids)) for ptc,ids in sorted(pins.items())}))
        if set(owner)!={n for n,node in graph.nodes.items() if node.type=='OPIN'}:raise ValueError('OPIN missing direct SOURCE membership')
        self.sources=MappingProxyType(pools);self.opin_owner=MappingProxyType(owner)

    def witness(self,source,sink,edge_ids):
        if type(source) is not int or type(sink) is not int or source not in self.sources or sink not in self.sinks:raise ValueError('invalid class endpoints')
        if edge_ids is None:raise ValueError('missing path')
        node=source;visited={node};opins=[];ipins=[]
        for eid in edge_ids:
            if type(eid) is not int or not 0<=eid<len(self.graph.edges):raise ValueError('invalid edge')
            edge=self.graph.edges[eid]
            if edge.source!=node or edge.sink in visited:raise ValueError('invalid path continuity')
            node=edge.sink;visited.add(node)
            if self.graph.nodes[node].capacity<=0:raise ValueError('disabled path node')
            if self.graph.nodes[node].type=='OPIN':opins.append(node)
            if self.graph.nodes[node].type=='IPIN':ipins.append(node)
        if node!=sink or len(opins)!=1 or len(ipins)!=1:raise ValueError('unsupported physical pin path')
        opin,ipin=opins[0],ipins[0]
        if self.opin_owner[opin]!=source or self.ipin_owner[ipin]!=sink:raise ValueError('path pin outside endpoint class')
        return {'source_class':source,'sink_class':sink,'selected_opin_rr':opin,'selected_ipin_rr':ipin,'selected_opin_ptc':int(dict(self.graph.nodes[opin].location)['ptc']),'selected_ipin_ptc':int(dict(self.graph.nodes[ipin].location)['ptc']),'allowed_source_physical_pin_count':len(self.sources[source].physical_pins),'allowed_sink_physical_pin_count':len(self.sinks[sink].physical_pins),'scope':'graph membership and path witness only; no packed-pin assignment, all-pin reachability or timing guarantee'}
