"""Pure full-record tree/raw-budget admission followed by occupancy gate."""
from criticality_net_occupancy_gate_v1 import plan

def validate(fields,rc,slots,queries,records):
 byid={r['connection_id']:r for r in records};ids={q['connection_id'] for q in queries}
 if not queries or len(ids)!=len(queries) or len(byid)!=len(records) or set(byid)!=ids:raise ValueError('query set')
 source=queries[0]['source'];net=queries[0]['net_id'];owned={source};parents={};delays={}
 if type(source) is not int or not 0<=source<len(fields['capacities']) or fields['capacities'][source]<=0:raise ValueError('source')
 for q in queries:
  r=byid[q['connection_id']]
  if q['source']!=source or q['net_id']!=net or any(r[k]!=v for k,v in q.items()):raise ValueError('query identity')
  if r['answer']['status']!='FOUND' or type(r['budget_integer']) is not int or r['budget_integer']<0:raise ValueError('answer/budget')
  u=source;raw=rc.initial(source);seen={u}
  for eid in r['answer']['physical_edge_ids']:
   if type(eid) is not int or eid not in slots:raise ValueError('edge identity')
   slot=slots[eid]
   if fields['edge_ids'][slot]!=eid or not fields['row_offsets'][u]<=slot<fields['row_offsets'][u+1]:raise ValueError('edge source')
   v=fields['dest_ranks'][slot]
   if v in seen or fields['capacities'][v]<=0:raise ValueError('cycle/capacity')
   incoming=(u,eid)
   if v in parents and parents[v]!=incoming:raise ValueError('multiple parents')
   parents[v]=incoming;seen.add(v);owned.add(v);increment=rc.increment(slot)
   if type(increment) is not int or increment<0:raise ValueError('raw increment')
   raw+=increment;u=v
  if u!=q['sink'] or raw!=r['answer']['delay'] or raw>r['budget_integer']:raise ValueError('endpoint/raw/budget')
  delays[q['connection_id']]=raw
 return dict(owned=frozenset(owned),parents=parents,delays=delays)

def prepare(fields,rc,slots,queries,old_records,candidate_records,ledger):
 old=validate(fields,rc,slots,queries,old_records);new=validate(fields,rc,slots,queries,candidate_records)
 oldbyid={r['connection_id']:r for r in old_records}
 for r in candidate_records:
  original=oldbyid[r['connection_id']]
  if {k:v for k,v in r.items() if k!='answer'}!={k:v for k,v in original.items() if k!='answer'}:raise ValueError('frozen record metadata changed')
 return dict(plan(fields['capacities'],ledger,old['owned'],new['owned']),old_audit=old,candidate_audit=new)
