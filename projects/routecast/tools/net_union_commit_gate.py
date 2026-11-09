"""Prepublication structural gate, assumes individual paths already audited."""
from net_union_topology import diagnose

def check(graph,current,replacements):
    existing={r['connection_id']:r for r in current['connections']}
    if len(existing)!=len(current['connections']):raise ValueError('duplicate current ID')
    changed={}
    for row in replacements:
        cid=row['connection_id']
        if cid in changed or cid not in existing:raise ValueError('duplicate/unknown replacement')
        old=existing[cid]
        if any(row[k]!=old[k] for k in ('net_id','source','sink')):raise ValueError('endpoint mutation unsupported')
        changed[cid]=row
    affected={r['net_id'] for r in changed.values()}
    merged=[changed.get(cid,row) for cid,row in existing.items() if row['net_id'] in affected]
    report=diagnose(graph,{'physical_graph_sha256':current['physical_graph_sha256'],'connections':merged})
    rejected=[r for r in report['nets'] if r['internal_multi_incoming_nodes'] or r['cyclic_union'] or r['source_has_incoming'] or not r['all_nodes_source_reachable']]
    return {'accepted':not rejected,'affected_nets':sorted(affected),'rejected_nets':rejected,'topology':report,'scope':'whole affected net union structure including retained paths; terminal SINK aliases allowed; individual path and native legality checks remain required'}
