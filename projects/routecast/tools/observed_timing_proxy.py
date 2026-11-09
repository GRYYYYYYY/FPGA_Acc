"""Frozen-baseline reported-path proxies, not STA or full criticality.

Physical sink equivalence groups use the maximum over all matching stable IDs.
Candidate coordinates may change; identity joins use baseline IDs/net identity.
"""
from collections import defaultdict
from decimal import Decimal,ROUND_HALF_UP
import xml.etree.ElementTree as ET


def path_deltas(graph,baseline,candidate,context):
    def index(pred):
        if pred['physical_graph_sha256']!=graph.sha256:raise ValueError('graph identity mismatch')
        rows={}
        for r in pred['connections']:
            cid=r['connection_id']
            if type(cid) is not int or cid<0 or cid in rows:raise ValueError('invalid/duplicate connection ID')
            rows[cid]=r
        return rows
    old=index(baseline);new=index(candidate)
    if set(old)!=set(new) or any(old[c]['net_id']!=new[c]['net_id'] for c in old):raise ValueError('fixed-packing identity changed')
    groups=defaultdict(list)
    for cid,r in old.items():groups[(r['net_id'],r['source'],r['sink'])].append(cid)
    delays={}
    for sid,xml in graph.switches.items():
        timing=ET.fromstring(xml).find('timing');value=Decimal(timing.attrib.get('Tdel','0')) if timing is not None else Decimal(0)
        if not value.is_finite() or value<0:raise ValueError('invalid switch delay')
        delays[sid]=int((value*Decimal(10**12)).to_integral_value(rounding=ROUND_HALF_UP))
    def metric(r):
        n=r['source'];visited={n};span=0;delay=0
        if n not in graph.nodes or graph.nodes[n].type!='SOURCE' or r['physical_edge_ids'] is None:raise ValueError('missing valid candidate path')
        for eid in r['physical_edge_ids']:
            if type(eid) is not int or eid<0 or eid>=len(graph.edges):raise ValueError('invalid edge')
            edge=graph.edges[eid]
            if edge.source!=n or edge.sink in visited:raise ValueError('invalid path continuity')
            n=edge.sink;visited.add(n);node=graph.nodes[n]
            if node.type in {'CHANX','CHANY'}:
                loc=dict(node.location);span+=max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1
            delay+=delays[edge.switch_id]
        if n!=r['sink'] or graph.nodes[n].type!='SINK':raise ValueError('wrong sink')
        return span,delay
    group_metrics={};paths=[]
    for path in context['paths']:
        span_delta=delay_delta=0
        for value in path['endpoint_groups']:
            group=tuple(value)
            if group not in groups:raise ValueError('timing group missing from baseline')
            if group not in group_metrics:
                ids=groups[group];a=[metric(old[c]) for c in ids];b=[metric(new[c]) for c in ids]
                group_metrics[group]={'baseline_ids':list(ids),'span_delta':max(x[0] for x in b)-max(x[0] for x in a),'switch_delay_delta_ps':max(x[1] for x in b)-max(x[1] for x in a)}
            span_delta+=group_metrics[group]['span_delta'];delay_delta+=group_metrics[group]['switch_delay_delta_ps']
        paths.append({'rank':path['rank'],'span_delta':span_delta,'switch_delay_delta_ps':delay_delta})
    if not paths:raise ValueError('empty timing context')
    return {'observed_path_max_span_delta':max(p['span_delta'] for p in paths),'observed_path_max_switch_delay_delta_ps':max(p['switch_delay_delta_ps'] for p in paths),'covered_groups':len(group_metrics),'paths':paths,'group_metrics':[{'group':list(k),**v} for k,v in sorted(group_metrics.items())],'scope':'partial baseline observed-path proxies; no RC/fanout/intra-block/new-path timing or CPD guarantee'}
