"""Frozen-initial per-pin NET primary; caller retains whole-NET fallback/gates."""
from fractions import Fraction

def route(graph,queries,old_records,criticalities,prices,edge_ids):
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
 for _,_,cid,q,value in sorted(ordered):
  result=tree.expand(q['sink'],value,prices,old[cid]['budget_integer']);results.append(dict(connection_id=cid,**result))
  if 'path_slots' in result:
   attempts[cid]=[edge_ids[s] for s in result['path_slots']]
   u=source
   for slot in result['path_slots']:
    v=tree.dest[slot]
    if v in parents and parents[v]!=(u,slot):raise RuntimeError('primary tree incompatibility')
    parents[v]=u,slot;u=v
   settled.add(q['sink'])
  else:attempts[cid]=None
  if not result['committed']:failure=cid;break
 return dict(complete=failure is None,first_failed_connection_id=failure,attempts=[dict(connection_id=q['connection_id'],physical_edge_ids=attempts.get(q['connection_id'])) for q in queries],search_results=results,parents=parents,settled=settled,order=[x[2] for x in sorted(ordered)],scope='Stops at first budget/unreachable failure; remaining pins unsearched, not proved unreachable. Must invoke whole-NET fallback and owner/overflow gates before feedback commit.')
