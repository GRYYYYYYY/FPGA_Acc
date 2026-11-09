"""Two-pass additive CSR assembly from compact nodes and repeatable raw arcs.

Arc factory yields (raw edge ID, source ID, destination ID, switch ID, cost).
Full graph XML, RC provenance and node cost bindings remain caller obligations.
"""
import hashlib,json,struct,sys
from array import array
from pathlib import Path
from prepared_csr import U64,TYPES,DIRECTIONS,SIDES,side_codes
from pre_route_endpoints import sha

NODE_FIELDS=('types','directions','sides','capacities','segments','xlow','xhigh','ylow','yhigh','layer','ptc')

def write(nodes, arc_factory, out, context):
    out=Path(out)
    if out.exists():raise ValueError('fresh output required')
    fields={name:array(data.typecode,data) for name,data in nodes.items()}
    ids=fields['node_ids'];n=len(ids)
    if ids.typecode!='Q' or list(ids)!=sorted(set(ids)):
        raise ValueError('node IDs must be sorted unique uint64')
    for name in NODE_FIELDS:
        kind='B' if name in ('types','directions','sides') else 'q' if name in ('xlow','xhigh','ylow','yhigh','layer','ptc') else 'Q'
        if name not in fields or len(fields[name])!=n or fields[name].typecode!=kind:
            raise ValueError('invalid node payload')
    for name,codes in (('types',TYPES),('directions',DIRECTIONS),('sides',SIDES)):
        if any(v not in codes.values() for v in fields[name]):raise ValueError('invalid node enum')
    rank={v:i for i,v in enumerate(ids)}
    degree=array('Q',[0])*n
    def checked_arcs():
        for expected,values in enumerate(arc_factory()):
            if len(values)!=5:raise ValueError('invalid arc record')
            eid,source,dest,switch,cost=values
            if any(type(v) is not int or v<0 or v>=U64 for v in (eid,source,dest,switch)) or eid!=expected:
                raise ValueError('raw arcs must retain contiguous ascending IDs')
            if source not in rank or dest not in rank:raise ValueError('unknown arc node')
            if cost is not None and (type(cost) is not int or not 0<=cost<U64):raise ValueError('invalid arc cost')
            yield eid,rank[source],rank[dest],switch,U64 if cost is None else cost
    digest=hashlib.sha256();e=0
    for arc in checked_arcs():
        degree[arc[1]]+=1;e+=1;digest.update(struct.pack('<5Q',*arc))
    rows=array('Q',[0])
    for d in degree:rows.append(rows[-1]+d)
    fields['row_offsets']=rows
    for name in ('edge_ids','dest_ranks','switch_ids','costs'):fields[name]=array('Q',[0])*e
    cursor=array('Q',rows[:-1]);second=hashlib.sha256();count=0
    for arc in checked_arcs():
        eid,source,dest,switch,cost=arc
        slot=cursor[source]
        if slot>=rows[source+1]:raise ValueError('arc factory changed degrees')
        cursor[source]+=1;count+=1;second.update(struct.pack('<5Q',*arc))
        for name,value in zip(('edge_ids','dest_ranks','switch_ids','costs'),(eid,dest,switch,cost)):fields[name][slot]=value
    if count!=e or second.digest()!=digest.digest():raise ValueError('arc factory changed between passes')
    out.mkdir();files={}
    for name,data in fields.items():
        if sys.byteorder!='little':data.byteswap()
        path=out/(name+'.bin')
        with path.open('wb') as f:data.tofile(f)
        files[name]={'file':path.name,'type':data.typecode,'elements':len(data),'bytes':path.stat().st_size,'sha256':sha(path)}
    context=dict(context);context.update(cost_payload_sha256=files['costs']['sha256'],edge_mapping_sha256=files['edge_ids']['sha256'])
    manifest={'schema':'ROUTECAST_PREPARED_ADDITIVE_CSR_V1','byteorder':'little','nodes':n,'edges':e,'disabled_cost_sentinel':U64,'context':context,'context_sha256':hashlib.sha256(json.dumps(context,sort_keys=True).encode()).hexdigest(),'type_codes':TYPES,'direction_codes':DIRECTIONS,'side_codes':side_codes(fields['sides']),'files':files,'scope':'independent additive search transport; no RC tree prefix, epochs or dynamic pressure representation'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
