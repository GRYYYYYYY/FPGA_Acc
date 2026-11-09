"""Native-channel reuse initialization with atomic caller-supplied audited warm fallback.
Caller supplies frozen matched budgets and a lazy capacity-positive fallback.
For each changed CID, minimize newly added non-native CHANNEL count before raw delay, under current frozen tree. penalty=raw simple-path envelope+1, not fitted. Pareto labels enforce original raw budget inside search; fixed10000 created-label limit returns UNKNOWN and audited wholeNET fallback. Optimality is only per expansion for the frozen tree when search finishes, never global wholeNET optimality. Cross-NET overuse remains forecast demand.
"""
from retained_criticality_tree_seed_v1 import seed
from budget_constrained_native_reuse_expand_v1 import expand,LABEL_LIMIT

class Rejected(ValueError):pass

def initialize(graph,fields,kinds,queries,old_records,budgets,edge_slots,fallback):
 if not queries:raise ValueError('empty NET')
 source=queries[0]['source'];net=queries[0]['net_id'];qs={q['connection_id']:q for q in queries};old={r['connection_id']:r for r in old_records}
 if len(qs)!=len(queries) or len(old)!=len(old_records) or set(qs)!=set(old) or len({q['sink'] for q in queries})!=len(queries):raise ValueError('NET connection domain')
 if len(kinds)!=graph.n or len(fields['capacities'])!=graph.n:raise ValueError('node domain')
 for cid,q in qs.items():
  if q['source']!=source or q['net_id']!=net or old[cid]['net_id']!=net:raise ValueError('NET identity')
  if type(budgets[cid]) is not int or not 0<=budgets[cid]<2**128:raise ValueError('budget domain')
  if any(type(q[k]) is not int or not 0<=q[k]<graph.n for k in ['source','sink']):raise ValueError('endpoint domain')
  if kinds[q['source']]!='SOURCE' or kinds[q['sink']]!='SINK':raise ValueError('terminal types')
 def validate(answers,subset):
  if set(answers)!=set(subset):raise Rejected('incomplete NET')
  parents={};owned=set()
  for cid in subset:
   q=qs[cid];a=answers[cid];u=source;visited={u};value=graph.initial[u]
   if fields['capacities'][u]<=0:raise Rejected('disabled source')
   edges=a['physical_edge_ids']
   for index,eid in enumerate(edges):
    if type(eid) is not int or eid<0:raise Rejected('edge ID')
    try:slot=edge_slots[eid]
    except (KeyError,IndexError):raise Rejected('absent edge')
    if type(slot) is not int or not 0<=slot<len(graph.inc) or fields['edge_ids'][slot]!=eid or not graph.offsets[u]<=slot<graph.offsets[u+1]:raise Rejected('arc source')
    v=graph.dest[slot]
    if v in visited or fields['capacities'][v]<=0:raise Rejected('cycle or disabled resource')
    if index<len(edges)-1 and kinds[v] in ('SOURCE','SINK'):raise Rejected('interior terminal')
    if kinds[v]!='SINK':
     if v in parents and parents[v]!=(u,slot):raise Rejected('parent conflict')
     parents[v]=(u,slot)
    visited.add(v);value+=graph.inc[slot];u=v
   if u!=q['sink'] or value!=a['delay'] or value>budgets[cid]:raise Rejected('endpoint/raw budget')
   owned.update(visited)
  return owned
 eligible=sorted(cid for cid,q in qs.items() if (old[cid]['source'],old[cid]['sink'])==(source,q['sink']))
 native_nodes={r['source'] for r in old_records}
 for r in old_records:
  native_nodes.update(fields['dest_ranks'][edge_slots[e]] for e in r['answer']['physical_edge_ids'])
 penalty=max(graph.initial)+graph.n*max(graph.inc,default=0)+1
 novelty={n:penalty for n in range(graph.n) if kinds[n] in ('CHANX','CHANY') and n not in native_nodes}
 answers={};repair_calls=0;reason=None;repair_searches=[]
 try:
  for cid in eligible:answers[cid]=dict(old[cid]['answer'],physical_edge_ids=list(old[cid]['answer']['physical_edge_ids']))
  validate(answers,eligible)
  tree=graph.tree(source);seed(tree,[(qs[cid]['sink'],[edge_slots[e] for e in answers[cid]['physical_edge_ids']],budgets[cid]) for cid in eligible])
  for cid in sorted(set(qs)-set(eligible)):
   repair_calls+=1;result=expand(tree,qs[cid]['sink'],budgets[cid],fields,kinds,novelty,penalty,edge_slots)
   repair_searches.append(dict(CID=cid,**{k:v for k,v in result.items() if k not in ['path_slots']}))
   if not result['committed']:raise Rejected(result['status'])
   answers[cid]=dict(status='FOUND',physical_edge_ids=[fields['edge_ids'][s] for s in result['path_slots']],delay=result['raw'])
  owned=validate(answers,qs)
 except (Rejected,ValueError) as error:
  reason=str(error);answers=fallback();owned=validate(answers,qs)
 return dict(label_limit=LABEL_LIMIT,repair_searches=repair_searches,novelty_penalty_integer=penalty,native_CHANNEL_nodes=sum(kinds[n] in ('CHANX','CHANY') for n in native_nodes),answers=answers,retained_connection_ids=eligible if reason is None else [],attempted_retained_connection_ids=eligible,repair_calls=repair_calls,whole_NET_fallback=reason is not None,fallback_reason=reason,owner_nodes=sorted(owned))
