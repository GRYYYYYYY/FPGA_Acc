"""Ordered tree reference with raw-minimum feasible attachment fallback.

A primary rejection leaves the tree unchanged. Raw-only Dijkstra finds the
minimum additive raw arrival among tree-compatible extensions. If its arrival
exceeds the budget there is no feasible extension of this fixed tree. This
does not backtrack earlier committed sinks or replace the old whole-NET joint
fallback; that remains required for a production integration.
"""
from fractions import Fraction
from criticality_shared_tree_reference_v1 import Tree as Primary

class Tree(Primary):
 def expand(self,target,criticality,congestion,raw_budget):
  congestion=tuple(congestion)
  owned=frozenset(self.arrival)
  primary=super().expand(target,criticality,congestion,raw_budget)
  if primary['committed'] or primary['status']=='UNREACHABLE':
   return dict(primary,used_raw_fallback=False)
  assert frozenset(self.arrival)==owned
  fallback=super().expand(target,Fraction(1),congestion,raw_budget)
  p,q=criticality.numerator,criticality.denominator
  if fallback['committed']:
   # Derive the actual new-node price from committed parent links, not the
   # raw-only Dijkstra's objective; independently checked by oracle tests.
   u=target;price=0
   while u not in owned:
    price+=congestion[u];u=self.parents[u][0]
   return dict(fallback,used_raw_fallback=True,status='COMMITTED_RAW_FALLBACK',objective_numerator=p*fallback['raw']+(q-p)*price,objective_denominator=q,primary_raw=primary['raw'])
  return dict(fallback,used_raw_fallback=True,status='NO_FEASIBLE_FIXED_TREE_EXTENSION',objective_numerator=p*fallback['raw'],objective_denominator=q,primary_raw=primary['raw'],scope='Raw-minimum lower bound only; objective_numerator excludes congestion on uncommitted alternative. Not whole-NET infeasibility.')
