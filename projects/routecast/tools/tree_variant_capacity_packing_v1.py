"""Exact bounded packing of complete NET node-union variants."""
import time
from collections import Counter

def pack_variants(capacities,base_counts,variants,max_nodes=100000,deadline=None):
 if max_nodes<1:raise ValueError('positive search node limit required')
 caps=tuple(capacities);base=Counter(base_counts)
 if any(n<0 or n>=len(caps) or c<0 or c>caps[n] for n,c in base.items()):raise ValueError('invalid fixed occupancy')
 options={}
 for net,choices in variants.items():
  options[net]=[]
  for choice in choices:
   nodes=frozenset(choice)
   if any(n<0 or n>=len(caps) for n in nodes):raise ValueError('invalid node identity')
   options[net].append((nodes,sum(1<<n for n in nodes if caps[n]==1),tuple(n for n in nodes if caps[n]!=1)))
 used=sum(1<<n for n,c in base.items() if c and caps[n]==1);counts=Counter(base);chosen={};visits=0;limit=None
 def search(remaining,unit_mask):
  nonlocal visits,limit
  if deadline is not None and time.perf_counter()>=deadline:limit='DEADLINE';return False
  if visits>=max_nodes:limit='SEARCH_NODE_LIMIT';return False
  visits+=1
  if not remaining:return True
  viable={net:[i for i,(_,mask,multi) in enumerate(options[net]) if not mask&unit_mask and all(counts[n]<caps[n] for n in multi)] for net in remaining};net=min(remaining,key=lambda n:(len(viable[n]),n))
  for index in viable[net]:
   nodes,mask,_=options[net][index];chosen[net]=index;counts.update(nodes)
   if search([n for n in remaining if n!=net],unit_mask|mask):return True
   counts.subtract(nodes);del chosen[net]
   if limit is not None:return False
  return False
 found=search(sorted(options),used)
 return dict(status='FOUND_POOL_BATCH' if found else limit or 'POOL_EXHAUSTED',search_nodes=visits,chosen_option_indices=dict(chosen) if found else None)
