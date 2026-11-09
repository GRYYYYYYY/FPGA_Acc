"""Exact rational present factor, integer-lattice ceil; not native float parity."""
from fractions import Fraction

def cost(base,history,occupancy,capacity,present_factor,old_owner=False,static_price=0):
 if any(type(v) is not int or v<0 for v in [base,history,occupancy,capacity,static_price]) or type(old_owner) is not bool:raise ValueError('integer domain')
 if not isinstance(present_factor,(int,Fraction)) or isinstance(present_factor,bool) or present_factor<0:raise ValueError('present factor')
 if old_owner and occupancy==0:raise ValueError('old owner absent')
 if occupancy and capacity==0:raise ValueError('owned zero capacity')
 other=occupancy-int(old_owner);scaled=Fraction(base*(1+history))*(1+present_factor*max(0,other-capacity+1));return -(-scaled.numerator//scaled.denominator)+static_price
