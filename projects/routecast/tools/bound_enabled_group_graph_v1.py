"""One-time exact raw-CSR binding; immutable search graph with owned initial values."""
from dataclasses import dataclass
@dataclass(frozen=True)
class BoundGraph:
 n:int
 offsets:tuple
 dest:tuple
 inc:tuple
 initial:tuple
 repair_bounds:object

def bind(original,bounds):
 offsets=tuple(original.offsets);dest=tuple(original.dest);raw=tuple(original.inc);initial=tuple(original.initial)
 if original.n!=bounds.n or offsets!=bounds.offsets or dest!=bounds.dest or raw!=bounds.raw:raise ValueError('bound raw-CSR context mismatch')
 if len(initial)!=original.n or any(type(v) is not int or v<0 for v in initial):raise ValueError('initial arrival domain')
 return BoundGraph(original.n,offsets,dest,raw,initial,bounds)
