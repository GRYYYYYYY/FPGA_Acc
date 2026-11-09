"""Exact rational present multiplier; experimental cost, not native float arithmetic."""
from fractions import Fraction

def cost(base, accumulated_factor, occupancy, capacity, present_factor, old_owner=False, static_price=0):
 if any(type(v) is not int or v<0 for v in (base,occupancy,capacity,static_price)):
  raise ValueError('nonnegative integer resource domain')
 if type(accumulated_factor) is not Fraction or accumulated_factor<1 or type(present_factor) is not Fraction or present_factor<0 or type(old_owner) is not bool:
  raise ValueError('exact nonnegative factors and boolean owner required')
 if old_owner and occupancy==0:raise ValueError('old owner absent')
 if occupancy and capacity==0:raise ValueError('owned zero capacity')
 other=occupancy-int(old_owner)
 pressure=max(0,other-capacity+1)
 return base*accumulated_factor*(1+pressure*present_factor)+static_price
