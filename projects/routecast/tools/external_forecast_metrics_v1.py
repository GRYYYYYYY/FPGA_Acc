"""Exact capacity-normalized full-domain ranking and frozen four-metric gate."""
from collections import Counter
from fractions import Fraction
from prediction_metrics import compare

def vectors(resources,bins,ledger,node_count,*,truth=False):
    if any(type(n) is not int or not 0<=n<node_count or type(v) is not int or v<0 for n,v in ledger.items()):
        raise ValueError('ledger node/count domain')
    resource_scores={};spatial=Counter();capacity={}
    for row in bins:
        key=tuple(row['key']);cap=row['capacity']
        if key in capacity or type(cap) is not int or cap<=0:raise ValueError('spatial capacity')
        capacity[key]=cap
    for row in resources:
        nid=row['id'];cap=row['capacity']
        if type(nid) is not int or not 0<=nid<node_count or nid in resource_scores or type(cap) is not int or cap<=0:raise ValueError('resource identity/capacity')
        count=ledger.get(nid,0)
        if truth and count>cap:raise ValueError('native label capacity overflow')
        resource_scores[nid]=Fraction(count,cap)
        keys=[tuple(k) for k in row['bins']]
        if not keys or len(keys)!=len(set(keys)):raise ValueError('resource spatial membership')
        for key in keys:
            if key not in capacity:raise ValueError('unknown spatial bin')
            spatial[key]+=count
    if not resource_scores or not capacity:raise ValueError('empty metric domain')
    return dict(resource=resource_scores,spatial={k:Fraction(spatial[k],v) for k,v in capacity.items()})

def metrics(predicted,truth,resource_k,spatial_k):
    result={}
    for scope,k in [('resource',resource_k),('spatial',spatial_k)]:
        r=compare(predicted[scope],truth[scope],k)
        # Exact hit count is authoritative for precision gate comparisons.
        ids=sorted(truth[scope]);n=min(k,len(ids))
        p=sorted(ids,key=lambda i:(-predicted[scope][i],i))[:n]
        t=sorted(ids,key=lambda i:(-truth[scope][i],i))[:n]
        r.update(top_k_hits=len(set(p)&set(t)),prediction_top_k=p,truth_top_k=t)
        result[scope]=r
    return result

def gate(candidate,control):
    checks=[]
    for scope in ('resource','spatial'):
        a,b=candidate[scope],control[scope]
        if a['k']!=b['k'] or a['universe_size']!=b['universe_size']:raise ValueError('metric domains differ')
        x,y=a['spearman'],b['spearman'];defined=x is not None and y is not None
        checks.append(dict(metric=scope+'_spearman',defined=defined,nonregress=defined and x>=y-1e-12,strict=defined and x>y+1e-12))
        x,y=a['top_k_hits'],b['top_k_hits']
        checks.append(dict(metric=scope+'_precision_at_k',defined=True,nonregress=x>=y,strict=x>y))
    return dict(checks=checks,pass_primary_gate=all(c['nonregress'] for c in checks) and any(c['strict'] for c in checks))
