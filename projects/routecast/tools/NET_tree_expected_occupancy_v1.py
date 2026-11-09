"""Input-only exact single-sink marginals and fixed bounded multi-sink policy."""
from collections import Counter
from fractions import Fraction
import math
from exact_NET_tree_expectation_v1 import expectation
from shortest_NET_tree_ensemble_v1 import sample
EXACT_ASSIGNMENT_LIMIT=4096
SAMPLES=16
SEED=19

def single_sink(prepared):
 if len(prepared['sinks'])!=1:raise ValueError('requires one distinct sink')
 probability=Counter({prepared['sinks'][0]:Fraction(1)})
 for v in sorted(prepared['distance'],key=lambda n:(-prepared['distance'][n][1],n)):
  if v==prepared['source']:continue
  incoming=probability[v]
  if not incoming:continue
  choices=prepared['choices'][v];share=incoming/len(choices)
  for u,_ in choices:probability[u]+=share
 assert probability[prepared['source']]==1 and all(0<=x<=1 for x in probability.values())
 return {n:probability[n] for n in prepared['distance'] if probability[n]}

def predict(prepared,*,net_id):
 if len(prepared['sinks'])==1:return dict(mode='exact_single_sink',probabilities=single_sink(prepared),samples=0)
 assignments=math.prod(map(len,prepared['choices'].values()))
 if assignments<=EXACT_ASSIGNMENT_LIMIT:
  exact=expectation(prepared,assignment_limit=EXACT_ASSIGNMENT_LIMIT)
  return dict(mode='exact_multi_sink_local_parents',probabilities={n:x for n,x in exact['node_probabilities'].items() if x},samples=0)
 counts=Counter()
 for i in range(SAMPLES):counts.update(sample(prepared,seed=SEED,net_id=net_id,sample_index=i)['nodes'])
 return dict(mode='sampled_shared_parent_multi_sink',probabilities={n:Fraction(x,SAMPLES) for n,x in counts.items()},samples=SAMPLES)
