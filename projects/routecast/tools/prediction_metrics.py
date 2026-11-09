"""Deterministic descriptive metrics; undefined correlations are explicit None."""
import math


def ranks(values):
    order=sorted(range(len(values)),key=lambda i:values[i]); result=[0.0]*len(values); start=0
    while start<len(order):
        end=start+1
        while end<len(order) and values[order[end]]==values[order[start]]: end+=1
        rank=(start+end-1)/2
        for i in order[start:end]: result[i]=rank
        start=end
    return result


def spearman(x,y):
    if len(x)!=len(y) or not x: raise ValueError('incompatible vectors')
    a,b=ranks(x),ranks(y); mean=(len(x)-1)/2
    cross=sum((u-mean)*(v-mean) for u,v in zip(a,b))
    denom=math.sqrt(sum((u-mean)**2 for u in a)*sum((v-mean)**2 for v in b))
    return None if denom==0 else cross/denom


def compare(predicted,truth,k):
    if set(predicted)!=set(truth) or not predicted or type(k) is not int or k<1: raise ValueError('invalid evaluation')
    ids=sorted(truth); k=min(k,len(ids))
    p=sorted(ids,key=lambda nid:(-predicted[nid],nid))[:k]
    t=sorted(ids,key=lambda nid:(-truth[nid],nid))[:k]
    overlap=len(set(p)&set(t))
    # Both sets contain k IDs, so precision and recall at k coincide here.
    return {'spearman':spearman([predicted[n] for n in ids],[truth[n] for n in ids]),
            'k':k,'precision_at_k':overlap/k,'recall_at_k':overlap/k,
            'mae':sum(abs(predicted[n]-truth[n]) for n in ids)/len(ids),
            'universe_size':len(ids),'nonzero_truth':sum(truth[n]>0 for n in ids),
            'top_k_tie_rule':'descending value then ascending resource ID',
            'truth_k_boundary':truth[t[-1]],'prediction_k_boundary':predicted[p[-1]]}
