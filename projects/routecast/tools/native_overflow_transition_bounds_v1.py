"""Exact bounds on overflow-unit change with nonnegative unknown external occupancy."""
def bounds(total,delta,capacity,external=None,nonoverused=False):
 if any(type(x) is not int for x in (total,delta,capacity)) or total<0 or capacity<0 or total+delta<0:raise ValueError('occupancy domain')
 def change(x):return max(0,x+delta-capacity)-max(0,x-capacity)
 if external is not None:
  if type(external) is not int or external<0:raise ValueError('external occupancy')
  if nonoverused and total+external>capacity:raise ValueError('inconsistent observation')
  x=change(total+external);return x,x
 if nonoverused and total>capacity:raise ValueError('nonoverused lower bound')
 near=change(total);far=change(capacity) if nonoverused else delta
 return (near,far) if delta>=0 else (far,near)
