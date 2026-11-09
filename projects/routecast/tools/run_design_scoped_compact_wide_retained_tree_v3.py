"""Exact original-linear fallback model with indexed actual-old budget lookup and exact undo-stack fallback; full states and audits remain required."""
import sys,json,time,heapq
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from packed_physical_edge_slots_v1 import EdgeSlots
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from compact_wide_sparse_structural_objective_search_v1 import Search
from cached_multiplicative_occupancy_context_v1 import Context
from load_design_routing_inputs_wide_v1 import load as load_design_inputs
from criticality_resident_joint_adapter_v2 import fallback
from criticality_shared_tree_sparse_reference_v3 import Graph as CriticalityGraph
from criticality_retained_net_primary_v1 import route as criticality_primary
from criticality_objective_admission_v1 import prepare as prepare_admission

def predict(endpoint,output,node_base_proof,criticality_directory,retain_context=False):
 begin=time.perf_counter();endpoint=Path(endpoint).resolve();out=Path(output).resolve();out.mkdir(parents=True);bindings={**closure([Path(__file__)]),str(endpoint):sha(endpoint)};bindings.update({v['path']:v['sha256'] for v in json.loads(endpoint.read_text())['inputs'].values()});compact_contract=R/'experiments/compact_stream_rc_contract_v1_2026-10-13/verification.json';compact_proof=json.loads(compact_contract.read_text());assert compact_proof['all_pass'] and all(sha(p)==h for p,h in compact_proof['bindings'].items());bindings.update(compact_proof['bindings']);bindings[str(compact_contract)]=sha(compact_contract);edge_slot_contract=R/'experiments/packed_physical_edge_slots_contract_v1_2026-10-13/verification.json';edge_slot_proof=json.loads(edge_slot_contract.read_text());assert edge_slot_proof['all_pass'] and all(sha(p)==h for p,h in edge_slot_proof['bindings'].items());bindings.update(edge_slot_proof['bindings']);bindings[str(edge_slot_contract)]=sha(edge_slot_contract);graph,digest,nodes,f,rc,queries=load_endpoints(endpoint);floors={};groups=defaultdict(list);binary=R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so';contract=R/'experiments/soft_demand_workspace_radix_contract_v3_2026-10-08/verification.json';proof=json.loads(contract.read_text());assert proof['random_graphs']==200 and proof['sequential_searches_full_raw_parent_edge_and_settled_arrays_equal']==2400 and proof['bindings'][str(binary)]==sha(binary);bindings.update({str(binary):sha(binary),str(contract):sha(contract),str(R/'tools/soft_demand_cpp/tree_workspace_radix_v3.cpp'):sha(R/'tools/soft_demand_cpp/tree_workspace_radix_v3.cpp')});hybrid_contract=R/'experiments/hybrid_bidirectional_search_contract_v1_2026-10-08/verification.json';hybrid_proof=json.loads(hybrid_contract.read_text());assert hybrid_proof['pass_all'] and all(sha(p)==h for p,h in hybrid_proof['bindings'].items());extra=[hybrid_contract,R/'experiments/bidirectional_rc_build_v2_2026-10-08/search.so',R/'tools/soft_demand_cpp/bidirectional_workspace_v2.cpp',R/'tools/soft_demand_cpp/tree_workspace_radix_stats_v4.cpp'];bindings.update({str(p):sha(p) for p in extra});candidate_contract=R/'experiments/sparse_structural_objective_contract_v1_2026-10-10/verification.json';candidate_proof=json.loads(candidate_contract.read_text());assert candidate_proof['all_raw_and_independent_minimum_structural_objectives_pass'] and all(sha(p)==h for p,h in candidate_proof['bindings'].items());bindings.update(candidate_proof['bindings']);bindings[str(candidate_contract)]=sha(candidate_contract);context_contract=R/'experiments/present_occupancy_context_contract_v1_2026-10-10/verification.json';context_proof=json.loads(context_contract.read_text());assert context_proof['all_owner_exclusion_prices_minimum_objectives_and_finish_rebuilds_pass'] and context_proof['shared_fallback_same_snapshot_and_raw_budget_fixture_pass'] and all(sha(p)==h for p,h in context_proof['bindings'].items());bindings.update(context_proof['bindings']);bindings[str(context_contract)]=sha(context_contract);node_base_proof=Path(node_base_proof).resolve();criticality_directory=Path(criticality_directory).resolve();wide_input_contract=R/'experiments/design_wide_input_contract_v1_2026-10-13/verification.json';wide_input_proof=json.loads(wide_input_contract.read_text());assert wide_input_proof['all_pass'] and all(sha(p)==h for p,h in wide_input_proof['bindings'].items());bindings.update(wide_input_proof['bindings']);bindings[str(wide_input_contract)]=sha(wide_input_contract);node_base,criticalities,base_bindings=load_design_inputs(endpoint,node_base_proof,criticality_directory,len(f['capacities']),rc.scale);bindings.update(base_bindings);wide_contract=R/'experiments/compact_wide_search_snapshot_contract_v1_2026-10-13/verification.json';wide_proof=json.loads(wide_contract.read_text());assert wide_proof['all_pass'] and all(sha(p)==h for p,h in wide_proof['bindings'].items());bindings.update(wide_proof['bindings']);bindings[str(wide_contract)]=sha(wide_contract);binary=R/'experiments/wide_cost_backend_build_v1_2026-10-13/search.so';search=Search(f,rc,binary,node_base);search.prepare({},0,structural=False);search_seconds=0.0;cpp_prepare_seconds=0.0;ledger_check_seconds=0.0;fallback_seconds=0.0
 criticality_proof=criticality_directory/'verification.json'
 for q in queries:
  c=criticalities[q['connection_id']];assert (q['net_id'],q['source'],q['sink'])==(c['net'],c['source_rr'],c['target_rr']);groups[q['net_id']].append(q)
 criticality_graph=CriticalityGraph(f,rc.increments,[rc.initial(u) for u in range(len(f['capacities']))]);model_setup_seconds=time.perf_counter()-begin;initial_tick=time.perf_counter()
 (out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scheduling_policy='all_NETs_each_round',retained_tree_policy='fanout>=16; keep old paths with no globally overused node before virtual owner release; no forced timing flags; wholeNET fallback may revise retained paths',present_cost_policy='base[n]*(1+accumulated_overuse[n])*(1+max(0,other_occupancy-capacity+1)) + static_span_price; acc_fac1/pres_fac1; initial history addition skipped; old owner excluded; static span separated from history',structural_node_base_proof=str(node_base_proof),criticality_input_proof=str(criticality_proof),structural_objective='Frozen perpin initialized criticality ordered shared-tree primary; common sum_pin criticality*raw + uniqueNode(1-maxUserCriticality)*congestion; initial floor and raw budgets unchanged',rounds=2,price_unit_integer=rc.scale//(20*10**9),static_channel_span_price_ns='1/20 per destination CHAN span, applied in feedback only; initial remains exact zero-price RC floor',policy='Complete two-round criticality feedback: original zero-price initial floors/budgets; frozen native perpin criticality ordered shared-tree primary; unchanged wholeNET legacy candidates re-scored by new common objective; multiplicative owner-excluded history/present snapshots, static span separate and strict overflow guard. Complete new physical/transaction/objective audit required; not native equivalence or legal routing.',required_connections=len(queries),transaction_guard='Reject whole-NET replacements with positive prospective fullgraph overflow delta or positive same-snapshot objective delta; retain complete rejected candidate and unchanged old epoch/state.'),indent=2)+'\n');records=[];owners={};independent=Counter();failures=[]
 for net,qs in sorted(groups.items()):
  assert len({q['source'] for q in qs})==1;src=qs[0]['source'];tick=time.perf_counter();d,parents,settled=search.search(src,{q['sink'] for q in qs});search_seconds+=time.perf_counter()-tick
  if any(q['sink'] not in settled for q in qs):raise RuntimeError('Initial floor unreachable; complete-feedback gate failed, no omitted query acceptance')
  for q in qs:floors[q['source'],q['sink']]=d[q['sink']]
  budgets={q['connection_id']:max(rc.scale//10**9,(3*floors[q['source'],q['sink']]+1)//2) for q in qs}
  owned=set()
  for q in sorted(qs,key=lambda q:q['connection_id']):
   if q['sink'] not in settled or d[q['sink']]>budgets[q['connection_id']]:failures.append(dict(query=q,status='BUDGET_UNREACHABLE'));continue
   u=q['sink'];path=[];used={u}
   while u!=src:
    previous,e=parents[u];path.append(f['edge_ids'][e]);u=previous;assert u not in used;used.add(u)
   path.reverse();assert rc.path(src,q['sink'],path)==d[q['sink']];owned.update(used);independent.update(used);records.append(dict(q,answer=dict(status='FOUND',physical_edge_ids=path,delay=d[q['sink']]),budget_integer=budgets[q['connection_id']],floor_integer=floors[src,q['sink']]))
  owners[net]=owned
 ledger=Counter(n for owned in owners.values() for n in owned);overflow=sum(max(0,c-f['capacities'][n]) for n,c in ledger.items());candidate=dict(status='COMPLETE_DEMAND_SKETCH' if not failures else 'INCOMPLETE_DEMAND_SKETCH',records=records,ledger=dict(ledger),independent_connection_ledger=dict(independent),completed_connections=len(records),required_connections=len(queries),failure=failures[0] if failures else None,failures=failures,overflow_units=overflow,overflow_nodes=sum(c>f['capacities'][n] for n,c in ledger.items()),eligible_for_legal_route_commit=False,graph_sha256=digest,scope='Complete endpoint demand estimate with possible cross-NET overuse; no route acceptance.')
 assert not failures and len(records)==len(queries)
 seed=candidate;(out/'initial.json').write_text(json.dumps(seed)+'\n');(out/'floors.json').write_text(json.dumps([dict(source=s,sink=t,minimum_integer=v) for (s,t),v in sorted(floors.items())])+'\n');initial_seconds=time.perf_counter()-initial_tick;feedback_tick=time.perf_counter();slots=EdgeSlots(f['edge_ids']);records=defaultdict(list)
 for x in seed['records']:records[x['net_id']].append(x)
 def own(recs):return {x['source'] for x in recs}|{f['dest_ranks'][slots[e]] for x in recs for e in x['answer']['physical_edge_ids']}
 def rebuild():return Counter(n for recs in records.values() for n in own(recs))
 record_count=sum(map(len,records.values()));assert record_count==len(queries);owned={n:own(recs) for n,recs in records.items()};ledger=rebuild();assert dict(ledger)=={int(n):c for n,c in seed['ledger'].items()};span_prices={i:max(int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow')),int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')))+1 for i,n in enumerate(nodes) if n.get('type') in {'CHANX','CHANY'}};prices=Counter(span_prices);epochs={n:1 for n in groups};weight=rc.scale//(20*10**9);assert weight>0;rounds=[];context=Context(search,f['capacities'],node_base,len(groups),span_prices);occupancy_context_seconds=0.0
 for round_index in range(2):
  changed={n:max(0,c-f['capacities'][n]) for n,c in ledger.items() if c>f['capacities'][n]};prices.update(changed if round_index > 0 else {});prepare_tick=time.perf_counter();context.start_round(prices,weight,ledger);cpp_prepare_seconds+=time.perf_counter()-prepare_tick;affected_nodes=set(changed)|set(span_prices) if round_index==0 else set(changed);affected=sorted(groups);events=[];before=sum(changed.values());round_start=time.perf_counter()
  for net in affected:
   qs=sorted(groups[net],key=lambda q:q['connection_id']);src=qs[0]['source'];assert all(q['source']==src for q in qs);context_tick=time.perf_counter();snapshot=context.begin(owned[net]);context_updates={};occupancy_context_seconds+=time.perf_counter()-context_tick;search_tick=time.perf_counter()
   class ObjectivePrices:
    def get(self,node,default=0):return node_base[node]+snapshot.get(node,0)
   primary=criticality_primary(criticality_graph,qs,records[net],criticalities,ObjectivePrices(),f['edge_ids'],ledger,f['capacities'],slots);parents=primary['parents'];settled=primary['settled'];query_by_id={q['connection_id']:q for q in qs};raw={query_by_id[item['connection_id']]['sink']:item['raw'] for item in primary['search_results'] if 'raw' in item};search_seconds+=time.perf_counter()-search_tick
   oldepoch=epochs[net];old=records[net];oldbyid={x['connection_id']:x for x in old};assert len(oldbyid)==len(old)==len(qs) and set(oldbyid)=={q['connection_id'] for q in qs};bad=[q['connection_id'] for q in qs if q['sink'] not in settled or raw[q['sink']]>oldbyid[q['connection_id']]['budget_integer']]
   event=dict(occupancy_snapshot_ticket=context.ticket,net_id=net,old_epoch=oldepoch,new_epoch=oldepoch,status='RETAIN_BUDGET_OR_UNREACHABLE' if bad else 'COMMITTED',failed_connection_ids=bad)
   event['retained_connection_ids']=primary['retained_connection_ids']
   event['primary_search_connection_ids']=[item['connection_id'] for item in primary['search_results'] if item['status']!='RETAINED_CLEAN_BRANCH']
   event['primary_search_calls']=primary['search_calls']
   candidate_from_fallback=None
   if bad:
    attempts=[]
    for q in qs:
     path=None
     if q['sink'] in settled:
      u=q['sink'];seen={u};path=[]
      while u!=src:
       previous,edge=parents[u];path.append(f['edge_ids'][edge]);u=previous;assert u not in seen;seen.add(u)
      path.reverse()
     attempts.append(dict(connection_id=q['connection_id'],physical_edge_ids=path))
    fallback_tick=time.perf_counter();replacement=fallback(f,rc,slots,qs,old,parents,settled,snapshot,1,node_base,criticalities,10000);fallback_seconds+=time.perf_counter()-fallback_tick
    event['primary_failed_connection_ids']=list(bad);event['primary_attempts']=attempts;event['fallback']={k:(str(v) if k in ('old_score','chosen_score') else v) for k,v in replacement.items() if k!='records'}
    if replacement['status']=='ACCEPT_STRICT_IMPROVEMENT':
     candidate_from_fallback=replacement['records'];bad=[];event['status']='COMMITTED';event['failed_connection_ids']=[]
   if not bad:
    if candidate_from_fallback is not None:candidate=candidate_from_fallback
    else:
     candidate=[]
     for q in qs:
      u=q['sink'];path=[];seen={u}
      while u!=src:
       previous,edge=parents[u];path.append(f['edge_ids'][edge]);u=previous;assert u not in seen;seen.add(u)
      path.reverse();delay=rc.path(src,q['sink'],path);assert delay==raw[q['sink']]<=oldbyid[q['connection_id']]['budget_integer'];candidate.append(dict(q,answer=dict(status='FOUND',physical_edge_ids=path,delay=delay),budget_integer=oldbyid[q['connection_id']]['budget_integer'],floor_integer=oldbyid[q['connection_id']]['floor_integer']))
    newowned=own(candidate);removed=owned[net]-newowned;added=newowned-owned[net]
    # Validate every affected count before touching the shared ledger.
    updates={node:ledger[node]-1 for node in removed};updates.update({node:ledger[node]+1 for node in added});assert all(value>=0 for value in updates.values())
    admission=prepare_admission(f,rc,slots,qs,old,candidate,ledger,criticalities,ObjectivePrices())
    pressure_delta=sum(max(0,value-f['capacities'][node])-max(0,ledger[node]-f['capacities'][node]) for node,value in updates.items());assert pressure_delta==admission['prospective_overflow_delta']
    if pressure_delta<=0:assert updates==admission['updates']
    event['prospective_overflow_delta']=pressure_delta
    event['objective_guard']={k:str(admission[k]) for k in ('old_score','candidate_score','objective_delta')}
    if not admission['accepted']:
     event['status']=admission['status'];event['rejected_records']=candidate
    else:
     for node,value in updates.items():
      if value:ledger[node]=value
      else:del ledger[node]
     record_count+=len(candidate)-len(records[net]);records[net]=candidate;owned[net]=newowned;epochs[net]+=1;event['new_epoch']=epochs[net];event['records']=candidate;context_updates=updates
   context_tick=time.perf_counter();context.finish(context_updates);occupancy_context_seconds+=time.perf_counter()-context_tick;event['occupancy_snapshot_ended']=True
   assert record_count==len(queries);events.append(event)
  check_tick=time.perf_counter();assert context.active is None and context.ledger==ledger;assert record_count==sum(map(len,records.values()))==len(queries);assert ledger==rebuild();assert ledger==Counter(n for owned_nodes in owned.values() for n in owned_nodes);ledger_check_seconds+=time.perf_counter()-check_tick
  state=dict(records=sorted([x for recs in records.values() for x in recs],key=lambda x:x['connection_id']),ledger=dict(ledger),epochs=epochs.copy(),prices=dict(prices));file=out/f'round{round_index}.json';file.write_text(json.dumps(state)+'\n');after=sum(max(0,c-f['capacities'][n]) for n,c in ledger.items());rounds.append(dict(round_index=round_index,changed_nodes=changed,affected_nets=affected,events=events,overflow_before=before,overflow_after=after,state_file=str(file),seconds=time.perf_counter()-round_start));print('FEEDBACK ROUND',out.name,round_index,len(affected),sum(x['status']=='COMMITTED' for x in events),before,after,flush=True)
 final=state;independent=Counter()
 for x in final['records']:independent.update(own([x]))
 candidate=dict(seed,records=final['records'],ledger=final['ledger'],independent_connection_ledger=dict(independent),overflow_units=after,overflow_nodes=sum(c>f['capacities'][int(n)] for n,c in final['ledger'].items()),status='COMPLETE_DEMAND_SKETCH',eligible_for_legal_route_commit=False);(out/'sketch.json').write_text(json.dumps(candidate)+'\n');(out/'structural_cost_metrics.json').write_text(json.dumps(dict(node_count=len(node_base),maximum_node_base=max(node_base),scope='Initialized native structural plus perquery current occupancy snapshot; wholeNET virtual release; factor1; original RC floors and raw budgets.'),indent=2)+'\n');assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rounds=rounds,total_paid_resident_seconds=time.perf_counter()-begin,model_setup_seconds=model_setup_seconds,initial_seconds=initial_seconds,feedback_seconds=time.perf_counter()-feedback_tick,cpp_prepare_seconds=cpp_prepare_seconds,search_seconds=search_seconds,occupancy_context_seconds=occupancy_context_seconds,fallback_seconds=fallback_seconds,ledger_check_seconds=ledger_check_seconds,files={str(p):sha(p) for p in out.iterdir() if p.is_file()}),indent=2)+'\n');print('FEEDBACK DONE',out.name,after,flush=True)

 search.close()
 result=dict(completed=len(queries),overflow_units=after,total_paid_resident_seconds=time.perf_counter()-begin)
 if retain_context:return result,(graph,digest,nodes,f)
 return result
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description='Retained-tree model with explicit authenticated design inputs')
 for name in ['endpoint','output','node_base_proof','criticality_directory']:parser.add_argument(name)
 args=parser.parse_args()
 print(json.dumps(predict(args.endpoint,args.output,args.node_base_proof,args.criticality_directory)),flush=True)
