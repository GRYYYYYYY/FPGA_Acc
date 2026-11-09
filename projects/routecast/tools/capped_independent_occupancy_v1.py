"""Exact capped occupancy under independent NET inclusion probabilities.

This is a distributional forecast, not conditioning on a feasible routing.
"""
from fractions import Fraction as F

def moments(probabilities,capacity):
 if type(capacity) is not int or capacity<0:raise ValueError('nonnegative integer capacity required')
 probabilities=list(probabilities)
 if any(type(p) not in (int,F) or not 0<=p<=1 for p in probabilities):raise ValueError('exact rational inclusion probabilities required')
 # Last cell absorbs all X>=capacity+1. Hence the strict overflow event
 # remains distinguishable even when capacity=0.
 limit=min(capacity+1,len(probabilities)+1);mass=[F(1)]+[F(0)]*limit
 for p in probabilities:
  p=F(p);updated=[F(0)]*len(mass)
  for k,value in enumerate(mass):
   updated[k]+=value*(1-p);updated[min(k+1,limit)]+=value*p
  mass=updated
 expected=sum(map(F,probabilities),F(0));capped=sum((min(k,capacity)*v for k,v in enumerate(mass)),F(0));over_probability=mass[-1] if capacity<len(probabilities) else F(0)
 assert sum(mass)==1 and 0<=capped<=capacity and capped<=expected
 return {'expected_demand':expected,'expected_capped_occupancy':capped,'expected_excess':expected-capped,'probability_over_capacity':over_probability}
