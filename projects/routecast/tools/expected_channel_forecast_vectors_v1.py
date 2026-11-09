"""Complete rational expected-count forecasts; separate from integer physical ledgers."""
from fractions import Fraction
from collections import defaultdict

def vectors(resources,bins,expected_counts,node_count):
 ids={r['id'] for r in resources}
 if len(ids)!=len(resources) or set(expected_counts)!=ids:raise ValueError('complete unique expected-count domain required')
 capacities={};totals=defaultdict(Fraction);observed=defaultdict(int);scores={}
 for b in bins:
  key=tuple(b['key']);cap=b['capacity']
  if key in capacities or type(cap) is not int or cap<=0:raise ValueError('spatial capacity domain')
  capacities[key]=cap
 for r in resources:
  n=r['id'];cap=r['capacity'];q=expected_counts[n]
  if type(n) is not int or not 0<=n<node_count or type(cap) is not int or cap<=0:raise ValueError('resource domain')
  if type(q) is not Fraction or not 0<=q<=cap:raise ValueError('rational expected-count range')
  keys=[tuple(k) for k in r['bins']]
  if not keys or len(keys)!=len(set(keys)) or not set(keys)<=capacities.keys():raise ValueError('spatial memberships')
  scores[n]=q/cap
  for key in keys:totals[key]+=q;observed[key]+=cap
 if not scores or observed!=capacities:raise ValueError('complete spatial capacity coverage required')
 return dict(resource=scores,spatial={key:totals[key]/cap for key,cap in capacities.items()})
