"""Independent complete online fallback event replay from original XML/Fraction."""
import sys,json,struct
from fractions import Fraction
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from audit_continue_primary_event_v1 import audit as audit_completion, POLICY as COMPLETION_POLICY
from source_binding_v2 import closure
from independent_fraction_arc_context_v2 import load_context
from buffered_rc_node_classes import read
from independent_fraction_arc_context_v2 import arc_delay
name=sys.argv[2];out=Path(sys.argv[1]).resolve();rp=out/'receipt.json';r=json.loads(rp.read_text());p=json.loads((out/'protocol.json').read_text());assert p['bindings']==r['bindings'];bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());seedfile=out/'initial.json';seed=json.loads(seedfile.read_text());records=defaultdict(list)
for x in seed['records']:records[x['net_id']].append(x)
endpoint=next(Path(k) for k in r['bindings'] if k.endswith('/endpoints.json'));ep=json.loads(endpoint.read_text());queries={q['connection_id']:q for q in ep['connections']};graph=Path(ep['inputs']['graph']['path']);xml,ids,classes,switches,digest=load_context(graph,ep['graph_sha256']);assert digest==ep['graph_sha256'];from exact_rc_lattice_direct_pairs_v2 import exact_scale
scale,electrical_pairs=exact_scale(ids,classes,switches,xml.graph.edges)
assert p['retained_tree_policy']=='fanout>=16; keep old paths with no globally overused node before virtual owner release; no forced timing flags; wholeNET fallback may revise retained paths'
assert p['primary_completion_policy']==COMPLETION_POLICY
assert p['transaction_guard']=='Reject whole-NET replacements with positive prospective fullgraph overflow delta or positive same-snapshot objective delta; retain complete rejected candidate and unchanged old epoch/state.'
from audit_wide_node_base_adapter_v1 import audit as audit_node_base
node_base=audit_node_base(graph,p['structural_node_base_proof'],scale)
assert p['price_unit_integer']==scale//(20*10**9);epochs={n:1 for n in records};prices=Counter()
from immutable_channel_span_prices_v1 import channel_span_prices
span_prices=channel_span_prices(xml);assert p['static_channel_span_price_ns']=='1/20 per destination CHAN span, applied in feedback only; initial remains exact zero-price RC floor'
prices.update(span_prices);checked=committed=retained=changed_trees=0;snapshot_count=0
assert p['present_cost_policy']=='base[n]*(1+accumulated_overuse[n])*(1+present_factor*max(0,other_occupancy-capacity+1)) + static_span_price; acc_fac1; initial history addition skipped; old owner excluded; static span separated from history'

factor=p['present_factor'];assert type(factor) is int and factor in (1,2,4)
assert len(sys.argv)==5 and int(sys.argv[4])==factor

criticality_proof=Path(p['criticality_input_proof']);cv=json.loads(criticality_proof.read_text());assert cv['nonignored_pin_keys_exactly_manifest'] and all(sha(path)==h for path,h in cv['bindings'].items());bindings.update(cv['bindings']);bindings[str(criticality_proof)]=sha(criticality_proof)
criticalities={}
pin_order={}
for row in json.loads((criticality_proof.parent/'initial_connection_criticalities.json').read_text()):
 cid=row['connection_id'];assert cid not in criticalities;query=queries[cid]
 assert (row['net'],row['source_rr'],row['target_rr'])==(query['net_id'],query['source'],query['sink'])
 value=struct.unpack('f',struct.pack('f',float(row['criticality_float32_text'])))[0];assert 0<=value<=1
 criticalities[cid]=Fraction(value)
 pin_order[cid]=row['local_sink_pin']
assert set(criticalities)==set(queries)
fallback_calls=fallback_accepted=fallback_retained=0

def physical_path(q,path,parents):
 u=q['source'];seen={u};assert xml.graph.nodes[u].capacity>0;a,b=classes[ids[u]];delay=a*b/2
 for eid in path:
  assert type(eid) is int and 0<=eid<len(xml.graph.edges)
  e=xml.graph.edges[eid];assert e.source==u and e.sink not in seen and xml.graph.nodes[e.sink].capacity>0
  incoming=(u,eid);assert e.sink not in parents or parents[e.sink]==incoming;parents[e.sink]=incoming
  delay+=arc_delay(classes,switches,ids[e.sink],e.switch_id);u=e.sink;seen.add(u)
 assert u==q['sink'];integer=delay*scale;assert integer.denominator==1
 return integer.numerator

def union_objective(recs):
 total=Fraction(0);users={};parents={}
 for rec in recs:
  q=queries[rec['connection_id']];assert all(rec[k]==q[k] for k in q)
  delay=physical_path(q,rec['answer']['physical_edge_ids'],parents);assert delay==rec['answer']['delay']<=rec['budget_integer']
  criticality=criticalities[rec['connection_id']];total+=criticality*delay
  for eid in rec['answer']['physical_edge_ids']:
   node=xml.graph.edges[eid].sink;users[node]=max(users.get(node,Fraction(0)),criticality)
 for node,maximum in users.items():
  accumulated=prices.get(node,0)-span_prices.get(node,0);assert accumulated>=0
  congestion=node_base[node]*(1+accumulated)*(1+factor*max(0,len(owner_sets[node]-{net})-xml.graph.nodes[node].capacity+1))+p['price_unit_integer']*span_prices.get(node,0)
  total+=(1-maximum)*congestion
 return total

def audit_fallback(event,old):
 meta=event['fallback'];oldbyid={x['connection_id']:x for x in old};attempts=event['primary_attempts']
 assert len(attempts)==len(old) and {a['connection_id'] for a in attempts}==set(oldbyid)
 attemptbyid={a['connection_id']:a['physical_edge_ids'] for a in attempts};bad=[];parents={}
 for cid in sorted(oldbyid):
  path=attemptbyid[cid]
  if path is None:bad.append(cid)
  else:
   delay=physical_path(queries[cid],path,parents)
   if delay>oldbyid[cid]['budget_integer']:bad.append(cid)
 assert bad and bad==event['primary_failed_connection_ids']
 old_cost=union_objective(old);assert old_cost==Fraction(meta['old_score'])
 assert meta['search_status'] in {'OPTIMAL_WITHIN_SUPPLIED_CANDIDATES','UNKNOWN_STATE_LIMIT'} and 1<=meta['states']<=10000
 if meta['search_status']=='UNKNOWN_STATE_LIMIT':assert meta['states']==10000
 if meta['status']=='ACCEPT_STRICT_IMPROVEMENT':
  assert event['status'] in {'COMMITTED','RETAIN_OVERFLOW_INCREASE','RETAIN_OBJECTIVE_INCREASE'} and not event['failed_connection_ids']
  new=event['rejected_records'] if event['status']!='COMMITTED' else event['records'];assert len(new)==len(old) and {x['connection_id'] for x in new}==set(oldbyid)
  for rec in new:
   cid=rec['connection_id'];assert rec['answer']['physical_edge_ids'] in (oldbyid[cid]['answer']['physical_edge_ids'],attemptbyid[cid])
  chosen=union_objective(new);assert chosen==Fraction(meta['chosen_score'])<old_cost
  return True
 assert meta['status']=='RETAIN' and event['status']=='RETAIN_BUDGET_OR_UNREACHABLE'
 assert event['failed_connection_ids']==bad and Fraction(meta['chosen_score'])==old_cost
 return False

def ownership(recs):
 owned=set()
 for x in recs:owned.add(x['source']);owned.update(xml.graph.edges[eid].sink for eid in x['answer']['physical_edge_ids'])
 return owned

def rebuild():return Counter(node for recs in records.values() for node in ownership(recs))
record_total=sum(map(len,records.values()));assert record_total==len(queries)
ledger=rebuild();assert dict(ledger)=={int(n):v for n,v in seed['ledger'].items()}
owner_sets=defaultdict(set)
for net,recs in records.items():
 for node in ownership(recs):owner_sets[node].add(net)
for index,roundrow in enumerate(r['rounds']):
 assert index==roundrow['round_index'];changed={n:c-xml.graph.nodes[n].capacity for n,c in ledger.items() if c>xml.graph.nodes[n].capacity};assert changed=={int(n):c for n,c in roundrow['changed_nodes'].items()};assert sum(changed.values())==roundrow['overflow_before'];prices.update(changed if index > 0 else {});affected_nodes=set(changed)|set(span_prices) if index==0 else set(changed);affected=sorted(records);assert affected==roundrow['affected_nets']==[x['net_id'] for x in roundrow['events']]
 for event in roundrow['events']:
  snapshot_count+=1;assert event['occupancy_snapshot_ticket']==snapshot_count and event['occupancy_snapshot_ended'] is True
  net=event['net_id'];old=records[net];transaction_old_nodes=ownership(old);assert epochs[net]==event['old_epoch']
  eligible=[]
  if len(old)>=16:
   for rec in old:
    nodes=ownership([rec])
    if all(ledger.get(node,0)<=xml.graph.nodes[node].capacity for node in nodes):eligible.append(rec['connection_id'])
  assert event['retained_connection_ids']==sorted(eligible)
  searched=event['primary_search_connection_ids'];assert len(searched)==event['primary_search_calls'] and len(set(searched))==len(searched)
  assert set(searched)<={rec['connection_id'] for rec in old}-set(eligible)
  assert audit_completion(event,old,eligible,criticalities,pin_order,queries,physical_path)
  if 'fallback' not in event:assert set(searched)|set(eligible)=={rec['connection_id'] for rec in old}
  if 'fallback' in event:
   fallback_calls+=1;accepted=audit_fallback(event,old);fallback_accepted+=accepted;fallback_retained+=not accepted
  else:assert event['status'] in {'COMMITTED','RETAIN_OVERFLOW_INCREASE','RETAIN_OBJECTIVE_INCREASE'} and 'primary_attempts' not in event and 'primary_failed_connection_ids' not in event
  if event['status']=='RETAIN_BUDGET_OR_UNREACHABLE':
   assert event['new_epoch']==epochs[net] and event['failed_connection_ids'] and set(event['failed_connection_ids'])<={x['connection_id'] for x in old};assert 'records' not in event;retained+=1
  else:
   assert event['status'] in {'COMMITTED','RETAIN_OVERFLOW_INCREASE','RETAIN_OBJECTIVE_INCREASE'} and not event['failed_connection_ids'];new=event['rejected_records'] if event['status']!='COMMITTED' else event['records'];changed_trees+=int(new!=old);assert len(new)==len(old) and {x['connection_id'] for x in new}=={x['connection_id'] for x in old};oldbyid={x['connection_id']:x for x in old};parents={}
   for rec in new:
    q=queries[rec['connection_id']];assert all(rec[k]==q[k] for k in q);assert rec['floor_integer']==oldbyid[rec['connection_id']]['floor_integer'] and rec['budget_integer']==oldbyid[rec['connection_id']]['budget_integer'];u=q['source'];used={u};a,b=classes[ids[u]];delay=a*b/2
    for eid in rec['answer']['physical_edge_ids']:
     edge=xml.graph.edges[eid];assert edge.source==u and edge.sink not in used and xml.graph.nodes[edge.sink].capacity>0;v=edge.sink;incoming=(u,eid);assert v not in parents or parents[v]==incoming;parents[v]=incoming;delay+=arc_delay(classes,switches,ids[v],edge.switch_id);used.add(v);u=v
    assert u==q['sink'];integer=delay*scale;assert integer.denominator==1 and integer.numerator==rec['answer']['delay']<=rec['budget_integer']
   if 'fallback' not in event:
    newbyid={rec['connection_id']:rec for rec in new}
    for cid in eligible:assert newbyid[cid]['answer']['physical_edge_ids']==oldbyid[cid]['answer']['physical_edge_ids']
   oldowned=ownership(old);newowned=ownership(new)
   proposed={node:ledger.get(node,0)-1 for node in oldowned-newowned};proposed.update({node:ledger.get(node,0)+1 for node in newowned-oldowned});assert all(value>=0 for value in proposed.values())
   pressure_delta=sum(max(0,value-xml.graph.nodes[node].capacity)-max(0,ledger.get(node,0)-xml.graph.nodes[node].capacity) for node,value in proposed.items());assert event['prospective_overflow_delta']==pressure_delta
   old_score=union_objective(old);new_score=union_objective(new);objective_delta=new_score-old_score
   meta=event['objective_guard'];assert Fraction(meta['old_score'])==old_score and Fraction(meta['candidate_score'])==new_score and Fraction(meta['objective_delta'])==objective_delta
   expected_status='RETAIN_OBJECTIVE_INCREASE' if objective_delta>0 else 'RETAIN_OVERFLOW_INCREASE' if pressure_delta>0 else 'COMMITTED'
   assert event['status']==expected_status
   if event['status']!='COMMITTED':
    assert (pressure_delta>0 or objective_delta>0) and event['new_epoch']==epochs[net] and 'records' not in event
    assert all(ledger.get(node,0)==len(owner_sets[node]) for node in oldowned|newowned)
    retained+=1;checked+=1;continue
   assert pressure_delta<=0 and objective_delta<=0 and 'rejected_records' not in event
   delta=ledger;oldowned=ownership(old);newowned=ownership(new)
   for node in oldowned-newowned:
    delta[node]-=1;assert delta[node]>=0
    if delta[node]==0:del delta[node]
   for node in newowned-oldowned:delta[node]+=1
   record_total+=len(new)-len(old);records[net]=new;epochs[net]+=1;assert epochs[net]==event['new_epoch'];ledger=delta;committed+=1
   for node in oldowned:owner_sets[node].remove(net)
   for node in newowned:owner_sets[node].add(net)
   assert all(ledger.get(node,0)==len(owner_sets[node]) for node in oldowned|newowned)
  assert record_total==len(queries);checked+=1
 assert record_total==sum(map(len,records.values()))==len(queries)
 assert ledger==rebuild() and ledger==Counter({node:len(nets) for node,nets in owner_sets.items() if nets})
 state=json.loads(Path(roundrow['state_file']).read_text());assert state['records']==sorted([x for recs in records.values() for x in recs],key=lambda x:x['connection_id']);assert {int(n):c for n,c in state['ledger'].items()}==dict(ledger);assert {int(n):c for n,c in state['prices'].items()}==dict(prices);assert {int(n):c for n,c in state['epochs'].items()}==epochs;assert roundrow['overflow_after']==sum(max(0,c-xml.graph.nodes[n].capacity) for n,c in ledger.items());print('PASS feedback replay',name,index,roundrow['overflow_after'],flush=True)
assert len(r['rounds'])==p['rounds']==2;c=json.loads((out/'sketch.json').read_text());assert c['records']==state['records'] and c['ledger']==state['ledger'] and not c['eligible_for_legal_route_commit'];assert c['completed_connections']==c['required_connections']==len(queries);assert c['overflow_units']==r['rounds'][-1]['overflow_after'];independent=Counter(node for recs in records.values() for x in recs for node in ownership([x]));assert dict(independent)=={int(n):v for n,v in c['independent_connection_ledger'].items()};assert c['overflow_nodes']==sum(cn>xml.graph.nodes[n].capacity for n,cn in ledger.items());assert all(sha(k)==h for k,h in bindings.items());Path(sys.argv[3]).resolve().write_text(json.dumps(dict(complete_primary_search_after_rejection_and_isolated_witnesses_pass=True,bindings=bindings,present_factor=factor,independent_owner_sets_scaled_polynomial=True,complete_prospective_overflow_guard_rejected_candidate_and_unchanged_epoch_pass=True,complete_same_snapshot_objective_guard_and_retained_state_pass=True,all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass=True,complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass=True,complete_fallback_attempt_membership_actual_old_objective_and_budget_checks_pass=True,fallback_calls=fallback_calls,fallback_accepted=fallback_accepted,fallback_retained=fallback_retained,events=checked,committed=committed,retained=retained,changed_trees=changed_trees,completed=len(queries),overflow_units=c['overflow_units'],ledger_update_audit='Replay bookkeeping updates touched nodes in place only after all new path/RC/ID checks; per-event independent owner-set equality and every-round full original-path ledger rebuild retained. No runtime memory-intermediate atomicity claim.',record_count_audit='Initial and every round full count, every event exact old/new length and connection-ID set check; inductive total updated only at replacement. No event omitted.',complete_present_snapshot_owner_exclusion_and_union_objective_pass=True,complete_frozen_perpin_raw_plus_max_user_unique_node_objective_pass=True,complete_structural_node_cost_original_XML_and_float32_bits_rebuild_pass=True,scope='Frozen perpin-criticality physical complete demand state/replacement audit; each event compared against independent explicit node-to-NET owner sets, full original-path ledger rebuild at each actual runtime round frame. No per-event runtime ledger snapshot exists; no actual memory intermediate-state claim. Fallback primary attempted paths independently checked on original XML/Fraction, failed budget IDs and actual-old union objective/membership checked; NOT_SETTLED paths do not carry an independent unreachability certificate; no failure infeasibility/weighted optimality/full reoptimization/heldout/native or netgain claim.'),indent=2)+'\n');print('PASS incremental feedback',checked,committed,retained,flush=True)
