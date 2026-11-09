"""Static residual graph closure and blocked boundary in one edge scan."""
def residual_reachability(fields, source, other):
    reachable=set();pending=[];frontier=set()
    if other.get(source,0)<fields['capacities'][source]:
        reachable.add(source);pending.append(source)
    while pending:
        u=pending.pop()
        for slot in range(fields['row_offsets'][u],fields['row_offsets'][u+1]):
            v=fields['dest_ranks'][slot]
            if v in reachable:
                continue
            if other.get(v,0)<fields['capacities'][v]:
                reachable.add(v);pending.append(v)
            else:
                frontier.add(v)
    return reachable,sorted(frontier) if reachable else [source]
