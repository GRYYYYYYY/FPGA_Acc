"""Exact original-linear fallback model with indexed actual-old budget lookup and exact undo-stack fallback; full states and audits remain required."""
import sys,json,time,heapq
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from class_cached_rc_endpoint_context_v1 import load_endpoints
from sparse_structural_objective_search_v1 import Search
from multiplicative_occupancy_context_v1 import Context
from load_structural_node_base_v1 import load as load_node_base
from load_structural_node_base_v1 import PROOF as NODE_BASE_PROOF
from criticality_resident_joint_adapter_v2 import fallback
from criticality_shared_tree_sparse_reference_v3 import Graph as CriticalityGraph
from criticality_ordered_net_primary_v1 import route as criticality_primary
from load_initial_connection_criticalities_v1 import load as load_criticalities
from criticality_net_admission_v1 import prepare as prepare_admission
import datetime
O=R/'experiments/mmc_net14_frozen_schedule_diagnosis_v1_2026-10-12'
endpoint=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json'
output=O
begin=time.perf_counter();endpoint=Path(endpoint).resolve();out=Path(output).resolve();out.mkdir(parents=True);bindings={**closure([Path(__file__)]),str(endpoint):sha(endpoint)};bindings.update({v['path']:v['sha256'] for v in json.loads(endpoint.read_text())['inputs'].values()});graph,digest,nodes,f,rc,queries=load_endpoints(endpoint);floors={};groups=defaultdict(list);binary=R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so';contract=R/'experiments/soft_demand_workspace_radix_contract_v3_2026-10-08/verification.json';proof=json.loads(contract.read_text());assert proof['random_graphs']==200 and proof['sequential_searches_full_raw_parent_edge_and_settled_arrays_equal']==2400 and proof['bindings'][str(binary)]==sha(binary);bindings.update({str(binary):sha(binary),str(contract):sha(contract),str(R/'tools/soft_demand_cpp/tree_workspace_radix_v3.cpp'):sha(R/'tools/soft_demand_cpp/tree_workspace_radix_v3.cpp')});hybrid_contract=R/'experiments/hybrid_bidirectional_search_contract_v1_2026-10-08/verification.json';hybrid_proof=json.loads(hybrid_contract.read_text());assert hybrid_proof['pass_all'] and all(sha(p)==h for p,h in hybrid_proof['bindings'].items());extra=[hybrid_contract,R/'experiments/bidirectional_rc_build_v2_2026-10-08/search.so',R/'tools/soft_demand_cpp/bidirectional_workspace_v2.cpp',R/'tools/soft_demand_cpp/tree_workspace_radix_stats_v4.cpp'];bindings.update({str(p):sha(p) for p in extra});candidate_contract=R/'experiments/sparse_structural_objective_contract_v1_2026-10-10/verification.json';candidate_proof=json.loads(candidate_contract.read_text());assert candidate_proof['all_raw_and_independent_minimum_structural_objectives_pass'] and all(sha(p)==h for p,h in candidate_proof['bindings'].items());bindings.update(candidate_proof['bindings']);bindings[str(candidate_contract)]=sha(candidate_contract);context_contract=R/'experiments/present_occupancy_context_contract_v1_2026-10-10/verification.json';context_proof=json.loads(context_contract.read_text());assert context_proof['all_owner_exclusion_prices_minimum_objectives_and_finish_rebuilds_pass'] and context_proof['shared_fallback_same_snapshot_and_raw_budget_fixture_pass'] and all(sha(p)==h for p,h in context_proof['bindings'].items());bindings.update(context_proof['bindings']);bindings[str(context_contract)]=sha(context_contract);node_base,base_bindings=load_node_base(len(f['capacities']),rc.scale);bindings.update(base_bindings);search=Search(f,rc,binary,node_base);search.prepare({},0,structural=False);search_seconds=0.0;cpp_prepare_seconds=0.0;ledger_check_seconds=0.0;fallback_seconds=0.0
criticality_directory=R/'experiments/mmc_native_initial_criticality_snapshot_v2_2026-10-10';criticalities=load_criticalities(criticality_directory);criticality_proof=criticality_directory/'verification.json';bindings.update(json.loads(criticality_proof.read_text())['bindings']);bindings[str(criticality_proof)]=sha(criticality_proof)
for q in queries:
 c=criticalities[q['connection_id']];assert (q['net_id'],q['source'],q['sink'])==(c['net'],c['source_rr'],c['target_rr']);groups[q['net_id']].append(q)
criticality_graph=CriticalityGraph(f,rc.increments,[rc.initial(u) for u in range(len(f['capacities']))]);model_setup_seconds=time.perf_counter()-begin;initial_tick=time.perf_counter()
control=R/'experiments/mmc_full_schedule_control_recovery_v1_2026-10-12/model'
frame=json.loads((control/'round0.json').read_text());receipt=json.loads((control/'receipt.json').read_text())
for p in [control/'round0.json',control/'receipt.json',R/'tools/run_criticality_multiplicative_guard_model_v1.py']:bindings[str(p)]=sha(p)
slots={eid:e for e,eid in enumerate(f['edge_ids'])}
def own(recs):return {x['source'] for x in recs}|{f['dest_ranks'][slots[e]] for x in recs for e in x['answer']['physical_edge_ids']}
base_records=defaultdict(list)
for x in frame['records']:base_records[x['net_id']].append(x)
span_prices={i:max(int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow')),int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')))+1 for i,n in enumerate(nodes) if n.get('type') in {'CHANX','CHANY'}}
prices=Counter({int(k):v for k,v in frame['prices'].items()});prices.update({int(k):v for k,v in receipt['rounds'][1]['changed_nodes'].items()});weight=rc.scale//(20*10**9)
results={};events=[]
for mode in ['common_round0','recorded_pre_net14']:
 records={n:list(v) for n,v in base_records.items()};epochs={int(k):v for k,v in frame['epochs'].items()}
 if mode=='recorded_pre_net14':
  for e in receipt['rounds'][1]['events']:
   if e['net_id']==14:break
   if e['status']=='COMMITTED':records[e['net_id']]=e['records'];epochs[e['net_id']]=e['new_epoch']
 owned={n:own(v) for n,v in records.items()};ledger=Counter(n for v in owned.values() for n in v);record_count=sum(map(len,records.values()))
 context=Context(search,f['capacities'],node_base,len(groups),span_prices);context.start_round(prices,weight,ledger);net=14
 qs=sorted(groups[net],key=lambda q:q['connection_id']);src=qs[0]['source'];assert all(q['source']==src for q in qs);context_tick=time.perf_counter();snapshot=context.begin(owned[net]);context_updates={};occupancy_context_seconds+=time.perf_counter()-context_tick;search_tick=time.perf_counter()
 class ObjectivePrices:
  def get(self,node,default=0):return node_base[node]+snapshot.get(node,0)
 primary=criticality_primary(criticality_graph,qs,records[net],criticalities,ObjectivePrices(),f['edge_ids']);parents=primary['parents'];settled=primary['settled'];query_by_id={q['connection_id']:q for q in qs};raw={query_by_id[item['connection_id']]['sink']:item['raw'] for item in primary['search_results'] if 'raw' in item};search_seconds+=time.perf_counter()-search_tick
 oldepoch=epochs[net];old=records[net];oldbyid={x['connection_id']:x for x in old};assert len(oldbyid)==len(old)==len(qs) and set(oldbyid)=={q['connection_id'] for q in qs};bad=[q['connection_id'] for q in qs if q['sink'] not in settled or raw[q['sink']]>oldbyid[q['connection_id']]['budget_integer']]
 event=dict(occupancy_snapshot_ticket=context.ticket,net_id=net,old_epoch=oldepoch,new_epoch=oldepoch,status='RETAIN_BUDGET_OR_UNREACHABLE' if bad else 'COMMITTED',failed_connection_ids=bad)
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
  admission=prepare_admission(f,rc,slots,qs,old,candidate,ledger)
  pressure_delta=sum(max(0,value-f['capacities'][node])-max(0,ledger[node]-f['capacities'][node]) for node,value in updates.items());assert pressure_delta==admission['prospective_overflow_delta']
  if pressure_delta<=0:assert updates==admission['updates']
  event['prospective_overflow_delta']=pressure_delta
  if pressure_delta>0:
   event['status']='RETAIN_OVERFLOW_INCREASE';event['rejected_records']=candidate
  else:
   for node,value in updates.items():
    if value:ledger[node]=value
    else:del ledger[node]
   record_count+=len(candidate)-len(records[net]);records[net]=candidate;owned[net]=newowned;epochs[net]+=1;event['new_epoch']=epochs[net];event['records']=candidate;context_updates=updates
 context_tick=time.perf_counter();context.finish(context_updates);occupancy_context_seconds+=time.perf_counter()-context_tick;event['occupancy_snapshot_ended']=True
 assert record_count==len(queries);events.append(event)
 results[mode]=event
 if mode=='recorded_pre_net14':
  expected=next(e for e in receipt['rounds'][1]['events'] if e['net_id']==14)
  assert event['status']==expected['status'] and event.get('records')==expected.get('records')
 assert context.active is None
assert all(sha(p)==h for p,h in bindings.items())
(O/'receipt.json').write_text(json.dumps(dict(bindings=bindings,results=results,recorded_pre_net14_event_path_and_status_equal=True,scope='Selected first changed skipped NET only; common snapshot versus reconstructed pre-event snapshot. Not all skipped NETs, causal speed, hotspot quality or independent candidate audit.'),indent=2)+'\n')
search.close();print('NET14 SNAPSHOT REPLAY COMPLETE',flush=True)
