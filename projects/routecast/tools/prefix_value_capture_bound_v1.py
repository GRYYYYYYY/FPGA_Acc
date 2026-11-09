"""Exact oracle ceiling for scores that depend only on a scalar prefix value.

Future target mass is used solely for a diagnostic upper bound. Groups with
identical observable values cannot be split by such a scoring function. The
score-boundary tie is sampled uniformly, as in the frozen temporal diagnostic.
"""
from collections import defaultdict
from fractions import Fraction

def ceiling(prefix, target, k):
    if len(prefix)!=len(target) or not prefix or type(k) is not int or not 1<=k<=len(prefix):
        raise ValueError('domain/k')
    groups=defaultdict(lambda:[0,0])
    for observable,mass in zip(prefix,target):
        if type(observable) is not int or observable<0 or type(mass) is not int or mass<0:
            raise ValueError('nonnegative integer data required')
        groups[observable][0]+=1;groups[observable][1]+=mass
    total=sum(target)
    if total==0:raise ValueError('zero target mass')
    order=sorted(groups,key=lambda value:(-Fraction(groups[value][1],groups[value][0]),value))
    remaining=k;captured=Fraction(0);allocation=[]
    for value in order:
        count,mass=groups[value];take=min(remaining,count)
        captured+=Fraction(take*mass,count);allocation.append(dict(value=value,count=count,mass=mass,selected=take))
        remaining-=take
        if not remaining:break
    return dict(capture=captured/total,allocation=allocation,groups=dict(groups),total_mass=total)
