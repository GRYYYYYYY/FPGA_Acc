"""Reuse audited owner-aware bounded wire search under prior-native actual budgets."""
import pathlib,json,time
from collections import Counter
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from load_complete_route_state_v1 import load_complete
from native_bounded_wire_search_v1 import NativeBoundedSearch
from native_bounded_wire_terminal_prune_v3 import NativeBoundedSearch as PrunedSearch
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_branch_wire_terminal_prune_paired_v3_2026-10-19'
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 O.mkdir(exist_ok=False);tick=time.perf_counter();G=R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json';geometry=json.loads(G.read_text());ep=pathlib.Path(geometry['previous_endpoint']);route=pathlib.Path(geometry['previous_native_route']);S=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18';proof=S/'independent_xml_verification_v1.json';pv=json.loads(proof.read_text());source=S/'initial.json';assert pv['all_paths_original_XML_fraction_RC_budget_singleparent_and_uniqueNET_pass'];assert pv['bindings'][str(source)]==sha(source) and pv['bindings'][str(route)]==sha(route);frame=json.loads(source.read_text());records={r['connection_id']:r for r in frame['records']};nets=[1395,1400,1404,1754,2925];selected=[]
 for net in nets:selected.extend(sorted(r['connection_id'] for r in records.values() if r['net_id']==net)[:16])
 assert len(selected)==80;bindings={str(p):sha(p) for p in [G,ep,route,proof,source,pathlib.Path(__file__).resolve(),R/'tools/native_bounded_wire_search_v1.py',R/'tools/native_bounded_wire_terminal_prune_v3.py',R/'experiments/native_bounded_wire_terminal_prune_core_v3_2026-10-19/verification.json',R/'tools/load_complete_route_state_v1.py',R/'tools/incremental_shared_tree_ledger_v1.py',R/'tools/class_cached_rc_endpoint_context_v1.py']}
 write(O/'protocol.json',dict(bindings=bindings,NETs=nets,connection_ids=selected,policy='Paired identical original80 contexts; only original control decisions commit. Target-pruned sidecar proposals never mutate state. Same exact budgets and10000 Pareto label limit. Count static terminal classification setup and per-query predicate checks separately. Reuse existing bounded owner-aware Pareto CPU kernel. Commit only strict per-NET unique CHAN-span reduction with exact prior-native path RC budget and all other current branches fixed.',RC_budget='Each chosen connection exact actual RC from certified pre-existing native state, no multiplier/relaxation/future labels.',scope='Fixed80-branch pilot on known old-source placement, full55300-NET prior occupancy. Not all affected NETs or new target layout, native FULL/STA, original quality gate or runtime gain. LABEL_LIMIT means unknown and leaves state unchanged.'))
 print('CONTEXT_LOAD_START',flush=True);graph,digest,nodes,f,rc,queries=load_endpoints(ep);metadata=json.loads(ep.read_text());state,initial,ledger=load_complete(route,metadata,nodes,f,rc);initials={r['connection_id']:r for r in initial};assert all(initials[cid]['delay_integer']==records[cid]['answer']['delay'] and initials[cid]['physical_edge_ids']==records[cid]['answer']['physical_edge_ids'] for cid in selected);assert ledger.occupancy==Counter({int(v):n for v,n in frame['ledger'].items()});assert all(eid==i for i,eid in enumerate(f['edge_ids']));length=ledger.length;search=NativeBoundedSearch(rc,length);bindings.update(search.bindings);pruner=PrunedSearch(rc,length);bindings.update(pruner.bindings);bindings[str(graph)]=digest;setup=time.perf_counter()-tick;baseline=dict(ledger.wire);qmap={q['connection_id']:q for q in queries};events=[];accepted={}
 print('CONTEXT_READY',setup,flush=True)
 for ordinal,cid in enumerate(selected):
  q=qmap[cid];net=q['net_id'];kept,parents=ledger.view(cid);before=ledger.wire[net];released=before-sum(length.get(n,0) for n in kept);assert released>=0;budget=records[cid]['answer']['delay'];start=time.perf_counter();pruned=None;control_seconds=0.;pruned_seconds=0.
  if released==0:answer=dict(status='NO_UNIQUE_CHAN_TO_REMOVE',physical_edge_ids=None,labels_created=0,labels_expanded=0,examined_edges=0)
  else:
   outside=Counter({n:ledger.outside(cid,n) for n in ledger.occupancy});ctick=time.perf_counter();answer=search.query(q['source'],q['sink'],budget,outside,kept,parents,10000,released);control_seconds=time.perf_counter()-ctick
   ptick=time.perf_counter();pruned=pruner.query(q['source'],q['sink'],budget,outside,kept,parents,10000,released);pruned_seconds=time.perf_counter()-ptick
   if pruned['status']=='FOUND':
    u=q['source'];seen={u}
    for eid in pruned['physical_edge_ids']:
     assert f['row_offsets'][u]<=eid<f['row_offsets'][u+1];v=f['dest_ranks'][eid];sw=f['switch_ids'][eid];assert v not in seen and outside[v]<f['capacities'][v]
     if v in parents:assert parents[v]==(u,sw)
     seen.add(v);u=v
    assert u==q['sink'] and rc.path(q['source'],q['sink'],pruned['physical_edge_ids'])<=budget and sum(length.get(v,0) for v in seen-kept)==pruned['cost']<released
   if answer['status']=='FOUND':assert pruned['status']=='FOUND' and (pruned['cost'],pruned['delay'])==(answer['cost'],answer['delay'])
  committed=False
  if answer['status']=='FOUND':
   path=[(q['source'],None)];u=q['source']
   for eid in answer['physical_edge_ids']:
    assert f['row_offsets'][u]<=eid<f['row_offsets'][u+1];v=f['dest_ranks'][eid];path.append((v,f['switch_ids'][eid]));u=v
   assert u==q['sink'] and rc.path(q['source'],q['sink'],answer['physical_edge_ids'])<=budget;ledger.replace(cid,path);assert ledger.wire[net]<before;committed=True;accepted[cid]=answer['physical_edge_ids']
  event=dict(pruned_answer=pruned,control_query_seconds=control_seconds,pruned_query_seconds=pruned_seconds,ordinal=ordinal,connection_id=cid,net_id=net,prior_RC_budget=budget,wire_before=before,wire_after=ledger.wire[net],released_unique_span=released,committed=committed,seconds=time.perf_counter()-start,**answer);events.append(event)
  print('BRANCH',ordinal,cid,event['status'],before,ledger.wire[net],flush=True)
  with (O/'events.jsonl').open('a') as out:out.write(json.dumps(event)+'\n')
 assert all(ledger.wire[n]<=baseline[n] for n in baseline);assert all(count<=f['capacities'][node] for node,count in ledger.occupancy.items());total_delay_before=0;total_delay_after=0
 for net in nets:
  group=[r for r in records.values() if r['net_id']==net];paths={};delays={}
  for record in group:
   cid=record['connection_id'];ids=accepted.get(cid,record['answer']['physical_edge_ids']);q=qmap[cid];delay=rc.path(q['source'],q['sink'],ids);assert delay<=record['answer']['delay'];paths[record['sink']]=ids;delays[record['sink']]=delay;total_delay_before+=record['answer']['delay'];total_delay_after+=delay
  assert len(paths)==len(group);write(O/f'net_{net}_tree.json',dict(net_id=net,source=group[0]['source'],paths=paths,sink_costs=delays,unique_nodes=sorted(ledger.nodes[net]),prior_span=baseline[net],new_span=ledger.wire[net]))
 write(O/'final_unique_NET_occupancy.json',dict(ledger.occupancy));write(O/'results.json',dict(status='FIXED80_PRIOR_BUDGET_STRICT_RESOURCE_PILOT_COMPLETE',bindings=bindings,branches=80,accepted=len(accepted),status_counts=dict(Counter(e['status'] for e in events)),all55300_NETs_capacity_legal=True,all13970_selected_NET_connections_prior_RC_budgets_pass=True,prior_selected_NET_CHAN_span=sum(baseline[n] for n in nets),new_selected_NET_CHAN_span=sum(ledger.wire[n] for n in nets),prior_sum_sink_RC=total_delay_before,new_sum_sink_RC=total_delay_after,setup_seconds=setup,search_component_seconds=sum(e['seconds'] for e in events),native_calls=search.native_calls,fallback_calls=search.fallback_calls,independent_audit_pending=True));search.close();pruner.close();print('PILOT_DONE',len(accepted),sum(baseline[n] for n in nets),sum(ledger.wire[n] for n in nets),flush=True)
if __name__=='__main__':main()
