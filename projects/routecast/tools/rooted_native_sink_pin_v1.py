"""Resolve a routed SINK from actual IPIN and post-route native pin identity.

Native routing may permute equivalent physical input pins. The routed IPIN is
the witness, rather than an old port/bit assignment or a SINK bbox corner.
"""
def root(node,grid):
    loc=node['loc'];layer=int(loc.get('layer',0));owners=set()
    xl,xh,yl,yh=[int(loc[k]) for k in ['xlow','xhigh','ylow','yhigh']]
    if xl>xh or yl>yh:raise ValueError('reversed endpoint bbox')
    for x in range(xl,xh+1):
        for y in range(yl,yh+1):
            tid,dx,dy=grid[x,y,layer];owners.add((tid,x-dx,y-dy,layer))
    if len(owners)!=1:raise ValueError('endpoint crosses rooted tiles')
    return next(iter(owners))

def resolve(record,ipin,sink,grid,pin_classes):
    if ipin['type']!='IPIN' or sink['type']!='SINK':raise ValueError('SINK requires routed IPIN witness')
    a,b=root(ipin,grid),root(sink,grid)
    if a!=b:raise ValueError('IPIN/SINK root mismatch')
    tid,x,y,layer=a;physical=int(ipin['loc']['ptc']);cls=int(sink['loc']['ptc'])
    if pin_classes[tid].get(physical)!=cls:raise ValueError('physical IPIN not in SINK class')
    options=[p for p in record['pins'] if p['index']>0 and
             (p['x'],p['y'],p['layer'],p['physical_pin'],p['class'])==(x,y,layer,physical,cls)]
    if len(options)!=1:raise ValueError('missing or ambiguous post-route physical pin')
    return options[0]['index']
