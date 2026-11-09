"""Index native CIDs by source/sink block using complete authenticated raw pins.

Sparse discovery requires an externally verified complete moved-block set and
same graph/netlist/CID translation. It cannot detect arbitrary unreported edits.
"""
from collections import defaultdict

def build_index(raw, mapping, physical_to_original):
    pins=mapping['pin_details'];sources={};sinks=defaultdict(list);order={}
    for pin in pins:
        nid=pin['net_id'];order.setdefault(nid,None)
        if pin['role']=='SOURCE':
            if nid in sources:raise ValueError('multiple source pins')
            sources[nid]=pin
        elif pin['role']=='SINK':sinks[nid].append(pin)
        else:raise ValueError('invalid pin role')
    ignored={r['net_id'] for r in raw['excluded_nets']};reconstructed=[];blocks=[]
    for nid in order:
        if nid in ignored:continue
        for sink in sinks[nid]:
            source=sources[nid];reconstructed.append(dict(connection_id=len(reconstructed),net_id=nid,source=source['rr_node'],sink=sink['rr_node']));blocks.append((source['block'],sink['block']))
    if reconstructed!=raw['connections']:raise ValueError('raw pin/connection identity mismatch')
    if len(set(physical_to_original))!=len(physical_to_original):raise ValueError('duplicate CID translation')
    index=defaultdict(set)
    for cid,original in enumerate(physical_to_original):
        if type(original) is not int or not 0<=original<len(blocks):raise ValueError('invalid CID translation')
        for block in blocks[original]:index[block].add(cid)
    return {block:frozenset(ids) for block,ids in index.items()}

def discover(index, moved_blocks, source, target):
    if len(source)!=len(target):raise ValueError('CID domain changed')
    candidates=set()
    for block in moved_blocks:
        # Blocks with no nonignored physical connection legitimately have no entry.
        candidates.update(index.get(block,()))
    delta=[]
    for cid in sorted(candidates):
        a,b=source[cid],target[cid]
        if a['connection_id']!=cid or b['connection_id']!=cid or a['net_id']!=b['net_id']:raise ValueError('CID/NET mismatch')
        if a!=b:delta.append(dict(old=a,new=b))
    return delta,len(candidates)
