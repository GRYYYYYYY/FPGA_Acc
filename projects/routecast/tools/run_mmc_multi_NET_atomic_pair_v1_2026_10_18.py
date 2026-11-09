"""Prospectively registered two-round atomic pair candidate on3 exposed layouts."""
import json,sys,time,shutil,os,contextlib
from pathlib import Path
from collections import Counter,defaultdict
from types import MappingProxyType
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from load_design_routing_inputs_v2 import load as load_inputs
from native_price_buffer_store_v1 import Store
from cached_multiplicative_occupancy_context_v1 import Context
from compiled_criticality_tree_v1 import Graph,NativePrices,BINARY
from criticality_retained_net_primary_v1 import route
from criticality_resident_joint_adapter_v2 import fallback
from atomic_multi_NET_group_session_v1 import Session
from multi_NET_private_prices_v1 import sync,GroupPrices,groups

def plain(x):
 if isinstance(x,(dict,MappingProxyType)):return {k:plain(v) for k,v in x.items()}
 if isinstance(x,(tuple,list)):return [plain(v) for v in x]
 return x

def predict(case,folder,shared,upstream):
 begin=time.perf_counter();E=R/'experiments';endpoint=E/f'mmc_multiplacement_inputs_v1_2026-10-18/{case}/demand/endpoints.json';ep=json.loads(endpoint.read_text());graph,digest,nodes,fields,rc,_=shared;assert ep['graph_sha256']==digest;warm=E/f'mmc_multiplacement_models_v1_2026-10-18/{case}/native_retained';wp=warm/'verification.json';w=json.loads(wp.read_text());assert w['schema']=='NATIVE_ENDPOINT_ANCHORED_WARM_INPUT_V2' and w['zero_initial_history'] and all(sha(k)==h for k,h in w['bindings'].items());assert json.loads((warm/'history.json').read_text())=={};oldp=json.loads((warm.parent/'feedback_on/native_retained/protocol.json').read_text());base,criticalities,b=load_inputs(endpoint,oldp['structural_node_base_proof'],Path(oldp['criticality_input_proof']).parent,len(fields['capacities']),rc.scale);bindings={str(endpoint):sha(endpoint),**upstream,**w['bindings'],**b,str(wp):sha(wp)};queries=defaultdict(list)
 for q in ep['connections']:queries[q['net_id']].append(q)
 for qs in queries.values():qs.sort(key=lambda q:q['connection_id'])
 seed=json.loads((warm/'initial.json').read_text());oldrecords=defaultdict(list)
 for rec in seed['records']:oldrecords[rec['net_id']].append(rec)
 ledger={int(n):v for n,v in seed['ledger'].items()};epochs={int(n):v for n,v in seed['epochs'].items()};slots={eid:i for i,eid in enumerate(fields['edge_ids'])}
 def own(records):return {x['source'] for x in records}|{fields['dest_ranks'][slots[e]] for x in records for e in x['answer']['physical_edge_ids']}
 owned={n:own(rs) for n,rs in oldrecords.items()};assert Counter(n for ns in owned.values() for n in ns)==ledger
 setup=time.perf_counter();session=Session(fields,rc,slots,dict(queries),dict(oldrecords),ledger,criticalities,epochs);publisher_setup=time.perf_counter()-setup;tick=time.perf_counter();search=Graph(fields,rc.increments,[rc.initial(n) for n in range(len(nodes))]);workspace_seconds=time.perf_counter()-tick;store=Store(fields,base);spans={i:max(int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow')),int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')))+1 for i,n in enumerate(nodes) if n.get('type') in {'CHANX','CHANY'}};history=Counter(spans);weight=rc.scale//(20*10**9);context=Context(store,fields['capacities'],base,len(queries),spans);folder.mkdir();shutil.copyfile(warm/'initial.json',folder/'initial.json');shutil.copyfile(warm/'floors.json',folder/'floors.json');protocol=dict(bindings=bindings,warm_seed_proof=str(wp),structural_node_base_proof=oldp['structural_node_base_proof'],criticality_input_proof=oldp['criticality_input_proof'],candidate='atomic_coowner_pair_v1',rounds=2,price_unit_integer=weight,retained_tree_policy='fanout>=16; eligibility uses complete shared pre-group ledger',transaction_guard='New group granularity: aggregate nonpositive overflow and summed perNET same frozen group-released objective; unchanged perpin budgets; atomic snapshot publication',scope='Demand sketch only, not native legal route or default candidate.');(folder/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rounds=[];search_seconds=fallback_seconds=publication_seconds=price_seconds=0
 for index in range(2):
  state=session.snapshot()
  if index:session.advance_price_epoch(generation=state.generation);state=session.snapshot()
  changed={n:c-fields['capacities'][n] for n,c in state.ledger.items() if c>fields['capacities'][n]}
  if index:history.update(changed)
  tick=time.perf_counter();context.start_round(history,weight,state.ledger);price_seconds+=time.perf_counter()-tick;pairing=groups(set(w['dirty_nets']),owned,state.ledger,fields['capacities']);events=[];before=sum(changed.values());round_generation=state.generation
  for number,pair in enumerate(pairing):
   state=session.snapshot();removed=Counter(n for net in pair for n in owned[net]);shadow=Counter(state.ledger)
   for n,c in removed.items():shadow[n]-=c
   frozen_prices=GroupPrices(context,state.ledger,removed);touched=set(removed);tick=time.perf_counter();sync(context,shadow,touched);price_seconds+=time.perf_counter()-tick;candidates={};parts=[]
   for net in pair:
    qs=queries[net];old=state.records[net];byid={r['connection_id']:r for r in old};snapshot=context.begin(set());tick=time.perf_counter();primary=route(search,qs,old,criticalities,NativePrices(base,snapshot),fields['edge_ids'],state.ledger,fields['capacities'],slots);search_seconds+=time.perf_counter()-tick;part=dict(net_id=net,retained_connection_ids=primary['retained_connection_ids'],primary_search_connection_ids=[x['connection_id'] for x in primary['search_results'] if x['status']!='RETAINED_CLEAN_BRANCH'],primary_search_calls=primary['search_calls'],primary_complete=primary['complete'],primary_attempts=primary['attempts'])
    if not primary['complete']:
     tick=time.perf_counter();replacement=fallback(fields,rc,slots,qs,old,primary['parents'],primary['settled'],snapshot,1,base,criticalities,10000);fallback_seconds+=time.perf_counter()-tick;part['fallback']={k:str(v) if k in ('old_score','chosen_score') else v for k,v in replacement.items() if k!='records'};candidate=replacement['records']
    else:
     candidate=[];attempt_by_id={a['connection_id']:a['physical_edge_ids'] for a in primary['attempts']}
     for q in qs:
      cid=q['connection_id'];path=attempt_by_id[cid];delay=rc.path(q['source'],q['sink'],path);assert delay<=byid[cid]['budget_integer'];candidate.append(dict(byid[cid],answer=dict(status='FOUND',physical_edge_ids=path,delay=delay)))
    candidates[net]=candidate;newowned=own(candidate);updates={n:context.ledger.get(n,0)+1 for n in newowned};context.finish(updates);touched.update(newowned);parts.append(part)
   cost_nodes=set(removed)
   for rs in candidates.values():cost_nodes.update(own(rs))
   prices={n:frozen_prices.get(n) for n in cost_nodes};expected={n:state.epochs[n] for n in pair};tick=time.perf_counter()
   try:ticket,answer=session.prepare(candidates,prices,generation=state.generation,expected_epochs=expected,price_epoch=state.price_epoch)
   except ValueError as error:ticket=None;answer=dict(accepted=False,status='GROUP_RETAIN_INVALID',invalid_reason=str(error),prospective_overflow_delta=None,old_score=None,candidate_score=None,objective_delta=None)
   if ticket is not None:
    session.commit(ticket,generation=state.generation,price_epoch=state.price_epoch)
    for n in pair:owned[n]=own(candidates[n])
   publication_seconds+=time.perf_counter()-tick;after=session.snapshot();tick=time.perf_counter();sync(context,after.ledger,touched);price_seconds+=time.perf_counter()-tick
   standalone={}
   for n in pair:
    oldset=own(state.records[n]);newset=own(candidates[n]);standalone[n]=sum(max(0,state.ledger.get(u,0)+(1 if u in newset else -1)-fields['capacities'][u])-max(0,state.ledger.get(u,0)-fields['capacities'][u]) for u in oldset^newset)
   event=dict(group_index=number,NETs=list(pair),generation_before=state.generation,generation_after=after.generation,price_epoch=state.price_epoch,old_NET_epochs=expected,new_NET_epochs={n:after.epochs[n] for n in pair},candidate_records=candidates,private_search=parts,standalone_overflow_deltas=standalone,admission={k:str(v) if k in ['old_score','candidate_score','objective_delta'] else v for k,v in answer.items()});events.append(event)
  final=session.snapshot();assert context.ledger==Counter(final.ledger);assert Counter(n for ns in owned.values() for n in ns)==Counter(final.ledger);overflow=sum(max(0,c-fields['capacities'][n]) for n,c in final.ledger.items());frame=dict(records=plain(sorted([x for rs in final.records.values() for x in rs],key=lambda x:x['connection_id'])),ledger=dict(final.ledger),epochs=dict(final.epochs),generation=final.generation,price_epoch=final.price_epoch,prices=dict(history));sp=folder/f'round{index}.json';sp.write_text(json.dumps(frame,separators=(',',':'))+'\n');rounds.append(dict(round_index=index,generation_at_round_begin=round_generation,changed_nodes=changed,grouping=[list(x) for x in pairing],events=events,overflow_before=before,overflow_after=overflow,state_file=str(sp)));print('ATOMIC_PAIR_ROUND',case,index,len(pairing),sum(e['admission']['accepted'] for e in events),before,overflow,flush=True)
 independent=Counter()
 for rec in frame['records']:independent.update(own([rec]))
 sketch=dict(seed,records=frame['records'],ledger=frame['ledger'],epochs=frame['epochs'],independent_connection_ledger=dict(independent),overflow_units=overflow,overflow_nodes=sum(v>fields['capacities'][n] for n,v in final.ledger.items()),status='COMPLETE_DEMAND_SKETCH',eligible_for_legal_route_commit=False);(folder/'sketch.json').write_text(json.dumps(sketch,separators=(',',':'))+'\n');assert all(sha(k)==h for k,h in bindings.items());receipt=dict(bindings=bindings,rounds=rounds,publisher_setup_seconds=publisher_setup,compiled_workspace_setup_seconds=workspace_seconds,primary_search_seconds=search_seconds,fallback_seconds=fallback_seconds,publication_prepare_seconds=publication_seconds,private_price_seconds=price_seconds,elapsed_before_receipt_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in folder.iterdir() if p.is_file()});(folder/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');store.close();search.close();session.close();return dict(case=case,overflow_units=overflow,whole_case_seconds=time.perf_counter()-begin,group_events=sum(len(x['events']) for x in rounds),accepted_groups=sum(e['admission']['accepted'] for x in rounds for e in x['events']),accepted_groups_with_positive_standalone_NET=sum(e['admission']['accepted'] and any(v>0 for v in e['standalone_overflow_deltas'].values()) for x in rounds for e in x['events']))

def main():
 E=R/'experiments';spec=E/'mmc_multi_NET_atomic_pair_protocol_v1_2026-10-18/protocol.json';p=json.loads(spec.read_text());assert all(sha(k)==h for k,h in p['bindings'].items());root=E/'mmc_multi_NET_atomic_pair_v1_2026-10-18';root.mkdir();(root/'logs').mkdir();bindings={**closure([Path(__file__)]),str(spec):sha(spec),str(BINARY):sha(BINARY)};stat=Path('/proc/self/stat').read_text().split(') ',1)[1].split();(root/'live_process.json').write_text(json.dumps(dict(pid=os.getpid(),startticks=stat[19]))+'\n');(root/'protocol.json').write_text(json.dumps(dict(bindings=bindings,registered_protocol=str(spec)),indent=2)+'\n');tick=time.perf_counter();shared=load_endpoints(E/'mmc_multiplacement_inputs_v1_2026-10-18/case_01/demand/endpoints.json');graph_seconds=time.perf_counter()-tick;rows=[];print('ATOMIC_PAIR_GRAPH_READY',graph_seconds,flush=True)
 for case in p['cases']:
  with (root/'logs'/f'{case}.log').open('x') as log,contextlib.redirect_stdout(log):row=predict(case,root/case,shared,bindings)
  rows.append(row);print('ATOMIC_PAIR_CASE_DONE',json.dumps(row),flush=True);(root/'stages.json').write_text(json.dumps(rows,indent=2)+'\n')
 (root/'results.json').write_text(json.dumps(dict(status='all3_atomic_pair_candidates_complete_independent_group_audits_pending',bindings=bindings,shared_graph_setup_seconds=graph_seconds,cases=rows),indent=2)+'\n')
if __name__=='__main__':main()
