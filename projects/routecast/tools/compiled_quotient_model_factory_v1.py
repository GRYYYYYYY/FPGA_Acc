"""Build fixed geometry groups/floors for the isolated whole-model candidate."""
from compiled_quotient_criticality_astar_v1 import Graph, BINARY
from static_quotient_lower_bound_v1 import LowerBound


def create(fields,increments,initial,nodes,node_base,weight):
    groups=[];domain={};floor=[]
    for i,node in enumerate(nodes):
        loc=node.find('loc').attrib;segment=node.find('segment')
        key=(int(loc.get('layer','0')),int(loc['xlow'])//4,int(loc['ylow'])//4,
             node.get('type'),int(segment.get('segment_id')) if segment is not None else -1,
             node.get('direction','NONE'))
        if key not in domain:domain[key]=len(domain)
        groups.append(domain[key])
        span=(max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1
              if node.get('type') in ('CHANX','CHANY') else 0)
        floor.append(node_base[i]+weight*span)
    lower=LowerBound(fields,increments,initial,floor,groups,max_targets=64)
    return Graph(lower)
