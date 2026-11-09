"""Deterministic deletion of surplus SAT owners, never selecting another SAT model."""
def reduce_witness(active,cuts):
 active=set(map(tuple,active));eligible={(node,c['NET']) for c in cuts for node in c['nodes']}
 if not active<=eligible or len({node for node,net in active})!=len(active):raise ValueError('owner domain or unit capacity')
 def covers(assignment):return all(any((node,c['NET']) in assignment for node in c['nodes']) for c in cuts)
 if not covers(active):raise ValueError('cut not covered')
 original=set(active);removed=[]
 for pair in sorted(original,reverse=True):
  if covers(active-{pair}):active.remove(pair);removed.append(pair)
 witnesses=[]
 for node,net in sorted(active):
  critical=[i for i,c in enumerate(cuts) if c['NET']==net and {(n,net) for n in c['nodes']}&active=={(node,net)}];assert critical
  witnesses.append(dict(node=node,NET=net,unique_owner_cut_indices=critical))
 assert covers(active)
 return dict(active=sorted(active),removed=removed,irreducibility_witnesses=witnesses,scope='Inclusion minimal only, not minimum cardinality or minimum route cost. Each retained owner is the unique selected owner in at least one original necessary cut.')
