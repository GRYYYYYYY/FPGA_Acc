"""RR quotient sketch: a topology/capacity relaxation, never an exact router.

Channel templates retain type, complete span, layer, direction, segment and
node timing. Pool exits may mix physical tracks: no lifted-path legality claim.
Input pin classes deduplicate physical pin ptc/facets before assigning capacity.
"""
from collections import defaultdict
from dataclasses import replace
from fractions import Fraction
import hashlib
import json
from types import MappingProxyType
from pin_pools import build_pools
from connection_golden import integer, UINT64_MAX
from rr_graph import RRGraph, RREdge
from run_sketch import predict


def quotient(graph,channel_pooling):
    pools,owner=build_pools(graph);groups=defaultdict(list)
    for nid,node in sorted(graph.nodes.items()):
        if node.type=='IPIN':key=('IPIN_CLASS',owner[nid])
        elif channel_pooling and node.type in {'CHANX','CHANY'}:
            loc=dict(node.location)
            key=(node.type,tuple((k,loc.get(k,'0')) for k in ('xlow','xhigh','ylow','yhigh','layer')),
                 node.direction,node.segment_id,node.timing)
        else:key=(node.type,nid)
        groups[key].append(nid)
    mapping={};nodes={};members={}
    for tid,(_,ids) in enumerate(groups.items()):
        first=graph.nodes[ids[0]];members[tid]=tuple(ids)
        for nid in ids:mapping[nid]=tid
        capacity=(pools[owner[ids[0]]].capacity if first.type=='IPIN' else
                  sum(graph.nodes[n].capacity for n in ids))
        nodes[tid]=replace(first,id=tid,capacity=capacity)
    arcs=sorted({(mapping[e.source],mapping[e.sink],e.switch_id) for e in graph.edges})
    edges=tuple(RREdge(s,t,w,()) for s,t,w in arcs)
    identity=hashlib.sha256(json.dumps({'physical_sha':graph.sha256,'channel_pooling':channel_pooling,
                                      'groups':[list(ids) for ids in members.values()],'arcs':arcs},sort_keys=True).encode()).hexdigest()
    pooled=RRGraph(MappingProxyType(nodes),edges,graph.switches,graph.segments,
                   MappingProxyType({'scope':'quotient RR relaxation','original_sha256':graph.sha256}),identity)
    return pooled,MappingProxyType(mapping),MappingProxyType(members)


def estimate(graph,endpoints,channel_pooling):
    if endpoints['graph_sha256']!=graph.sha256:raise ValueError('physical graph identity mismatch')
    for row in endpoints['connections']:
        if set(row)!={'connection_id','net_id','source','sink'} or any(not integer(v,0,UINT64_MAX) for v in row.values()):
            raise ValueError('invalid endpoint fields')
        if row['source'] not in graph.nodes or row['sink'] not in graph.nodes:
            raise ValueError('endpoint outside physical graph')
        if graph.nodes[row['source']].type!='SOURCE' or graph.nodes[row['sink']].type!='SINK':
            raise ValueError('endpoint type mismatch')
    pooled,mapping,members=quotient(graph,channel_pooling)
    translated={'schema':'ROUTECAST_ENDPOINTS_V1','graph_sha256':pooled.sha256,
                'connections':[{**r,'source':mapping[r['source']],'sink':mapping[r['sink']]} for r in endpoints['connections']]}
    prediction=predict(pooled,translated,'rr_length_switch',len(pooled.nodes))
    # Uniform capacity-weighted expected demand. Multiple tracks of the same
    # net inside a template are relaxed to one net touch (possible undercount).
    expected={}
    for tid,ids in members.items():
        node=pooled.nodes[tid]
        if node.type not in {'CHANX','CHANY'}:continue
        demand=prediction['node_occupancy'].get(str(tid),0)
        for nid in ids:
            value=Fraction(demand*graph.nodes[nid].capacity,node.capacity) if node.capacity else Fraction(0)
            expected[str(nid)]=[value.numerator,value.denominator]
    return {'schema':'ROUTECAST_TEMPLATE_SKETCH_V1','physical_graph_sha256':graph.sha256,
            'quotient_graph_sha256':pooled.sha256,'channel_pooling':channel_pooling,
            'physical_nodes':len(graph.nodes),'physical_edges':len(graph.edges),
            'template_nodes':len(pooled.nodes),'template_edges':len(pooled.edges),
            'prediction':prediction,'channel_expected_demand':expected,
            'template_members':{str(t):list(ids) for t,ids in members.items()},
            'scope':'pin-class/channel quotient relaxation with uniform expected demand; not physical routes'}
