"""Exact tie-averaged pressure capture and registered prospective gate."""
from fractions import Fraction
from collections import Counter
from math import sqrt

def metrics(scores,truth,k,ids):
 assert len(scores)==len(truth)==len(ids) and 0<k<=len(scores) and len(set(ids))==len(ids)
 total=sum(truth);assert all(v>=0 for v in truth)
 if not total:return dict(status='unassessable',spearman=None,capture=None)
 counts=[Counter(scores),Counter(truth)];ranks=[]
 for counts1 in counts:
  offset=0;rank={}
  for v,n in sorted(counts1.items()):rank[v]=2*offset+n-1;offset+=n
  ranks.append(rank)
 mean=len(scores)-1;x=[ranks[0][v]-mean for v in scores];y=[ranks[1][v]-mean for v in truth];xx=sum(v*v for v in x);yy=sum(v*v for v in y);rho=sum(a*b for a,b in zip(x,y))/sqrt(xx*yy) if xx and yy else None
 order=sorted(range(len(ids)),key=lambda i:(-scores[i],ids[i]));boundary=scores[order[k-1]];above=[i for i,v in enumerate(scores) if v>boundary];tie=[i for i,v in enumerate(scores) if v==boundary];capture=(Fraction(sum(truth[i] for i in above))+Fraction((k-len(above))*sum(truth[i] for i in tie),len(tie)))/total
 return dict(status='evaluated',spearman=rho,capture=str(capture),fixed_ID_capture=str(Fraction(sum(truth[i] for i in order[:k]),total)),target_mass=total)

def gate(candidate,controls,k,n):
 if candidate['capture'] is None or candidate['spearman'] is None:return 'unassessable'
 c=Fraction(candidate['capture']);rho=candidate['spearman']
 for name,reference in controls.items():
  if name=='uniform_risk':
   assert reference['spearman'] is None and Fraction(reference['capture'])==Fraction(k,n)
   if c<=Fraction(k,n):return 'fail'
  else:
   if reference['capture'] is None or reference['spearman'] is None:return 'unassessable'
   t=Fraction(reference['capture']);r=reference['spearman']
   if c<t or rho<r-1e-12 or not(c>t or rho>r+1e-12):return 'fail'
 return 'pass'
