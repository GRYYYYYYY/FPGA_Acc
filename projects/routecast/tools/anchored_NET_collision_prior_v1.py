"""NET-independent fixed-set/uniform-k-subset mixture, exact RR marginals.

Uniform geometry pools are modeling assumptions, not reachability proofs.
Weight is the probability of uniform redraw; zero retains observed node sets.
"""
from fractions import Fraction

def marginal(size,histogram,owner_histogram,weight=Fraction(1,2)):
 if type(size) is not int or size<1:raise ValueError('positive size')
 if type(weight) is not int and not isinstance(weight,Fraction):raise ValueError('exact weight')
 weight=Fraction(weight)
 if not 0<=weight<=1:raise ValueError('weight range')
 if any(type(k) is not int or not 0<=k<=size or type(v) is not int or v<0 for k,v in histogram.items()):raise ValueError('NET histogram')
 if any(type(k) is not int or k not in histogram or type(v) is not int or not 0<=v<=histogram[k] for k,v in owner_histogram.items()):raise ValueError('owner histogram')
 if owner_histogram.get(0,0) or owner_histogram.get(size,0)!=histogram.get(size,0):raise ValueError('impossible owner histogram')
 mean=Fraction(0);empty=Fraction(1)
 for k,count in histogram.items():
  owners=owner_histogram.get(k,0);free=count-owners
  p_free=weight*Fraction(k,size);p_owned=1-weight+p_free
  mean+=owners*p_owned+free*p_free
  empty*=(1-p_owned)**owners*(1-p_free)**free
 risk=mean-1+empty
 assert risk>=0
 return dict(expected_occupancy=mean,probability_empty=empty,expected_overflow=risk)
