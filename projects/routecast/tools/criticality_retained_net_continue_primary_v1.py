"""Continue after rejected primary expansion; only committed branches enter shared tree."""
from fractions import Fraction
from retained_criticality_tree_seed_v1 import seed

def route(graph,queries,old_records,criticalities,prices,edge_ids,ledger,capacities,edge_slots,min_fanout=16):
 if not queries:raise ValueError('empty NET')
 source=queries[0]['source'];net=queries[0]['net_id'];old={r['connection_id']:r for r in old_records}
 ids={q['connection_id'] for q in queries}
 if len(ids)!=len(queries) or len(old)!=len(old_records) or ids!=set(old):raise ValueError('connection set')
 ordered=[];sink_contract={}
 for q in queries:
  cid=q['connection_id'];r=old[cid];c=criticalities[cid]
  if any(r[k]!=v for k,v in q.items()) or q['source']!=source or q['net_id']!=net:raise ValueError('NET identity')
  if (c['net'],c['source_rr'],c['target_rr'])!=(net,source,q['sink']):raise ValueError('criticality identity')
  value=Fraction(c['criticality_numerator'],c['criticality_denominator'])
  if not 0<=value<=1 or type(r['budget_integer']) is not int or r['budget_integer']<0:raise ValueError('cost/budget')
  s=q['sink'];contract=(r['budget_integer'],tuple(r['answer']['physical_edge_ids']))
  if s in sink_contract and sink_contract[s]!=contract:raise ValueError('duplicate sink contract')
  sink_contract[s]=contract;ordered.append((-value,c['local_sink_pin'],cid,q,value))
 tree=graph.tree(source);attempts={};results=[];failure=None;parents={};settled=set()
 if type(min_fanout) is not int or min_fanout<1:raise ValueError('fanout threshold')
 slots=edge_slots
 retained=[];retained_slots={}
 if len(queries)>=min_fanout:
  for q in queries:
   cid=q['connection_id'];r=old[cid];u=source;nodes={u};path=[]
   for eid in r['answer']['physical_edge_ids']:
    slot=slots[eid]
    if not tree.offsets[u]<=slot<tree.offsets[u+1]:raise ValueError('old path source')
    u=tree.dest[slot]
    if u in nodes:raise ValueError('old cyclic path')
    nodes.add(u);path.append(slot)
   if u!=q['sink']:raise ValueError('old path endpoint')
   if all(ledger.get(n,0)<=capacities[n] for n in nodes):
    retained.append((q['sink'],path,r['budget_integer']));retained_slots[cid]=path
 seed(tree,retained);parents.update(tree.parents)
 for q in queries:
  cid=q['connection_id']
  if cid in retained_slots:
   settled.add(q['sink']);attempts[cid]=list(old[cid]['answer']['physical_edge_ids'])
   results.append(dict(connection_id=cid,status='RETAINED_CLEAN_BRANCH',committed=True,raw=tree.arrival[q['sink']],path_slots=tuple(retained_slots[cid])))
 rejected=[]
 for _,_,cid,q,value in sorted(ordered):
  if cid in retained_slots:continue
  result=tree.expand(q['sink'],value,prices,old[cid]['budget_integer']);results.append(dict(connection_id=cid,**result))
  if not result['committed']:
   if failure is None:failure=cid
   rejected.append(dict(connection_id=cid,status=result['status'],raw=result.get('raw'),
    physical_edge_ids=[edge_ids[s] for s in result['path_slots']] if 'path_slots' in result else None))
   attempts[cid]=None
   continue
  if 'path_slots' not in result:raise RuntimeError('Committed expansion without physical path')
  attempts[cid]=[edge_ids[s] for s in result['path_slots']]
  u=source
  for slot in result['path_slots']:
   v=tree.dest[slot]
   if v in parents and parents[v]!=(u,slot):raise RuntimeError('primary tree incompatibility')
   parents[v]=u,slot;u=v
  settled.add(q['sink'])
 return dict(retained_connection_ids=sorted(retained_slots),search_calls=len(results)-len(retained_slots),
  complete=all(q['sink'] in settled and tree.arrival[q['sink']]<=old[q['connection_id']]['budget_integer'] for q in queries),
  first_failed_connection_id=failure,rejected_expansions=rejected,
  attempts=[dict(connection_id=q['connection_id'],physical_edge_ids=attempts.get(q['connection_id'])) for q in queries],
  search_results=results,parents=parents,settled=settled,order=[x[2] for x in sorted(ordered)],
  scope='Search every nonretained pin in original order after rejection. Only committed expansions enter tree/parents/settled; rejected physical paths are separate witnesses, never seeds or legal fallback candidates. Whole-NET fallback and guards remain required.')
