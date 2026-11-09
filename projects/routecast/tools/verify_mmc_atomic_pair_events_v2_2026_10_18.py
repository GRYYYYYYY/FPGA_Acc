"""Independent XML/Fraction replay of every private pair and atomic publication."""
import json,sys,time,struct
from pathlib import Path
from fractions import Fraction
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from independent_fraction_arc_context_v2 import load_context,arc_delay
from audit_structural_node_base_v1 import audit as audit_base
from immutable_channel_span_prices_v1 import channel_span_prices

def main():
 start=time.perf_counter();out=Path(sys.argv[1]).resolve();destination=Path(sys.argv[2]).resolve();rp=out/'receipt.json';receipt=json.loads(rp.read_text());p=json.loads((out/'protocol.json').read_text());assert p['bindings']==receipt['bindings'];bindings={**receipt['bindings'],**receipt['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());wp=Path(p['warm_seed_proof']);warm=json.loads(wp.read_text());assert warm['schema']=='NATIVE_ENDPOINT_ANCHORED_WARM_INPUT_V2' and warm['zero_initial_history'] and warm['all_old_per_design_minima_independently_recertified'] is False;ip=Path(warm['initial_independent_verification']);iv=json.loads(ip.read_text());assert iv['all115572V2budgets_matched'] and next(x for x in iv['rows'] if x['mode']=='native_retained')['all_original_XML_fraction_paths_budgets_parents_ledgers_pass'];assert iv['bindings'][str(wp.parent/'initial.json')]==sha(wp.parent/'initial.json');assert all(sha(k)==h for k,h in iv['bindings'].items());bindings[str(ip)]=sha(ip)
 seed=json.loads((out/'initial.json').read_text());assert seed==json.loads((wp.parent/'initial.json').read_text());epfile=Path(warm['endpoint']);ep=json.loads(epfile.read_text());queries={q['connection_id']:q for q in ep['connections']};assert len(queries)==115572;graph=Path(ep['inputs']['graph']['path']);xml,ids,classes,switches,digest=load_context(graph,ep['graph_sha256']);assert digest==ep['graph_sha256'];scale=seed['scale'];assert scale==10**18;capacities=[xml.graph.nodes[n].capacity for n in range(len(xml.graph.nodes))];base=audit_base(graph,p['structural_node_base_proof'],scale);spans=channel_span_prices(xml);weight=scale//(20*10**9);assert p['price_unit_integer']==weight
 cvp=Path(p['criticality_input_proof']);cv=json.loads(cvp.read_text());assert cv['schema']=='ROUTECAST_FROZEN_TIMING_REMAP_V1' and cv['all_values_equal_before_timing_epoch'] and cv['all_endpoints_equal_after_placement'];assert all(sha(k)==h for k,h in cv['bindings'].items());critical={};pinindex={}
 for row in json.loads((cvp.parent/'remapped_criticalities.json').read_text()):
  cid=row['connection_id'];q=queries[cid];assert (row['net'],row['source_rr'],row['target_rr'])==(q['net_id'],q['source'],q['sink']);value=Fraction(struct.unpack('<f',struct.pack('<f',float(row['criticality_float32_text'])))[0]);assert value==Fraction(row['criticality_numerator'],row['criticality_denominator']);critical[cid]=value;pinindex[cid]=row['local_sink_pin']
 assert set(critical)==set(queries);records=defaultdict(list);qgroups=defaultdict(list)
 for r in seed['records']:records[r['net_id']].append(r)
 for q in queries.values():qgroups[q['net_id']].append(q)
 for q in qgroups.values():q.sort(key=lambda x:x['connection_id'])
 def nodes(recs):return {r['source'] for r in recs}|{xml.graph.edges[e].sink for r in recs for e in r['answer']['physical_edge_ids']}
 owned={n:nodes(rs) for n,rs in records.items()};ledger=Counter(n for ns in owned.values() for n in ns);assert dict(ledger)=={int(n):v for n,v in seed['ledger'].items()};epochs={int(n):v for n,v in seed['epochs'].items()};generation=0;history=Counter();dirty=set(warm['dirty_nets']);checked=accepted=escapes=fallbacks=0
 def path(q,edgeids,budget,parents=None):
  u=q['source'];seen={u};a,b=classes[ids[u]];delay=a*b/2
  for eid in edgeids:
   if type(eid) is not int or not 0<=eid<len(xml.graph.edges):raise ValueError('edge identity')
   edge=xml.graph.edges[eid]
   if edge.source!=u or edge.sink in seen or capacities[edge.sink]<=0:raise ValueError('physical arc')
   if parents is not None:
    incoming=(u,eid)
    if edge.sink in parents and parents[edge.sink]!=incoming:raise ValueError('tree parent')
    parents[edge.sink]=incoming
   delay+=arc_delay(classes,switches,ids[edge.sink],edge.switch_id);u=edge.sink;seen.add(u)
  value=delay*scale
  if u!=q['sink'] or value.denominator!=1 or (budget is not None and value>budget):raise ValueError('endpoint/budget')
  return value.numerator
 def validate(net,recs):
  byid={r['connection_id']:r for r in recs};oldbyid={r['connection_id']:r for r in records[net]};qs=qgroups[net]
  if len(byid)!=len(recs) or set(byid)!=set(oldbyid):raise ValueError('query coverage')
  parents={}
  for q in qs:
   r=byid[q['connection_id']];old=oldbyid[q['connection_id']]
   if {k:v for k,v in r.items() if k!='answer'}!={k:v for k,v in old.items() if k!='answer'} or any(r[k]!=v for k,v in q.items()):raise ValueError('frozen metadata')
   raw=path(q,r['answer']['physical_edge_ids'],old['budget_integer'],parents)
   if r['answer']['status']!='FOUND' or raw!=r['answer']['delay']:raise ValueError('raw delay')
 def score(recs,counts):
  users={};result=Fraction(0)
  for rec in recs:
   c=critical[rec['connection_id']];result+=c*rec['answer']['delay']
   for eid in rec['answer']['physical_edge_ids']:
    node=xml.graph.edges[eid].sink;users[node]=max(users.get(node,Fraction(0)),c)
  for node,c in users.items():result+=(1-c)*(base[node]*(1+history[node])*(1+max(0,counts.get(node,0)-capacities[node]+1))+weight*spans.get(node,0))
  return result
 for index,roundrow in enumerate(receipt['rounds']):
  assert index==roundrow['round_index']
  if index:generation+=1
  assert generation==roundrow['generation_at_round_begin'];overused={n for n,c in ledger.items() if c>capacities[n]};changed={n:ledger[n]-capacities[n] for n in overused};assert changed=={int(n):v for n,v in roundrow['changed_nodes'].items()} and sum(changed.values())==roundrow['overflow_before']
  if index:history.update(changed)
  inverse={n:set() for n in overused}
  for net,ns in owned.items():
   for n in ns&overused:inverse[n].add(net)
  used=set();expectedgroups=[]
  for net in sorted(dirty):
   if net in used:continue
   choices=set()
   for node in owned[net]&overused:choices.update(inverse[node])
   choices-=used|{net};pair=sorted([net,min(choices)]) if choices else [net];used.update(pair);expectedgroups.append(pair)
  assert expectedgroups==roundrow['grouping']==[e['NETs'] for e in roundrow['events']]
  for ordinal,event in enumerate(roundrow['events']):
   checked+=1;pair=event['NETs'];assert event['group_index']==ordinal and event['generation_before']==generation and event['price_epoch']==index;assert {int(n):v for n,v in event['old_NET_epochs'].items()}=={n:epochs[n] for n in pair};candidate={int(n):rs for n,rs in event['candidate_records'].items()};assert set(candidate)==set(pair);removed=Counter(n for net in pair for n in owned[net]);common=Counter(ledger)
   for node,c in removed.items():common[node]-=c;assert common[node]>=0
   private=Counter(common);invalid=False
   try:
    for net in pair:validate(net,candidate[net])
   except ValueError:invalid=True
   a=event['admission']
   if invalid:assert a['status']=='GROUP_RETAIN_INVALID' and a['accepted'] is False
   else:
    assert len(event['private_search'])==len(pair)
    for net,part in zip(pair,event['private_search']):
     assert part['net_id']==net;old={r['connection_id']:r for r in records[net]};eligible=sorted(cid for cid,r in old.items() if len(old)>=16 and all(ledger.get(n,0)<=capacities[n] for n in nodes([r])));assert eligible==part['retained_connection_ids'];order=sorted((cid for cid in old if cid not in eligible),key=lambda cid:(-critical[cid],pinindex[cid],cid));searched=part['primary_search_connection_ids'];assert searched==order[:len(searched)] and part['primary_search_calls']==len(searched);attempts={x['connection_id']:x['physical_edge_ids'] for x in part['primary_attempts']};assert set(attempts)==set(old);parents={}
     assert searched or part['primary_complete']
     failed=searched[-1] if not part['primary_complete'] else None
     for cid,edges in attempts.items():
      if edges is not None:
       raw=path(queries[cid],edges,None,parents)
       if cid==failed:assert raw>old[cid]['budget_integer']
       else:assert raw<=old[cid]['budget_integer']
      if cid not in eligible and cid not in searched:assert edges is None
     for cid in eligible:assert attempts[cid]==old[cid]['answer']['physical_edge_ids']
     if part['primary_complete']:
      assert searched==order and all(attempts[cid] is not None for cid in old) and 'fallback' not in part;assert all(r['answer']['physical_edge_ids']==attempts[r['connection_id']] for r in candidate[net])
     else:
      fallbacks+=1;assert 'fallback' in part;f=part['fallback'];before=score(records[net],private);after=score(candidate[net],private);assert Fraction(f['old_score'])==before and Fraction(f['chosen_score'])==after
      if f['status']=='ACCEPT_STRICT_IMPROVEMENT':assert after<before
      else:assert after==before and candidate[net]==records[net]
     private.update(nodes(candidate[net]))
    before=sum((score(records[n],common) for n in pair),Fraction(0));after=sum((score(candidate[n],common) for n in pair),Fraction(0));updates={n:private.get(n,0) for n in set(ledger)|set(private) if ledger.get(n,0)!=private.get(n,0)};delta=sum(max(0,v-capacities[n])-max(0,ledger.get(n,0)-capacities[n]) for n,v in updates.items());assert a['prospective_overflow_delta']==delta and Fraction(a['old_score'])==before and Fraction(a['candidate_score'])==after and Fraction(a['objective_delta'])==after-before;accept=delta<=0 and after<=before;assert a['accepted']==accept
    expected_status='GROUP_ADMIT' if accept else 'GROUP_RETAIN_OBJECTIVE_INCREASE' if after>before else 'GROUP_RETAIN_OVERFLOW_INCREASE';assert a['status']==expected_status;standalone={}
    for net in pair:
     newnodes=nodes(candidate[net]);standalone[net]=sum(max(0,ledger.get(u,0)+(1 if u in newnodes else -1)-capacities[u])-max(0,ledger.get(u,0)-capacities[u]) for u in owned[net]^newnodes)
    assert standalone=={int(n):v for n,v in event['standalone_overflow_deltas'].items()}
    if accept:
     accepted+=1;escapes+=any(v>0 for v in standalone.values());generation+=1
     for n,v in updates.items():
      if v:ledger[n]=v
      else:ledger.pop(n,None)
     for net in pair:records[net]=candidate[net];owned[net]=nodes(candidate[net]);epochs[net]+=1
   assert event['generation_after']==generation and {int(n):v for n,v in event['new_NET_epochs'].items()}=={n:epochs[n] for n in pair}
  frame=json.loads(Path(roundrow['state_file']).read_text());assert frame['records']==sorted([r for rs in records.values() for r in rs],key=lambda x:x['connection_id']);assert {int(n):v for n,v in frame['ledger'].items()}==dict(ledger) and {int(n):v for n,v in frame['epochs'].items()}==epochs;assert frame['generation']==generation and frame['price_epoch']==index;assert {int(n):v for n,v in frame['prices'].items()}==dict(Counter(spans)+history);assert sum(max(0,c-capacities[n]) for n,c in ledger.items())==roundrow['overflow_after'];assert Counter(n for ns in owned.values() for n in ns)==ledger;print('ATOMIC_GROUP_REPLAY_ROUND_PASS',out.name,index,len(roundrow['events']),roundrow['overflow_after'],flush=True)
 assert len(receipt['rounds'])==2;final=json.loads((out/'sketch.json').read_text());assert final['records']==frame['records'] and final['ledger']==frame['ledger'] and final['epochs']==frame['epochs'];assert final['eligible_for_legal_route_commit'] is False;assert all(sha(k)==h for k,h in bindings.items());destination.open('x').write(json.dumps(dict(status='all_group_physical_paths_frozen_budgets_pairing_prices_objectives_overflow_and_epochs_pass',bindings=bindings,group_events=checked,accepted_groups=accepted,accepted_groups_with_positive_standalone_NET=escapes,independent_fallback_score_checks=fallbacks,all_group_event_replays_pass=True,seconds=time.perf_counter()-start,scope='Independent XML/Fraction/private-price/publication replay. Does not independently prove bounded fallback search optimality, native equivalence, forecast improvement or fullflow gain.'),indent=2)+'\n');print('ALL_ATOMIC_GROUP_EVENTS_PASS',out.name,checked,accepted,escapes,flush=True)
if __name__=='__main__':main()
