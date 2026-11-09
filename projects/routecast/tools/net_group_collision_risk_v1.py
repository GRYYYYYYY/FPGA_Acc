"""Exact expected overflow for an explicit independent NET-choice prior.

One NET selects k distinct members of a unit-capacity group uniformly; NETs
are independent. Geometry/terminal grouping is a prior, not reachability proof.
"""
from fractions import Fraction

def independent_overflow(probabilities,capacity):
 if type(capacity) is not int or capacity<0:raise ValueError('capacity')
 ps=[]
 for p in probabilities:
  if type(p) is not int and not isinstance(p,Fraction):raise ValueError('exact rational probability required')
  p=Fraction(p)
  if not 0<=p<=1:raise ValueError('probability')
  ps.append(p)
 if capacity>=len(ps):return Fraction(0)
 distribution=[Fraction(0)]*(capacity+1);distribution[0]=Fraction(1);overflow=Fraction(0)
 for p in ps:
  overflow+=p*distribution[capacity]
  if capacity:
   following=[Fraction(0)]*(capacity+1);following[capacity]=distribution[capacity]+p*distribution[capacity-1]
   for k in range(capacity):following[k]=(1-p)*distribution[k]+(p*distribution[k-1] if k else 0)
   distribution=following
  assert sum(distribution)==1
 return overflow

def unit_group_expectation(size,occupancy_histogram):
 if type(size) is not int or size<1:raise ValueError('positive group size')
 mean=Fraction(0);empty=Fraction(1)
 for k,count in occupancy_histogram.items():
  if type(k) is not int or not 0<=k<=size or type(count) is not int or count<0:raise ValueError('NET occupancy histogram')
  mean+=count*Fraction(k,size);empty*=Fraction(size-k,size)**count
 overflow=mean-1+empty
 assert overflow>=0
 return dict(expected_occupancy=mean,probability_empty=empty,expected_overflow=overflow)
