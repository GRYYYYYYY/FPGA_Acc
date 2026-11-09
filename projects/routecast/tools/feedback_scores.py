"""Uncalibrated development feedback scores, no native-route inputs."""
from collections import defaultdict


def scores(graph,endpoints,occupancy):
    length=0;overuse=0
    for key,value in occupancy.items():
        if type(value) is not int or value<0:raise ValueError('invalid unique-net occupancy')
        try:nid=int(key)
        except (ValueError,TypeError):raise ValueError('invalid resource ID')
        if nid not in graph.nodes:raise ValueError('unknown resource')
        node=graph.nodes[nid]
        if node.type in {'CHANX','CHANY'}:
            loc=dict(node.location);span=max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1
            length+=value*span;overuse+=max(0,value-node.capacity)
    groups=defaultdict(set)
    for r in endpoints['connections']:
        groups[r['net_id']].update((r['source'],r['sink']))
    hpwl=0
    for nodes in groups.values():
        coords=[dict(graph.nodes[n].location) for n in nodes]
        xs=[int(loc['xlow']) for loc in coords];ys=[int(loc['ylow']) for loc in coords]
        hpwl+=max(xs)-min(xs)+max(ys)-min(ys)
    return {'channel_net_span_sum':length,'predicted_channel_overuse_units':overuse,'net_bbox_hpwl':hpwl}
