"""Deterministic scalar additive-delay tree growth; no native route inputs."""
import heapq,time,copy
from types import MappingProxyType
class EdgeSlotContext:
 def __init__(self,fields):
  ids=fields['edge_ids']
  if type(ids) is not tuple:raise ValueError('immutable edge identity tuple required')
  slots={eid:s for s,eid in enumerate(ids)}
  if len(slots)!=len(ids):raise ValueError('duplicate physical edge identities')
  self._ids=ids;self._slots=MappingProxyType(slots)
 def slots(self,fields):
  if fields['edge_ids'] is not self._ids:raise ValueError('edge snapshot replaced')
  return self._slots
from tree_pareto_search_constraints_v3 import search
from collections import Counter,defaultdict

def grouped_floor(fields,rc,source,sinks):
 remaining=set(sinks);dist={source:rc.initial(source)};queue=[(dist[source],source)];answer={}
 while queue and remaining:
  d,u=heapq.heappop(queue)
  if d!=dist[u]:continue
  if u in remaining:answer[u]=d;remaining.remove(u)
  for slot in range(fields['row_offsets'][u],fields['row_offsets'][u+1]):
   v=fields['dest_ranks'][slot]
   if fields['capacities'][v]<=0:continue
   nd=d+rc.increments[slot]
   if v not in dist or nd<dist[v]:dist[v]=nd;heapq.heappush(queue,(nd,v))
 return answer

def _import_seed(fields,rc,seed_records,slot_by_eid):
 offsets=fields['row_offsets'];dst=fields['dest_ranks'];caps=fields['capacities'];owners=defaultdict(set);parents=defaultdict(dict);prefix=defaultdict(dict);ledger=Counter();records=[]
 seen_cids=set()
 for record in seed_records:
  rec={**record,'answer':dict(record['answer'],physical_edge_ids=list(record['answer']['physical_edge_ids']))}
  net,src,sink=rec['net_id'],rec['source'],rec['sink'];assert rec['connection_id'] not in seen_cids;seen_cids.add(rec['connection_id']);u=src;delay=rc.initial(src);prefix[net][src]=delay;owners[net].add(src)
  for eid in rec['answer']['physical_edge_ids']:
   slot=slot_by_eid[eid];assert offsets[u]<=slot<offsets[u+1];v=dst[slot];parent=(u,eid);assert v not in parents[net] or parents[net][v]==parent;parents[net][v]=parent;delay+=rc.increments[slot]
   assert v not in prefix[net] or prefix[net][v]==delay
   prefix[net][v]=delay;owners[net].add(v);u=v
  assert u==sink and rc.path(src,sink,rec['answer']['physical_edge_ids'])==rec['answer']['delay']==delay<=rec['budget_integer'];records.append(rec)
 ledger.update(n for own in owners.values() for n in own);assert all(count<=caps[n] for n,count in ledger.items())
 return owners,parents,prefix,ledger,records,seen_cids

class SeedContext:
 def __init__(self,fields,rc,records,edge_context=None):
  if not isinstance(fields,MappingProxyType) or any(type(v) is not tuple for v in fields.values()):raise ValueError('immutable graph snapshot required')
  attrs=tuple(getattr(rc,k) for k in ('increments','initials','arcs','scale'))
  if any(type(v) is not tuple for v in attrs[:3]):raise ValueError('immutable RC snapshot required')
  self._fields=fields;self._rc=rc;self._attrs=attrs
  ids=[r['connection_id'] for r in records]
  if len(ids)!=len(set(ids)):raise ValueError('duplicate seed identities')
  context=EdgeSlotContext(fields) if edge_context is None else edge_context
  self._state=_import_seed(fields,rc,copy.deepcopy(list(records)),context.slots(fields))
 def fork(self,fields,rc):
  if fields is not self._fields or rc is not self._rc or any(getattr(rc,k) is not v for k,v in zip(('increments','initials','arcs','scale'),self._attrs)):raise ValueError('seed model snapshot replaced')
  return copy.deepcopy(self._state)

def predict(fields,rc,queries,floors,tree=True,floor_budget=True,seed_records=(),deadline=None,spans=None,penalty=0,max_labels=10000,remaining_delays=None,remaining_cache=None,forbidden_by_net=None,edge_context=None,seed_context=None):
 if seed_context is not None:
  if seed_records:raise ValueError('cannot mix prepared and explicit seed')
  prepared=seed_context.fork(fields,rc);seed_records=prepared[4]
 if spans is None:raise ValueError('graph spans required')
 offsets=fields['row_offsets'];dst=fields['dest_ranks'];caps=fields['capacities'];eids=fields['edge_ids'];owners=defaultdict(set);parents=defaultdict(dict);prefix=defaultdict(dict);ledger=Counter();records=[];failure=None;expanded=0
 seed_ids={r['connection_id'] for r in seed_records};query_ids=[q['connection_id'] for q in queries]
 if len(seed_ids)!=len(seed_records) or len(set(query_ids))!=len(query_ids) or seed_ids.intersection(query_ids):raise ValueError('duplicate connection identities')
 # Import only immutable caller records into a new local ownership state.
 slot_by_eid={eid:s for s,eid in enumerate(eids)} if edge_context is None else edge_context.slots(fields)
 if seed_context is None:owners,parents,prefix,ledger,records,seen_cids=_import_seed(fields,rc,seed_records,slot_by_eid)
 else:owners,parents,prefix,ledger,records,seen_cids=prepared
 for q in queries:
  if q['connection_id'] in seen_cids:raise ValueError('query already retained')

  if deadline is not None and time.perf_counter()>deadline:failure=dict(query=q,status='DEADLINE');break
  net,src,sink=q['net_id'],q['source'],q['sink'];own=owners[net];par=parents[net];pd=prefix[net]
  if own and src not in pd:raise ValueError('multiple sources in one NET')
  floor=floors.get((src,sink));budget=max(rc.scale//10**9,(3*floor+1)//2) if floor_budget and floor is not None else rc.scale//10**9
  allowed=lambda n:ledger.get(n,0)-int(n in own)<caps[n]
  if not allowed(src):failure=dict(query=q,status='SOURCE_CAPACITY');break
  initial={n:d for n,d in pd.items() if d<=budget} if tree and own else {src:rc.initial(src)}
  try:remaining=remaining_cache.get(sink,deadline) if remaining_cache is not None else None if remaining_delays is None else remaining_delays[sink]
  except TimeoutError:failure=dict(query=q,status='DEADLINE');break
  answer=search(fields,rc,src,sink,initial,own,ledger,budget,spans,penalty,max_labels,deadline,remaining_delay=remaining,forbidden_nodes=frozenset() if forbidden_by_net is None else forbidden_by_net.get(net,frozenset()));expanded+=answer['expanded']
  if answer['status']!='FOUND':failure=dict(query=q,status=answer['status'],floor_integer=floor,budget_integer=budget,labels_created=answer['labels_created']);break
  join=answer['join'];path=[];node=join;seen={node}
  while node!=src:
   u,eid=par[node];assert u not in seen;seen.add(u);path.append(eid);node=u
  path.reverse();branch=[];u=join
  for eid in answer['physical_edge_ids']:
   slot=slot_by_eid[eid];assert offsets[u]<=slot<offsets[u+1];v=dst[slot];branch.append((u,v,eid,slot));u=v
  path.extend(answer['physical_edge_ids']);delay=answer['delay']
  incoming={v:(u,eid) for u,v,eid,slot in branch};conflicts=[v for v,p in incoming.items() if v in par and par[v]!=p]
  if conflicts:failure=dict(query=q,status='MULTI_PARENT_REJECTED',nodes=conflicts);break
  assert rc.path(src,sink,path)==delay<=budget
  used={src,join}|{v for u,v,eid,slot in branch};assert all(allowed(n) for n in used)
  # Prefix state includes every retained node, including older paths not used here.
  if not own:pd[src]=rc.initial(src)
  for u,v,eid,slot in branch:pd[v]=pd[u]+rc.increments[slot]
  par.update(incoming);ledger.update(used-own);own.update(used)
  records.append(dict(q,answer=dict(status='FOUND',physical_edge_ids=path,delay=delay),budget_integer=budget,floor_integer=floor))
 return dict(status='COMPLETE_DIAGNOSTIC' if failure is None else 'INCOMPLETE_NOT_PUBLISHABLE',records=sorted(records,key=lambda r:r['connection_id']),ledger=dict(ledger),completed_connections=len(records),required_connections=len(seed_records)+len(queries),failure=failure,expanded_nodes=expanded,tree=tree,floor_budget=floor_budget)
