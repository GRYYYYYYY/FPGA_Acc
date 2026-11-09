"""Join deterministic frontend pin traversal to physical sketch witnesses.

Within equivalent (net,SINK) groups, frontend sink traversal order defines CID
order. This records nominal packed-pin mapping, not native pin permutation.
"""
from collections import defaultdict,deque
from pin_choice_catalog import PinChoiceCatalog
from physical_prediction_audit import audit


def join(graph,endpoints,mapping,prediction):
    audit(graph,endpoints,prediction);catalog=PinChoiceCatalog(graph)
    active={r['net_id'] for r in endpoints['connections']};sources={};sinks=defaultdict(deque);seen=set()
    for detail in mapping['pin_details']:
        if detail['net_id'] not in active:continue
        identity=(detail['block'],detail['port'],detail['bit'],detail['role'])
        if identity in seen:raise ValueError('duplicate packed pin identity')
        seen.add(identity)
        role=detail['role'];node=detail['rr_node'];ptc=detail['physical_pin_ptc']
        if type(node) is not int or type(ptc) is not int:raise ValueError('invalid class/pin identity')
        pools=catalog.sources if role=='SOURCE' else catalog.sinks if role=='SINK' else None
        if pools is None or node not in pools or ptc not in pools[node].physical_pins:raise ValueError('nominal pin outside graph class')
        if role=='SOURCE':
            if detail['net_id'] in sources:raise ValueError('multiple packed drivers')
            sources[detail['net_id']]=detail
        else:sinks[(detail['net_id'],node)].append(detail)
    paths={r['connection_id']:r for r in prediction['connections']};rows=[]
    for endpoint in sorted(endpoints['connections'],key=lambda r:r['connection_id']):
        cid=endpoint['connection_id'];net=endpoint['net_id'];key=(net,endpoint['sink'])
        if net not in sources or sources[net]['rr_node']!=endpoint['source'] or not sinks[key]:raise ValueError('packed endpoint cohort mismatch')
        source=sources[net];sink=sinks[key].popleft();w=catalog.witness(endpoint['source'],endpoint['sink'],paths[cid]['physical_edge_ids'])
        rows.append({'connection_id':cid,'net_id':net,'packed_source':{k:source[k] for k in ('block','port','bit','physical_pin_ptc')},'packed_sink':{k:sink[k] for k in ('block','port','bit','physical_pin_ptc')},'path_pin_witness':w,'selected_opin_matches_nominal_ptc':w['selected_opin_ptc']==source['physical_pin_ptc'],'selected_ipin_matches_nominal_ptc':w['selected_ipin_ptc']==sink['physical_pin_ptc']})
    if any(sinks.values()):raise ValueError('unconsumed packed sinks')
    return rows
