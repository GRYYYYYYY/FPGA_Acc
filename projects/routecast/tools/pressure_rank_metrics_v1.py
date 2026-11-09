"""Exact average-rank semantics via joint histograms; cached deterministic topK.

Vectors are in ascending domain-ID order; ties therefore use ascending index.
No calibration/MAE interpretation is assigned to risk scores.
"""
from collections import Counter
from math import sqrt,isfinite

def top(values,k):
 n=len(values)
 if not n or type(k) is not int or k<1:raise ValueError('domain/K')
 k=min(k,n);hist=Counter(values)
 if any(not isfinite(v) or v<0 for v in hist):raise ValueError('score domain')
 prior=0
 for cut,count in sorted(hist.items(),reverse=True):
  if prior+count>=k:break
  prior+=count
 selected={i for i,v in enumerate(values) if v>cut};needed=k-len(selected)
 for i,v in enumerate(values):
  if needed and v==cut:selected.add(i);needed-=1
  if not needed:break
 assert len(selected)==k
 return dict(n=n,k=k,hist=hist,selected=selected,boundary=cut,above=prior,equal=hist[cut])

def metric(pred,truth,pt,tt):
 if len(pred)!=len(truth) or pt['n']!=tt['n'] or pt['k']!=tt['k']:raise ValueError('incompatible vectors')
 n=pt['n'];k=pt['k'];joint=Counter(zip(pred,truth))
 def ranks(hist):
  result={};prior=0
  for value,count in sorted(hist.items()):result[value]=prior+(count-1)/2;prior+=count
  return result
 a=ranks(pt['hist']);b=ranks(tt['hist']);mean=(n-1)/2
 covariance=sum(count*(a[x]-mean)*(b[y]-mean) for (x,y),count in joint.items())
 variance_a=sum(count*(a[x]-mean)**2 for x,count in pt['hist'].items());variance_b=sum(count*(b[y]-mean)**2 for y,count in tt['hist'].items())
 corr=None if variance_a==0 or variance_b==0 else covariance/sqrt(variance_a*variance_b)
 hits=len(pt['selected']&tt['selected'])
 def interval(fixed,variable,values):
  above=sum(values[i]>variable['boundary'] for i in fixed)
  equal=sum(values[i]==variable['boundary'] for i in fixed)
  slots=k-variable['above']
  return [above+max(0,slots-(variable['equal']-equal)),above+min(slots,equal)]
 return dict(spearman=corr,k=k,precision_at_k=hits/k,recall_at_k=hits/k,universe_size=n,nonzero_truth=sum(count for value,count in tt['hist'].items() if value>0),truth_k_boundary=tt['boundary'],prediction_k_boundary=pt['boundary'],top_k_tie_rule='descending value then ascending resource ID',truth_strictly_above=tt['above'],truth_equal_boundary=tt['equal'],prediction_strictly_above=pt['above'],prediction_equal_boundary=pt['equal'],fixed_prediction_truth_tie_hit_interval=interval(pt['selected'],tt,truth),fixed_truth_prediction_tie_hit_interval=interval(tt['selected'],pt,pred))
