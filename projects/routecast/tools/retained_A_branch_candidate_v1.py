"""Keep constraint-unaffected input-A branches; attach affected paths atomically.

Uses the existing additive-RC seed validator. A proposal is not a raw minimum
certificate unless the upstream oracle separately supplies that certificate.
Hybrid rejection is never permission to prune: use the complete proposal.
"""
from types import SimpleNamespace
from retained_criticality_tree_seed_v1 import seed

def candidate(fields,increments,source,initial,connections,blocked,proposal_provider):
 n=len(fields['capacities']);blocked=frozenset(blocked);qs=sorted(connections,key=lambda q:q['connection_id'])
 if not 0<=source<n or source in blocked or fields['capacities'][source]<=0:raise ValueError('source')
 if len({q['connection_id'] for q in qs})!=len(qs) or not qs:raise ValueError('connections')
 def empty():return SimpleNamespace(n=n,source=source,initial={source:initial},arrival={source:initial},parents={},offsets=fields['row_offsets'],dest=fields['dest_ranks'],inc=increments)
 def walk(slots,target):
  u=source;nodes=[u]
  for e in slots:
   if type(e) is not int or not fields['row_offsets'][u]<=e<fields['row_offsets'][u+1]:raise ValueError('physical edge')
   u=fields['dest_ranks'][e]
   if fields['capacities'][u]<=0:raise ValueError('disabled physical node')
   nodes.append(u)
  if u!=target:raise ValueError('target')
  return nodes
 original=[];unaffected=[];affected=[]
 for q in qs:
  if q['source']!=source:raise ValueError('mixed source')
  nodes=walk(q['physical_edge_ids'],q['sink']);original.append((q['sink'],q['physical_edge_ids'],q['budget']))
  (affected if blocked.intersection(nodes) else unaffected).append(q)
 validation=empty();seed(validation,original)
 tree=empty();seed(tree,[(q['sink'],q['physical_edge_ids'],q['budget']) for q in unaffected])
 def finish(kind,provider=None):
  answers={}
  for q in qs:
   u=q['sink'];slots=[];seen={u}
   if u not in tree.arrival or tree.arrival[u]>q['budget']:raise ValueError('tree budget')
   while u!=source:
    parent,e=tree.parents[u]
    if parent in seen:raise ValueError('tree cycle')
    seen.add(parent);slots.append(e);u=parent
   slots.reverse()
   if q in unaffected and slots!=q['physical_edge_ids']:raise ValueError('retained path changed')
   answers[q['sink']]={'reachable':True,'raw_cost':tree.arrival[q['sink']],'slots':slots}
  result=dict(provider or {});result.update(kind=kind,within_budget=True,answers=answers,raw_certificate=None,pruning_allowed=False,retained_connection_ids=[q['connection_id'] for q in unaffected],affected_connection_ids=[q['connection_id'] for q in affected],retention_succeeded=True)
  result.setdefault('weighted_searches',0);result.setdefault('raw_searches',0);return result
 if not affected:return finish('A_UNCHANGED_PRIMAL')
 proposal=proposal_provider()
 if not proposal['within_budget']:
  if not proposal.get('pruning_allowed') or proposal.get('raw_certificate') is None:raise ValueError('missing independent raw prune certificate')
  return dict(proposal,retention_succeeded=False,retention_rejected_reason='raw infeasible',retained_connection_ids=[])
 proposed=empty();paths=[];nodes_by_sink={}
 for q in qs:
  a=proposal['answers'][q['sink']]
  if not a['reachable']:raise ValueError('proposal reachability')
  nodes=walk(a['slots'],q['sink'])
  if blocked.intersection(nodes):raise ValueError('proposal mask')
  paths.append((q['sink'],a['slots'],q['budget']));nodes_by_sink[q['sink']]=nodes
 seed(proposed,paths)
 for q in qs:
  if proposal['answers'][q['sink']]['raw_cost']!=proposed.arrival[q['sink']]:raise ValueError('proposal raw cost')
 for q in affected:
  a=proposal['answers'][q['sink']];nodes=nodes_by_sink[q['sink']];join=max(i for i,node in enumerate(nodes) if node in tree.arrival);suffix=a['slots'][join:];value=tree.arrival[nodes[join]]+sum(increments[e] for e in suffix)
  if value>q['budget']:
   return dict(proposal,retention_succeeded=False,retention_rejected_reason='existing-prefix budget',retained_connection_ids=[])
  u=nodes[join]
  for e in suffix:
   v=fields['dest_ranks'][e]
   if v in tree.arrival:raise ValueError('suffix unexpectedly joins existing tree')
   tree.parents[v]=(u,e);tree.arrival[v]=tree.arrival[u]+increments[e];u=v
 return finish('A_BRANCH_RETAINED_PRIMAL',proposal)
