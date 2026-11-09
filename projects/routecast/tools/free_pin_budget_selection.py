"""Search original or snapshot-free equivalent target pins under one budget.

The caller supplies architecture-verified equivalence and a verified global
occupied-ptc snapshot. This does not commit pins or certify net/tree capacity.
A label-limited target prevents a claim of optimality over all targets.
"""
def choose(engine,context,source,sink,source_ptc,current_ptc,budget,members,occupied,equivalence='full',cost_overrides=None,blocked_edges=(),max_labels=100000,delay_prefilter=False):
 if type(sink) is not int or sink not in engine.catalog.sinks:raise ValueError('invalid sink')
 pool=engine.catalog.sinks[sink].physical_pins
 allowed=frozenset(members);used=frozenset(occupied)
 if equivalence not in {'full','none'}:raise ValueError('unverified equivalence')
 if type(current_ptc) is not int or current_ptc not in allowed:raise ValueError('original pin outside equivalence members')
 if any(type(p) is not int or p not in pool for p in tuple(allowed)+tuple(used)):raise ValueError('invalid member or occupied pin')
 if equivalence=='none' and allowed!={current_ptc}:raise ValueError('non-equivalent class must be singleton')
 targets=sorted({current_ptc}|(allowed-used if equivalence=='full' else set()))
 overrides=dict(cost_overrides or {});forbidden=frozenset(blocked_edges);attempts=[]
 if type(delay_prefilter) is not bool:raise ValueError('invalid prefilter mode')
 screening=None
 if delay_prefilter:
  from free_pin_delay_prefilter import feasible_targets
  if type(max_labels) is not int or max_labels<1:raise ValueError('invalid label limit')
  if any(type(e) is not int or not 0<=e<len(engine.graph.edges) or type(v) is not int or v<0 for e,v in overrides.items()):raise ValueError('invalid cost override')
  screening=feasible_targets(engine,context,source,sink,source_ptc,targets,budget,forbidden)
 for ptc in targets:
  if screening is not None and ptc not in screening['feasible_targets']:
   attempts.append({'status':'UNREACHABLE','path':None,'cost':None,'delay':None,'selected_ipin_ptc':ptc,'budget':budget,'max_labels':max_labels,'labels_created':0,'labels_expanded':0,'examined_edges':0,'reverse_settled_nodes':0,'reverse_examined_edges':0,'infeasibility_method':'shared_exact_delay_prefilter'})
   continue
  result=dict(engine.query_prepared(context,source,sink,source_ptc,ptc,budget,overrides,forbidden,max_labels=max_labels));result['selected_ipin_ptc']=ptc;attempts.append(result)
 limited=any(r['status']=='LABEL_LIMIT' for r in attempts);found=[r for r in attempts if r['status']=='FOUND']
 best=min(found,key=lambda r:(r['cost'],r['delay'],r['selected_ipin_ptc'])) if found else None
 answer={'status':'FOUND' if best else 'LABEL_LIMIT' if limited else 'UNREACHABLE','best':best,'attempts':attempts,'selection_complete':not limited,'optimal_over_supplied_free_targets':bool(best) and not limited,'targets':targets,'scope':'supplied fixed-source, free-equivalent target snapshot and additive costs/budget only; caller must revalidate ownership before commit'}
 if screening is not None:answer['delay_prefilter']=screening
 return answer
