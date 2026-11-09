"""Independent residual negative-cycle check of additive assignment optimality."""
def verify(costs,assignment):
    if set(costs)!=set(assignment):raise ValueError('request cohort mismatch')
    if not costs:return {'optimal':True,'total_cost':0,'scope':'empty assignment'}
    used={tuple(p):r for r,p in assignment.items()}
    if len(used)!=len(assignment):raise ValueError('noninjective assignment')
    pins={p for options in costs.values() for p in options};edges=[]
    for r,options in costs.items():
        selected=tuple(assignment[r])
        if selected not in options:raise ValueError('nonmember selected pin')
        for p,c in options.items():
            if type(c) is not int or c<0:raise ValueError('invalid cost')
            left=('request',r);right=('pin',p)
            edges.append((right,left,-c) if p==selected else (left,right,c))
    reservoir=('reservoir',)
    for p in pins:
        node=('pin',p)
        edges.append((reservoir,node,0) if p in used else (node,reservoir,0))
    nodes={n for a,b,_ in edges for n in (a,b)};dist={n:0 for n in nodes}
    for iteration in range(len(nodes)):
        changed=False
        for a,b,c in edges:
            if dist[b]>dist[a]+c:dist[b]=dist[a]+c;changed=True
        if not changed:return {'optimal':True,'total_cost':sum(costs[r][tuple(p)] for r,p in assignment.items()),'scope':'supplied additive matching only'}
    return {'optimal':False,'total_cost':sum(costs[r][tuple(p)] for r,p in assignment.items()),'scope':'negative residual cycle proves cheaper supplied matching exists'}
