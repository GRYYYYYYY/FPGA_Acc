"""Pure unique-NET occupancy replacement plan; no shared-state mutation.

Physical/identity/raw-budget/tree admission must precede this gate. Existing
old ownership is virtually released once, then new ownership acquired once.
Positive prospective fullgraph overflow delta retains the entire old NET.
"""
def plan(capacities,ledger,old_owned,new_owned):
 old=frozenset(old_owned);new=frozenset(new_owned);n=len(capacities)
 if not old or not new:raise ValueError('empty ownership')
 if any(type(u) is not int or not 0<=u<n for u in old|new):raise ValueError('owner node domain')
 updates={};delta=0
 for u in sorted(old|new):
  capacity=capacities[u];count=ledger.get(u,0)
  if type(capacity) is not int or capacity<=0 or type(count) is not int or count<0:raise ValueError('capacity/count')
  if u in old and count<1:raise ValueError('old owner absent')
  after=count-(u in old)+(u in new)
  if after<0:raise ValueError('negative prospective count')
  delta+=max(0,after-capacity)-max(0,count-capacity)
  if after!=count:updates[u]=after
 return dict(status='RETAIN_OVERFLOW_INCREASE' if delta>0 else 'ADMIT_OCCUPANCY_REPLACEMENT',prospective_overflow_delta=delta,updates={} if delta>0 else updates,rejected_updates=updates if delta>0 else {},old_owned=old,new_owned=new,scope='Occupancy only; preceding full physical/budget/singleparent checks remain required.')
