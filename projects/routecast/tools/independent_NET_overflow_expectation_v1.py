"""Exact unit-capacity prior statistics, assuming independent NET occupancies.

Inputs are unique-NET inclusion marginals, not independent sink marginals.
Actual native occupancies need not follow this prior. No calibrated predictor
or new native surcharge is implemented here.
"""
from fractions import Fraction

def unit_capacity(probabilities):
 ps=[Fraction(p) for p in probabilities]
 if any(p<0 or p>1 for p in ps):raise ValueError('invalid NET marginal')
 mean=sum(ps,Fraction(0));ones=sum(p==1 for p in ps);p0=Fraction(1)
 for p in ps:p0*=1-p
 if ones>=2:p1=Fraction(0)
 elif ones==1:
  p1=Fraction(1)
  for p in ps:
   if p!=1:p1*=1-p
 else:p1=p0*sum((p/(1-p) for p in ps),Fraction(0))
 expected_overflow=mean-1+p0;probability_overflow=1-p0-p1;mean_excess=max(Fraction(0),mean-1)
 assert 0<=probability_overflow<=1 and expected_overflow>=mean_excess>=0
 return dict(mean=mean,mean_excess=mean_excess,expected_overflow=expected_overflow,probability_overflow=probability_overflow,probability_empty=p0,probability_exactly_one=p1,jensen_gap=expected_overflow-mean_excess)
