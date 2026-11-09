"""Prefix-preserving terminal candidates and exact capacitated matching.

These are proposals only: no model mutation or objective admission occurs here.
"""
from collections import Counter,deque
from bisect import bisect_right

def match(rows,capacities):
 rows={r:tuple(sorted(set(ps))) for r,ps in rows.items()}
 assert all(type(r) is int for r in rows)
 assert all(type(p) is int and type(c) is int and c>=0 for p,c in capacities.items())
 assert all(p in capacities for ps in rows.values() for p in ps)
 assigned={};users={p:[] for p in capacities}
 def augment(r,seen):
  for p in rows[r]:
   if p in seen:continue
   seen.add(p)
   if len(users[p])<capacities[p]:
    users[p].append(r);assigned[r]=p;return True
   for other in tuple(users[p]):
    if augment(other,seen):
     users[p].remove(other);users[p].append(r);assigned[r]=p;return True
  return False
 for r in sorted(rows):augment(r,set())
 assert len(assigned)==sum(map(len,users.values()))
 assert all(p in rows[r] for r,p in assigned.items())
 assert all(len(rs)<=capacities[p] for p,rs in users.items())
 missing=set(rows)-set(assigned);reachable=set(missing);pins=set();queue=deque(sorted(missing))
 while queue:
  r=queue.popleft()
  for p in rows[r]:
   if p in pins:continue
   pins.add(p)
   for other in users[p]:
    if other not in reachable:reachable.add(other);queue.append(other)
 deficit=len(reachable)-sum(capacities[p] for p in pins)
 if missing:assert deficit==len(missing)>0
 else:assert deficit==0
 return dict(feasible=not missing,matching=assigned,matched=len(assigned),
             hall_rows=sorted(reachable),hall_resources=sorted(pins),
             hall_capacity=sum(capacities[p] for p in pins),hall_deficit=deficit)

def terminal_index(fields,kinds):
 """Only IPINs whose outgoing edges all end in one terminal SINK are eligible."""
 info={};pools={}
 offsets=fields['row_offsets'];dest=fields['dest_ranks']
 for pin,kind in enumerate(kinds):
  if kind!='IPIN':continue
  slots=tuple(range(offsets[pin],offsets[pin+1]));sinks={dest[s] for s in slots}
  if len(sinks)!=1:continue
  sink=next(iter(sinks))
  if kinds[sink]!='SINK' or offsets[sink]!=offsets[sink+1]:continue
  info[pin]=(sink,slots);pools.setdefault(sink,[]).append(pin)
 return info,pools

def probe(sink,records,ledger,fields,kinds,rc,edge_slots,info,pools):
 """All records targeting this class participate; unsupported classes stay unchanged."""
 base=dict(sink_RR=sink,connection_ids=sorted(r['connection_id'] for r in records),
           NETs=sorted({r['net_id'] for r in records}),sink_capacity=fields['capacities'][sink])
 if len(base['NETs'])!=len(records):
  return dict(base,status='UNSUPPORTED_REPEATED_NET_IN_CLASS')
 pins=pools.get(sink,[])
 if not pins or any(fields['capacities'][p]!=1 for p in pins):
  return dict(base,status='UNSUPPORTED_NONUNIT_OR_MISSING_IPIN_POOL')
 if len(records)>fields['capacities'][sink]:
  return dict(base,status='SINK_DEMAND_EXCEEDS_CAPACITY')
 old_pins={};upstream={};old_tail={}
 for r in records:
  edges=r['answer']['physical_edge_ids'];cid=r['connection_id']
  if len(edges)<2 or edges[-1] not in edge_slots or edges[-2] not in edge_slots:
   return dict(base,status='UNSUPPORTED_TERMINAL_PATH')
  before,last=edge_slots[edges[-2]],edge_slots[edges[-1]]
  pin=fields['dest_ranks'][before];source=bisect_right(fields['row_offsets'],before)-1
  if pin not in info or info[pin][0]!=sink or last not in info[pin][1] or fields['dest_ranks'][last]!=r['sink'] or r['sink']!=sink:
   return dict(base,status='UNSUPPORTED_TERMINAL_PATH')
  old_pins[cid]=pin;upstream[cid]=source;old_tail[cid]=(before,last)
 counts=Counter(old_pins.values());background={p:ledger.get(p,0)-counts[p] for p in pins}
 assert all(x>=0 for x in background.values())
 available={p:max(0,fields['capacities'][p]-background[p]) for p in pins}
 candidates={};byid={r['connection_id']:r for r in records}
 for cid,r in sorted(byid.items()):
  old_a,old_b=old_tail[cid];u=upstream[cid];choices={}
  for a in range(fields['row_offsets'][u],fields['row_offsets'][u+1]):
   pin=fields['dest_ranks'][a]
   if pin not in available or not available[pin]:continue
   for b in info[pin][1]:
    delay=r['answer']['delay']-rc.increment(old_a)-rc.increment(old_b)+rc.increment(a)+rc.increment(b)
    if delay>r['budget_integer']:continue
    item=dict(IPIN=pin,delay=delay,terminal_edges=[fields['edge_ids'][a],fields['edge_ids'][b]])
    if pin not in choices or (delay,item['terminal_edges'])<(choices[pin]['delay'],choices[pin]['terminal_edges']):choices[pin]=item
  candidates[cid]=choices
 result=match({cid:choices.keys() for cid,choices in candidates.items()},available)
 assignments=[]
 if result['feasible']:
  for cid,pin in sorted(result['matching'].items()):
   r=byid[cid];candidate=candidates[cid][pin];path=list(r['answer']['physical_edge_ids'][:-2])+candidate['terminal_edges']
   assert rc.path(r['source'],r['sink'],path)==candidate['delay']<=r['budget_integer']
   assignments.append(dict(connection_id=cid,net_id=r['net_id'],source=r['source'],sink=r['sink'],
                           old_IPIN=old_pins[cid],new_IPIN=pin,upstream_RR=upstream[cid],
                           budget_integer=r['budget_integer'],old_delay=r['answer']['delay'],
                           candidate_delay=candidate['delay'],physical_edge_ids=path))
 return dict(base,status='FEASIBLE_PREFIX_BUDGET_PROPOSAL' if result['feasible'] else 'HALL_DEFICIENT_PREFIX_BUDGET_GRAPH',
             candidate_edges=sum(map(len,candidates.values())),available_IPIN_capacity=available,
             matching=result,assignments=assignments,channel_paths_unchanged_by_construction=True,
             input_state_mutated=False,objective_admission_pending=True)
