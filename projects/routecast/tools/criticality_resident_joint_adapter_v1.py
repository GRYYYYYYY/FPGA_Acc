"""Pure CSR/records adapter: preserve legacy candidate generation, re-score.

Legacy selection is executed unchanged. Its whole-tree answer is explicitly
considered even if the new candidate enumerator reaches its state cap. The
legacy acceptance flag is diagnostic and never authorizes new-objective commit.
No ledger/epoch or caller records are mutated.
"""
from fractions import Fraction
from resident_actual_old_fallback_undo_adapter_v2 import fallback as Legacy
from criticality_whole_net_choice_reference_v1 import choose,score
from budget_NET_gate_reference_v1 import audit

def fallback(fields,rc,slots,queries,old_records,parents,settled,prices,weight,node_base,criticalities,max_states=10000):
 if type(weight) is not int or weight<0 or len(node_base)!=len(fields['capacities']):raise ValueError('cost domain')
 if any(type(v) is not int or v<0 for v in node_base):raise ValueError('base cost')
 if type(max_states) is not int or max_states<1:raise ValueError('state cap')
 oldbyid={r['connection_id']:r for r in old_records}
 ids={q['connection_id'] for q in queries}
 if not queries or len(ids)!=len(queries) or len(oldbyid)!=len(old_records) or ids!=set(oldbyid):raise ValueError('connection set')
 source=queries[0]['source'];pins=[]
 for q in queries:
  cid=q['connection_id'];r=criticalities[cid]
  if r['source_rr']!=q['source'] or r['target_rr']!=q['sink']:raise ValueError('criticality endpoint identity')
  c=Fraction(r['criticality_numerator'],r['criticality_denominator'])
  if not 0<=c<=1:raise ValueError('criticality range')
  pins.append((q['sink'],c))
 legacy=Legacy(fields,rc,slots,queries,old_records,parents,settled,prices,weight,max_states)
 legacybyid={r['connection_id']:r for r in legacy['records']}
 adjacency={};caps={source:fields['capacities'][source]};budgets={};old_paths={};candidates={};congestion={}
 def add(path,sink):
  u=source
  for eid in path:
   slot=slots[eid]
   if fields['edge_ids'][slot]!=eid or not fields['row_offsets'][u]<=slot<fields['row_offsets'][u+1]:raise ValueError('physical edge identity')
   v=fields['dest_ranks'][slot];adjacency.setdefault(u,{})[eid]=(eid,v,rc.increment(slot),0);caps[v]=fields['capacities'][v]
   value=prices.get(v,0)
   if type(value) is not int or value<0:raise ValueError('price')
   cost=node_base[v]+weight*value
   if v in congestion and congestion[v]!=cost:raise ValueError('price snapshot changed')
   congestion[v]=cost;u=v
  if u!=sink:raise ValueError('path endpoint')
 for q in queries:
  r=oldbyid[q['connection_id']];s=q['sink'];oldpath=list(r['answer']['physical_edge_ids'])
  if q['source']!=source or any(r[k]!=v for k,v in q.items()):raise ValueError('query identity')
  if s in budgets and (budgets[s]!=r['budget_integer'] or old_paths[s]!=oldpath):raise ValueError('duplicate sink')
  budgets[s]=r['budget_integer'];old_paths[s]=oldpath;candidates.setdefault(s,[]);add(oldpath,s)
  legacy_path=list(legacybyid[q['connection_id']]['answer']['physical_edge_ids']);add(legacy_path,s);candidates[s].append(legacy_path)
  if s in settled:
   u=s;seen={u};path=[]
   while u!=source:
    prev,slot=parents[u]
    if not fields['row_offsets'][prev]<=slot<fields['row_offsets'][prev+1] or fields['dest_ranks'][slot]!=u:raise ValueError('attempt arc')
    path.append(fields['edge_ids'][slot]);u=prev
    if u in seen:raise ValueError('attempt cycle')
    seen.add(u)
   path.reverse();add(path,s);candidates[s].append(path)
 adj={u:list(v.values()) for u,v in adjacency.items()}
 answer=choose(adj,source,budgets,old_paths,candidates,pins,congestion,rc.initial(source),caps,max_states)
 # Keep the legacy whole-tree feasible answer eligible outside capped search.
 legacy_paths={q['sink']:legacybyid[q['connection_id']]['answer']['physical_edge_ids'] for q in queries}
 check=audit(adj,source,budgets,legacy_paths,rc.initial(source),caps);cost=score(adj,source,legacy_paths,pins,congestion,rc.initial(source))
 if cost<answer['chosen_score']:
  answer=dict(answer,paths=legacy_paths,audit=check,chosen_score=cost,status='ACCEPT_STRICT_IMPROVEMENT')
 records=[]
 for q in queries:
  r=oldbyid[q['connection_id']];path=list(answer['paths'][q['sink']]);raw=rc.path(source,q['sink'],path)
  if raw!=answer['audit']['delays'][q['sink']] or raw>r['budget_integer']:raise ValueError('chosen raw proof')
  records.append(dict(r,answer=dict(status='FOUND',physical_edge_ids=path,delay=raw)))
 return dict(records=records,status=answer['status'],old_score=answer['old_score'],chosen_score=answer['chosen_score'],states=answer['states'],search_status=answer['search_status'],legacy_status=legacy['status'],legacy_states=legacy['states'])
