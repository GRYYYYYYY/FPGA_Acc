"""Necessary/guaranteed deterministic top-K membership from valid bin intervals."""
def rank_bounds(lower,upper,capacities,k):
 n=len(lower)
 if not n or len(upper)!=n or len(capacities)!=n or type(k) is not int or not 1<=k<=n:raise ValueError('rank domains')
 if any(type(x) is not int or x<0 for x in [*lower,*upper]) or any(type(c) is not int or c<=0 for c in capacities) or any(a>b for a,b in zip(lower,upper)):raise ValueError('invalid intervals/capacities')
 rows=[]
 for t in range(n):
  certain=[];possible=[]
  for b in range(n):
   if b==t:continue
   left,right=lower[b]*capacities[t],upper[t]*capacities[b]
   if left>right or left==right and b<t:certain.append(b)
   left,right=upper[b]*capacities[t],lower[t]*capacities[b]
   if left>right or left==right and b<t:possible.append(b)
  rows.append({'best_rank_lower_bound':1+len(certain),'worst_rank_upper_bound':1+len(possible),'excluded_from_topK':len(certain)>=k,'guaranteed_in_topK':len(possible)<k,'certain_outrankers':certain})
 return rows
