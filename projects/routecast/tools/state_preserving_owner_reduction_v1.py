"""Delete surplus true owners, prioritizing removal of disruptive assignments.

Does not flip false variables, optimize globally, or guarantee fewer actors.
"""
def reduce_witness(active,cuts,ownership):
 active=set(map(tuple,active));eligible={(n,c['NET']) for c in cuts for n in c['nodes']}
 if not active<=eligible or len({n for n,net in active})!=len(active):raise ValueError('owner domain or capacity')
 incidence={p:[] for p in active};counts=[]
 for i,c in enumerate(cuts):
  support={(n,c['NET']) for n in c['nodes']}&active
  if not support:raise ValueError('uncovered cut')
  counts.append(len(support))
  for p in support:incidence[p].append(i)
 def priority(p):
  n,net=p;displaced=sum(n in ns for other,ns in ownership.items() if other!=net)
  missing=n not in ownership.get(net,set())
  return displaced,int(missing),n,net
 removed=[]
 for p in sorted(active,key=priority,reverse=True):
  if all(counts[i]>1 for i in incidence[p]):
   active.remove(p);removed.append(p)
   for i in incidence[p]:counts[i]-=1
 witnesses=[dict(node=n,NET=net,unique_owner_cut_indices=[i for i in incidence[(n,net)] if counts[i]==1]) for n,net in sorted(active)]
 assert all(w['unique_owner_cut_indices'] for w in witnesses)
 return dict(active=sorted(active),removed=removed,irreducibility_witnesses=witnesses,scope='Subset of one fixed SAT model; delete more disruptive surplus owners first. Inclusion minimal only, no global actor or cost optimum and no guaranteed improvement.')
