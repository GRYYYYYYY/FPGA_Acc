"""Exact local-parent ensemble expectation on bounded predecessor supports."""
import itertools,math
from collections import Counter
from fractions import Fraction
from shortest_NET_tree_ensemble_v1 import materialize

def expectation(prepared,*,assignment_limit):
 keys=list(prepared['choices']);total=math.prod(len(prepared['choices'][v]) for v in keys)
 if type(assignment_limit) is not int or assignment_limit<1:raise ValueError('invalid assignment limit')
 if total>assignment_limit:raise ValueError('parent assignment limit exceeded; no truncated expectation emitted')
 occupied=Counter();per_sink={s:Counter() for s in prepared['sinks']};unions=Counter()
 for choices in itertools.product(*(prepared['choices'][v] for v in keys)):
  selected=dict(zip(keys,choices));tree=materialize(prepared,selected);occupied.update(tree['nodes']);unions[tuple(sorted(tree['nodes']))]+=1
  for sink in prepared['sinks']:
   visited={prepared['source']};u=sink
   while u!=prepared['source']:visited.add(u);u=selected[u][0]
   per_sink[sink].update(visited)
 exact={v:Fraction(occupied[v],total) for v in prepared['distance']}
 independent={}
 for v in exact:
  absent=Fraction(1)
  for s in per_sink:absent*=1-Fraction(per_sink[s][v],total)
  independent[v]=1-absent
 return dict(parent_assignments=total,node_probabilities=exact,independent_sink_union=independent,node_union_counts=dict(unions))
