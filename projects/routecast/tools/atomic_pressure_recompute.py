"""Whole-net frozen pressure search and atomic software commit.

Background is a complete current-placement sketch. This is one simultaneous
frozen-cost batch, not negotiated congestion or guaranteed route-tree legality.
"""
from collections import Counter
from net_pressure_sketch import NetPressure
from physical_prediction_audit import audit
from rr_local_batch_occupancy import LocalBatchOccupancy
from connection_golden import Result


def recompute(graph,endpoints,background,net_ids,*,alpha=256):
    audit(graph,endpoints,background)
    selected=set(net_ids)
    if any(type(n) is not int or n<0 for n in selected):raise ValueError('invalid selected net')
    grouped={}
    for row in endpoints['connections']:grouped.setdefault(row['net_id'],[]).append(row)
    if not selected<=grouped.keys():raise ValueError('unknown selected net')
    engine=NetPressure(graph,background,alpha);ledger=LocalBatchOccupancy(graph)
    for r in background['connections']:
        if ledger.update(r['connection_id'],1,r['net_id'],r['source'],r['sink'],r['physical_edge_ids'])!=Result.COMMITTED:raise ValueError('background commit rejected')
    updates=[];new_rows={};contexts={};work={'settled_nodes':0,'edge_visits':0}
    for net in sorted(selected):
        rows=grouped[net];sources={r['source'] for r in rows}
        if len(sources)!=1:raise ValueError('mixed net roots')
        result,context=engine.query(net,rows[0]['source'],{r['sink'] for r in rows},True)
        if result.budget_exhausted or set(result.paths)!={r['sink'] for r in rows}:raise ValueError('incomplete pressure search; batch not published')
        contexts[str(net)]=context;work['settled_nodes']+=result.settled_nodes;work['edge_visits']+=result.edge_visits
        for r in rows:
            path=result.paths[r['sink']];new_rows[r['connection_id']]={**r,'physical_edge_ids':path,'method':'frozen_net_pressure'}
            updates.append({**r,'epoch':2,'edge_ids':path})
    if ledger.update_batch(updates)!=Result.COMMITTED:raise ValueError('pressure batch rejected')
    rows=[new_rows.get(r['connection_id'],r) for r in background['connections']]
    prediction={'physical_graph_sha256':graph.sha256,'connections':rows,'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},'methods':dict(Counter(r['method'] for r in rows)),'requested':len(rows),'completed':len(rows)}
    checked=audit(graph,endpoints,prediction)
    return prediction,{'net_ids':sorted(selected),'recomputed_connections':len(updates),'alpha':alpha,'contexts':contexts,'work':work,'physical_audit':checked,'scope':'whole-net own-excluded frozen pressure; complete sketches only; no native route input; no VPR joint-tree legality claim'}
