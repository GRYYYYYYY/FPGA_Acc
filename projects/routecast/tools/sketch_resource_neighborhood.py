"""Pre-route channel-sharing closure from authenticated physical sketches."""
from collections import defaultdict
from physical_prediction_audit import audit
from affected_connections import affected


def resource_neighborhood(graph,before,after,baseline,candidate,*,hops=1):
    if type(hops) is not int or hops<0:raise ValueError('invalid hop count')
    closure=affected(before,after)
    audit(graph,before,baseline);audit(graph,after,candidate)
    resources=defaultdict(set);users=defaultdict(set);source_nets=defaultdict(set);net_sources=defaultdict(set)
    for endpoint in (before,after):
        for r in endpoint['connections']:
            source_nets[r['source']].add(r['net_id']);net_sources[r['net_id']].add(r['source'])
    for prediction in (baseline,candidate):
        for r in prediction['connections']:
            if r['physical_edge_ids'] is None:raise ValueError('complete sketch required')
            for eid in r['physical_edge_ids']:
                n=graph.edges[eid].sink
                if graph.nodes[n].type in {'CHANX','CHANY'}:
                    resources[r['net_id']].add(n);users[n].add(r['net_id'])
    def source_close(nets):
        nets=set(nets)
        while True:
            expanded=nets|{n for seed in nets for s in net_sources[seed] for n in source_nets[s]}
            if expanded==nets:return nets
            nets=expanded
    selected=source_close(closure['affected_net_ids']);layers=[sorted(selected)]
    for _ in range(hops):
        expanded=source_close(selected|{net for seed in selected for n in resources[seed] for net in users[n]})
        layers.append(sorted(expanded-selected));selected=expanded
    return {'seed_net_ids':closure['affected_net_ids'],'expanded_net_ids':sorted(selected),'net_layers':layers,'recompute_connection_ids':sorted(r['connection_id'] for r in after['connections'] if r['net_id'] in selected),'remove_connection_ids':closure['remove_connection_ids'],'hops':hops,'scope':'baseline/candidate sketch channel sharing plus whole-net SOURCE closure; no native route inputs','limitations':['complete physical sketches required','not a guarantee of native reroute closure','sharing graph construction scans both sketches']}
