"""Deterministic injective matching over explicit physical-pin candidates.

Each request needs a distinct (class,ptc). Caller must establish reachability
and packed-pin equivalence. No partial assignment is returned on failure.
"""
from collections import deque


def assign(candidates):
    adj={}
    for request,pins in candidates.items():
        if type(request) is not int or request<0:raise ValueError('invalid request ID')
        values=list(pins)
        if any(type(p) is not tuple or len(p)!=2 or any(type(n) is not int or n<0 for n in p) for p in values):raise ValueError('invalid physical pin')
        if len(set(values))!=len(values):raise ValueError('duplicate candidate pin')
        adj[request]=tuple(sorted(values))
    left={};right={}
    for start in sorted(adj):
        queue=deque([start]);seen_left={start};seen_right=set();parent={};free=None
        while queue and free is None:
            request=queue.popleft()
            for pin in adj[request]:
                if pin in seen_right:continue
                seen_right.add(pin);parent[pin]=request
                if pin not in right:free=pin;break
                other=right[pin]
                if other not in seen_left:seen_left.add(other);queue.append(other)
        if free is None:
            neighbors={pin for r in seen_left for pin in adj[r]}
            if neighbors!=seen_right or len(neighbors)>=len(seen_left):raise AssertionError('invalid Hall witness')
            return {'status':'infeasible','assignment':{},'hall_witness':{'request_ids':sorted(seen_left),'physical_pins':[list(p) for p in sorted(neighbors)],'deficiency':len(seen_left)-len(neighbors)},'scope':'infeasible only for supplied candidates; not all RR routing options'}
        pin=free
        while True:
            request=parent[pin];old=left.get(request);left[request]=pin;right[pin]=request
            if old is None:break
            pin=old
    return {'status':'matched','assignment':{r:list(left[r]) for r in sorted(left)},'hall_witness':None,'scope':'injective physical pin assignment only; no channel/route-tree/timing legality'}
