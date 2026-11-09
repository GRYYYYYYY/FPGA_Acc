"""Independent complete-coverage and isolated rejected-path witness checks."""
POLICY='Continue every nonretained pin in original criticality/pin/CID order; rejected expansions never enter committed tree; separate physical/raw rejection witnesses; original wholeNET fallback and guards unchanged.'


def audit(event,old,eligible,criticalities,pin_order,queries,physical_path):
    old={r['connection_id']:r for r in old}
    searched=event['primary_search_connection_ids']
    expected=sorted(set(old)-set(eligible),key=lambda cid:(-criticalities[cid],pin_order[cid],cid))
    assert searched==expected and all(type(cid) is int for cid in searched)
    rows=event['primary_rejected_expansions'];seen=set();positions={cid:i for i,cid in enumerate(searched)};last=-1
    for row in rows:
        cid=row['connection_id']
        assert type(cid) is int and cid in positions and cid not in seen and positions[cid]>last
        seen.add(cid);last=positions[cid]
        if row['status']=='RETAIN_RAW_BUDGET':
            assert type(row['raw']) is int and isinstance(row['physical_edge_ids'],list)
            actual=physical_path(queries[cid],row['physical_edge_ids'],{})
            assert actual==row['raw']>old[cid]['budget_integer']
        else:
            assert row['status']=='UNREACHABLE' and row['raw'] is None and row['physical_edge_ids'] is None
    if 'fallback' in event:
        attempts=event['primary_attempts']
        assert len(attempts)==len(old) and {x['connection_id'] for x in attempts}==set(old)
        for attempt in attempts:
            cid=attempt['connection_id'];path=attempt['physical_edge_ids']
            if path is None:assert cid in seen
            else:assert physical_path(queries[cid],path,{})<=old[cid]['budget_integer']
    return True
