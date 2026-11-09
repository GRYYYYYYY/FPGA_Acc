"""Input-only whole-net seed ordering; pending connections remain exact-router work."""
from collections import defaultdict,Counter
from fractions import Fraction
from prepared_csr import TYPES

def select(records, required_ids, context, policy):
    groups=defaultdict(list)
    for record in records:groups[record['net_id']].append(record)
    ids=[r['connection_id'] for r in records]
    if len(set(ids))!=len(ids) or set(ids)!=set(required_ids):
        raise ValueError('complete unique connection partition required')
    owners={net:({r['source'] for r in recs}|
                 {context.graph.edges[e].sink for r in recs for e in r['answer']['physical_edge_ids']})
            for net,recs in groups.items()}
    if policy=='connection_count':
        order=sorted(groups,key=lambda net:(-len(groups[net]),len(owners[net]),net))
    elif policy=='connection_per_channel_span':
        channel={TYPES['CHANX'],TYPES['CHANY']}
        span={net:sum(context.spans[n] for n in owned if context.types[n] in channel)
              for net,owned in owners.items()}
        order=sorted(groups,key=lambda net:(-Fraction(len(groups[net]),max(1,span[net])),
                                            -len(groups[net]),len(owners[net]),net))
    else:raise ValueError('unknown selection policy')
    ledger=Counter();kept=[];decisions=[]
    for net in order:
        blockers=sorted(n for n in owners[net] if ledger[n]+1>context.graph.nodes[n].capacity)
        if not blockers:ledger.update(owners[net]);kept.append(net)
        decisions.append(dict(net_id=net,admitted=not blockers,blocking_nodes=blockers))
    selected=sorted((r for net in kept for r in groups[net]),key=lambda r:r['connection_id'])
    pending=sorted(set(required_ids)-{r['connection_id'] for r in selected})
    return dict(records=selected,pending=pending,decisions=decisions,ledger=dict(ledger))
