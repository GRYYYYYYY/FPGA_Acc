"""Integer acc_fac1/pres_fac1 experimental cost, not live native equivalence."""
def cost(base, accumulated_overuse, occupancy, capacity, old_owner=False, static_price=0):
 values=(base,accumulated_overuse,occupancy,capacity,static_price)
 if any(type(v) is not int or v<0 for v in values) or type(old_owner) is not bool:
  raise ValueError('nonnegative integer domain and boolean owner required')
 if old_owner and occupancy==0:raise ValueError('old owner absent')
 if occupancy and capacity==0:raise ValueError('owned zero-capacity resource')
 other=occupancy-int(old_owner)
 return base*(1+accumulated_overuse)*(1+max(0,other-capacity+1))+static_price
