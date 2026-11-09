"""Directed net-union structural diagnostics; not a VPR legality verifier.

SINK class aliases may have multiple terminal occurrences and are reported
separately. Internal reconvergence and cycles require a richer tree witness.
Call independent physical path audit before using this diagnostic.
"""
from collections import defaultdict,deque


def diagnose(graph,prediction):
    if prediction['physical_graph_sha256']!=graph.sha256:raise ValueError('graph mismatch')
    edges=defaultdict(set);roots={}
    for r in prediction['connections']:
        net=r['net_id'];source=r['source']
        if net in roots and roots[net]!=source:raise ValueError('mixed roots')
        roots[net]=source
        if r['physical_edge_ids'] is None:raise ValueError('incomplete paths')
        edges[net].update(r['physical_edge_ids'])
    reports=[]
    for net in sorted(roots):
        incoming=defaultdict(set);outgoing=defaultdict(set);nodes={roots[net]}
        for eid in edges[net]:
            edge=graph.edges[eid];nodes.update((edge.source,edge.sink));incoming[edge.sink].add(eid);outgoing[edge.source].add(eid)
        internal=[n for n in nodes if len(incoming[n])>1 and graph.nodes[n].type!='SINK'];terminal=[n for n in nodes if len(incoming[n])>1 and graph.nodes[n].type=='SINK']
        degree={n:len(incoming[n]) for n in nodes};queue=deque(sorted(n for n in nodes if degree[n]==0));visited=0
        while queue:
            n=queue.popleft();visited+=1
            for eid in outgoing[n]:
                dst=graph.edges[eid].sink;degree[dst]-=1
                if degree[dst]==0:queue.append(dst)
        reached={roots[net]};queue=deque(reached)
        while queue:
            n=queue.popleft()
            for eid in outgoing[n]:
                dst=graph.edges[eid].sink
                if dst not in reached:reached.add(dst);queue.append(dst)
        reports.append({'net_id':net,'unique_edges':len(edges[net]),'unique_nodes':len(nodes),'internal_multi_incoming_nodes':sorted(internal),'terminal_multi_incoming_nodes':sorted(terminal),'cyclic_union':visited!=len(nodes),'source_has_incoming':bool(incoming[roots[net]]),'all_nodes_source_reachable':reached==nodes})
    return {'nets':reports,'net_count':len(reports),'internal_reconvergent_net_count':sum(bool(r['internal_multi_incoming_nodes']) for r in reports),'cyclic_net_count':sum(r['cyclic_union'] for r in reports),'terminal_alias_net_count':sum(bool(r['terminal_multi_incoming_nodes']) for r in reports),'scope':'union structural diagnostics after individual physical audit; terminal class alias not classified illegal; not complete VPR tree legality'}
