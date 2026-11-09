"""Net-specific frozen pressure contexts over shared immutable base arcs.

Fresh per-query lazy arc view; no cross-net/source cache reuse. Own contribution
is one unique-net node touch, regardless of number of sink branches.
"""
from collections import Counter,defaultdict
from types import MappingProxyType
import hashlib,json
from copy import copy
from compact_indexed_sketch import CompactIndexedSketch

def net_union(graph,prediction):
    if prediction['physical_graph_sha256']!=graph.sha256:raise ValueError('graph identity mismatch')
    users=defaultdict(set);seen=set();roots={}
    for r in prediction['connections']:
        cid=r['connection_id'];net=r['net_id'];node=r['source'];path=r['physical_edge_ids']
        if type(cid) is not int or cid<0 or cid in seen or type(net) is not int or net<0:raise ValueError('invalid connection/net identity')
        seen.add(cid)
        if type(node) is not int or type(r['sink']) is not int or node not in graph.nodes or graph.nodes[node].type!='SOURCE' or path is None:raise ValueError('invalid source/path')
        if net in roots and roots[net]!=node:raise ValueError('multiple source roots for net')
        roots[net]=node
        nodes={node}
        for eid in path:
            if type(eid) is not int or eid<0 or eid>=len(graph.edges):raise ValueError('invalid edge')
            edge=graph.edges[eid]
            if edge.source!=node or edge.sink in nodes:raise ValueError('invalid path continuity')
            node=edge.sink;nodes.add(node)
        if node!=r['sink'] or graph.nodes[node].type!='SINK':raise ValueError('invalid sink')
        users[net].update(nodes)
    demand=Counter(n for nodes in users.values() for n in nodes)
    if {str(n):v for n,v in demand.items()}!=prediction['node_occupancy']:raise ValueError('background union mismatch')
    return MappingProxyType({n:frozenset(nodes) for n,nodes in users.items()}),MappingProxyType(dict(demand))

class ArcView:
    def __init__(self,owner,net,exclude):self.owner=owner;self.own=owner.users[net] if exclude else frozenset();self.cache={}
    def __getitem__(self,node):
        if node not in self.cache:
            self.cache[node]=tuple((eid,dst,None if cost is None else cost+(self.owner.reduced[dst] if dst in self.own else self.owner.full[dst])) for eid,dst,cost in self.owner.base.outgoing[node])
        return self.cache[node]

class NetPressure:
    def __init__(self,graph,prediction,alpha=256):
        if type(alpha) is not int or alpha<0:raise ValueError('invalid alpha')
        self.users,self.demand=net_union(graph,prediction);self.roots=MappingProxyType({r['net_id']:r['source'] for r in prediction['connections']});self.base=CompactIndexedSketch(graph,'rr_length_switch',len(graph.nodes));self.full={};self.reduced={}
        for n,node in graph.nodes.items():
            c=node.capacity;channel=c>0 and node.type in {'CHANX','CHANY'};d=self.demand.get(n,0)
            self.full[n]=(alpha*max(0,d-c+1)+c-1)//c if channel else 0
            self.reduced[n]=(alpha*max(0,max(0,d-1)-c+1)+c-1)//c if channel else 0
        self.identity={'graph':graph.sha256,'alpha':alpha,'demand':sorted(self.demand.items())}
    def query(self,net,source,sinks,exclude=True):
        if type(net) is not int or net not in self.users or type(source) is not int or source!=self.roots[net] or type(exclude) is not bool:raise ValueError('invalid net context')
        engine=copy(self.base);engine.outgoing=ArcView(self,net,exclude)
        context=hashlib.sha256(json.dumps({**self.identity,'net':net,'exclude':exclude,'own_nodes':sorted(self.users[net]) if exclude else []},sort_keys=True).encode()).hexdigest()
        return engine.search(source,sinks),context
