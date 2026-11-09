"""Conservative closure for atomic nets and SOURCE-group regional context."""


def affected(before,after):
    if before['graph_sha256']!=after['graph_sha256']:raise ValueError('graph changed; full invalidation required')
    def index(endpoint):
        rows={};roots={}
        for r in endpoint['connections']:
            if set(r)!={'connection_id','net_id','source','sink'}:raise ValueError('invalid endpoint fields')
            if any(type(v) is not int or v<0 for v in r.values()):raise ValueError('invalid endpoint identity')
            cid=r['connection_id'];net=r['net_id'];source=r['source']
            if cid in rows:raise ValueError('duplicate connection identity')
            if net in roots and roots[net]!=source:raise ValueError('net has mixed sources')
            rows[cid]=r;roots[net]=source
        return rows
    a=index(before);b=index(after);changed={c for c in set(a)|set(b) if a.get(c)!=b.get(c)}
    nets=set();sources=set()
    for c in changed:
        for row in (a.get(c),b.get(c)):
            if row:nets.add(row['net_id']);sources.add(row['source'])
    allrows=list(a.values())+list(b.values());expanded=True
    while expanded:
        expanded=False
        for r in allrows:
            if r['net_id'] in nets or r['source'] in sources:
                if r['net_id'] not in nets or r['source'] not in sources:expanded=True
                nets.add(r['net_id']);sources.add(r['source'])
    old={c for c,r in a.items() if r['net_id'] in nets};new={c for c,r in b.items() if r['net_id'] in nets}
    return {'changed_connection_ids':sorted(changed),'affected_net_ids':sorted(nets),'affected_source_ids':sorted(sources),'remove_connection_ids':sorted(old-set(b)),'recompute_connection_ids':sorted(new),'retained_connection_ids':sorted(set(b)-new),'scope':'fixed graph; whole-net atomic and complete SOURCE-group context closure'}
