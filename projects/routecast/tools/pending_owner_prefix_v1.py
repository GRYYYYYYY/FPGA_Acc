"""Input-only ordered pending window and whole-owner witness union selection."""
import time
from collections import Counter,defaultdict
from owner_joint_repair_v1 import constrained_witness

def select(f,rc,before,pending,max_owner_nets=4,max_queries=16,deadline=None):
 if any(type(v) is not int or v<1 for v in (max_owner_nets,max_queries)):raise ValueError('positive lookahead limits required')
 old={r['connection_id'] for r in before};ids=[q['connection_id'] for q in pending]
 if len(old)!=len(before) or len(ids)!=len(set(ids)) or old.intersection(ids):raise ValueError('pending scope overlaps or duplicates accepted identities')
 ordered=sorted(pending,key=lambda q:(q['net_id'],q['connection_id']));slots={e:s for s,e in enumerate(f['edge_ids'])};owners=defaultdict(set)
 for r in before:owners[r['net_id']].add(r['source']);owners[r['net_id']].update(f['dest_ranks'][slots[e]] for e in r['answer']['physical_edge_ids'])
 release=set();selected=[];evidence=[];stop='WINDOW_LIMIT' if len(ordered)>max_queries else 'ALL_PENDING_SELECTED'
 for q in ordered[:max_queries]:
  if deadline is not None and time.perf_counter()>=deadline:stop='DEADLINE';break
  try:witness=constrained_witness(f,rc,q,frozenset(),deadline)
  except TimeoutError:stop='DEADLINE';break
  if witness is None:stop='INPUT_UNREACHABLE';break
  other=Counter(n for net,own in owners.items() if net!=q['net_id'] for n in own);used={q['source']}|{f['dest_ranks'][slots[e]] for e in witness['physical_edge_ids']};blocked=sorted(n for n in used if other[n]>=f['capacities'][n]);blocking=sorted(net for net,own in owners.items() if net!=q['net_id'] and own.intersection(blocked));proposed=release|set(blocking);fits=len(proposed)<=max_owner_nets;evidence.append(dict(query=q,witness=witness,blocked_nodes=blocked,blocking_net_ids=blocking,cumulative_release=sorted(proposed),selected=fits))
  if not fits:stop='OWNER_LIMIT';break
  release=proposed;selected.append(q)
 removed=[r['connection_id'] for r in before if r['net_id'] in release]
 return dict(queries=selected,requested_connection_ids=[q['connection_id'] for q in selected],released_net_ids=sorted(release),removed_connection_ids=removed,witness_evidence=evidence,stop=stop,remaining_pending_ids=[q['connection_id'] for q in ordered if q['connection_id'] not in {s['connection_id'] for s in selected}],scope='Max ordered input-witness prefix, not globally optimal release selection or complete routing; whole accepted NET removal.')
