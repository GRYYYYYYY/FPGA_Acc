"""Exact absolute-count loss factorization. Target-dependent diagnostic primitive."""
from collections import defaultdict

def factorize(pools,truth,domain):
 domain=set(domain)
 if not pools or not domain or not set(truth)<=domain or any(type(v) is not int or v<0 for v in truth.values()):raise ValueError('factorization truth/domain')
 fixed=defaultdict(int);variable=defaultdict(dict);cards={}
 for net,choices in sorted(pools.items()):
  if type(net) is not int or not choices or any(not set(c)<=domain for c in choices):raise ValueError('candidate domain')
  cards[net]=len(choices)
  for node in set.union(*(set(c) for c in choices)):
   pattern=tuple(int(node in c) for c in choices)
   if all(pattern):fixed[node]+=1
   else:variable[node][net]=pattern
 constant=0;unary={n:[0]*d for n,d in cards.items()};terms=[];nonlinear=[]
 for node in sorted(domain):
  low=fixed[node];patterns=variable[node];high=low+len(patterns);target=truth.get(node,0);row={'node':node,'fixed_count':low,'upper_count':high,'target':target,'patterns':{n:list(p) for n,p in sorted(patterns.items())}}
  if low>=target:sign=1;row['kind']='affine_positive';constant+=low-target
  elif high<=target:sign=-1;row['kind']='affine_negative';constant+=target-low
  else:row['kind']='nonlinear';nonlinear.append(row);terms.append(row);continue
  for net,pattern in patterns.items():
   for i,bit in enumerate(pattern):unary[net][i]+=sign*bit
  terms.append(row)
 shifts={n:min(costs) for n,costs in unary.items()}
 for n,costs in unary.items():constant+=shifts[n];unary[n]=[v-shifts[n] for v in costs]
 if constant<0:raise ArithmeticError('affine normalization must preserve nonnegative lower constant')
 return {'constant':constant,'cardinalities':cards,'unary':unary,'unary_shifts':shifts,'nonlinear':nonlinear,'node_terms':terms}

def value(factors,selection):
 return factors['constant']+sum(costs[selection[n]] for n,costs in factors['unary'].items())+sum(abs(t['fixed_count']+sum(bits[selection[n]] for n,bits in t['patterns'].items())-t['target']) for t in factors['nonlinear'])
