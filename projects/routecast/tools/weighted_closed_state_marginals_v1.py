"""Complete closed-state partition sums for one small dependency component.

State weight is exp(sum(theta[n]*x[n])) on every implication-closed binary
assignment. All branches covered; logarithmic floating arithmetic is approximate.
"""
import math


def calculate(weights,edges):
    nodes=sorted(weights);n=len(nodes);index={u:i for i,u in enumerate(nodes)}
    if any(not math.isfinite(w) for w in weights.values()):raise ValueError('finite log weights required')
    successors=[1<<i for i in range(n)];neighbors=[0]*n
    for u,v in edges:
        if u not in index or v not in index:raise ValueError('unknown endpoint')
        a,b=index[u],index[v];successors[a]|=1<<b;neighbors[a]|=1<<b;neighbors[b]|=1<<a
    for k in range(n):
        for i in range(n):
            if successors[i]>>k&1:successors[i]|=successors[k]
    ancestors=[sum(1<<i for i in range(n) if successors[i]>>j&1) for j in range(n)]
    theta=[weights[u] for u in nodes];cache={0:(0.,tuple(0. for _ in nodes))};trace={0:dict(kind='empty',logZ=0.,marginals=list(cache[0][1]))}
    def visit(free):
        if free in cache:return cache[free]
        # Factor disconnected residual components before branching.
        remaining=free;parts=[]
        while remaining:
            first=remaining&-remaining;part=0;pending=first
            while pending:
                bit=pending&-pending;pending^=bit
                if part&bit:continue
                part|=bit;pending|=neighbors[bit.bit_length()-1]&free&~part
            parts.append(part);remaining&=~part
        if len(parts)>1:
            values=[visit(p) for p in parts];logZ=math.fsum(z for z,m in values);marg=tuple(math.fsum(m[i] for z,m in values) for i in range(n));record=dict(kind='product',children=parts)
        else:
            bit=free&-free;i=bit.bit_length()-1;forced_A=ancestors[i]&free;forced_B=successors[i]&free;a=free&~forced_A;b=free&~forced_B;za,ma=visit(a);zb,mb=visit(b);zb+=math.fsum(theta[j] for j in range(n) if forced_B>>j&1)
            top=max(za,zb);wa=math.exp(za-top);wb=math.exp(zb-top);pa=wa/(wa+wb);pb=wb/(wa+wb);logZ=top+math.log(wa+wb)
            marg=tuple(pa*ma[j]+pb*(1. if forced_B>>j&1 else mb[j]) for j in range(n));record=dict(kind='branch',vertex=i,child_A=a,child_B=b,forced_A=forced_A,forced_B=forced_B)
        if not math.isfinite(logZ) or any(not -1e-14<=p<=1+1e-14 for p in marg):raise ValueError('partition arithmetic failure')
        cache[free]=(logZ,marg);trace[free]=dict(record,logZ=logZ,marginals=list(marg));return cache[free]
    full=(1<<n)-1;logZ,marg=visit(full)
    return dict(nodes=nodes,log_partition=logZ,marginals={u:marg[i] for i,u in enumerate(nodes)},states=len(cache),trace={str(k):v for k,v in trace.items()})
