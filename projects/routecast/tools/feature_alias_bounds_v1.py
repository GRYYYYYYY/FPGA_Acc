"""Exact binary Hamming and ROC limits for functions constant on feature classes."""
from fractions import Fraction as F

def limits(groups):
 groups=list(groups)
 if not groups or any(type(n) is not int or type(p) is not int or n<1 or not 0<=p<=n for n,p in groups):raise ValueError('positive class size and binary count required')
 positives=sum(p for n,p in groups);negatives=sum(n-p for n,p in groups);rates=[F(p,n) for n,p in groups];order=sorted(range(len(groups)),key=lambda i:rates[i]);twice=0;negative_before=0;i=0
 while i<len(order):
  j=i+1
  while j<len(order) and rates[order[j]]==rates[order[i]]:j+=1
  pos=sum(groups[k][1] for k in order[i:j]);neg=sum(groups[k][0]-groups[k][1] for k in order[i:j]);twice+=pos*(2*negative_before+neg);negative_before+=neg;i=j
 return {'minimum_binary_errors':sum(min(p,n-p) for n,p in groups),'maximum_ROC_AUC':F(twice,2*positives*negatives) if positives and negatives else None,'majority_decisions':[int(2*p>=n) for n,p in groups],'oracle_rates':rates,'conflicting_groups':sum(0<p<n for n,p in groups),'resources_in_conflicting_groups':sum(n for n,p in groups if 0<p<n)}
