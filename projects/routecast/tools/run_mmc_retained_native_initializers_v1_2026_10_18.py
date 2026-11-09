"""Full MMC matched-budget raw/native-retained initialization pilot."""
import json,sys,time,contextlib
from pathlib import Path
from collections import defaultdict,Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
from persistent_raw_compiled_session_v1 import Session
from compiled_criticality_tree_v1 import Graph,BINARY
from native_retained_net_initializer_v1 import initialize
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_retained_native_initializers_v1_2026-10-18';tick=time.perf_counter();cp=R/'experiments/native_retained_initializer_core_v3_2026-10-18/verification.json';core=json.loads(cp.read_text());assert core['status']=='pass' and all(sha(p)==h for p,h in core['bindings'].items())
geo=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());ep=Path(geo['previous_endpoint']);route=Path(geo['previous_native_route']);target=R/'experiments/mmc_native_state_swap_inputs_v1_2026-10-18/demand/endpoints.json';source=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18'
bindings={**closure([Path(__file__)]),str(cp):sha(cp),str(D/'protocol.json'):sha(D/'protocol.json')};cache=Cache()
with cache.installed():
 raw=Session(ep,route);cold=raw.cold_seconds
 with (D/'fresh_raw.log').open('x') as log,contextlib.redirect_stdout(log):raw_result=raw.predict(target,D/'fresh_raw',generation=0)
 frame=json.loads((D/'fresh_raw/initial.json').read_text());meta=json.loads(target.read_text());queries=meta['connections'];source_proof=json.loads((source/'independent_xml_verification_v1.json').read_text());assert source_proof['all_native_paths_exact'] and not source_proof['all_old_per_design_minima_independently_recertified'];assert all(sha(p)==h for p,h in source_proof['bindings'].items());bindings.update(source_proof['bindings']);bindings[str(source/'independent_xml_verification_v1.json')]=sha(source/'independent_xml_verification_v1.json')
 oldframe=json.loads((source/'initial.json').read_text());old={x['connection_id']:x for x in oldframe['records']};minimum={x['connection_id']:x for x in frame['records']};qby={q['connection_id']:q for q in queries};assert len(old)==len(qby)==115572
 budgets={};floors={};direct=set()
 for cid,q in qby.items():
  same=(q['source'],q['sink'])==(old[cid]['source'],old[cid]['sink'])
  if same:F=old[cid]['floor_integer'];B=max(raw.rc.scale//10**9,(3*F+1)//2,old[cid]['answer']['delay'])
  else:F=minimum[cid]['floor_integer'];B=max(raw.rc.scale//10**9,(3*F+1)//2);direct.add(cid)
  assert type(F) is int and F>=0;floors[cid]=F;budgets[cid]=B
 dirty={qby[cid]['net_id'] for cid in direct};groups=defaultdict(list)
 for q in queries:groups[q['net_id']].append(q)
 assert len(direct)==99 and len(dirty)==54
 graph_tick=time.perf_counter();g=Graph(raw.fields,raw.rc.increments,[raw.rc.initial(n) for n in range(len(raw.nodes))]);assert core['bindings'][str(BINARY)]==sha(BINARY);kinds=tuple(n.get('type') for n in raw.nodes);edge_ids=raw.fields['edge_ids'];identity=all(i==v for i,v in enumerate(edge_ids));slots=range(len(edge_ids)) if identity else {v:i for i,v in enumerate(edge_ids)};graph_seconds=time.perf_counter()-graph_tick
 outcomes={}
 for mode in ['raw_min','native_retained']:
  stage=time.perf_counter();answers={cid:dict(r['answer'],physical_edge_ids=list(r['answer']['physical_edge_ids'])) for cid,r in old.items()};ledger=Counter(raw.ledger.occupancy);independent=Counter({int(n):v for n,v in oldframe['independent_connection_ledger'].items()});events=[]
  for net in sorted(dirty):
   qs=sorted(groups[net],key=lambda q:q['connection_id']);fallback=lambda qs=qs:{q['connection_id']:dict(minimum[q['connection_id']]['answer'],physical_edge_ids=list(minimum[q['connection_id']]['answer']['physical_edge_ids'])) for q in qs}
   if mode=='native_retained':result=initialize(g,raw.fields,kinds,qs,[old[q['connection_id']] for q in qs],budgets,slots,fallback)
   else:
    selected=fallback();owner={qs[0]['source']}|{g.dest[slots[e]] for a in selected.values() for e in a['physical_edge_ids']};result=dict(answers=selected,owner_nodes=sorted(owner),retained_connection_ids=[],attempted_retained_connection_ids=[],repair_calls=0,whole_NET_fallback=False,fallback_reason=None)
   ledger.subtract(raw.ledger.nodes[net].keys());ledger.update(result['owner_nodes'])
   for cid,a in result['answers'].items():
    independent.subtract(n for n,s in raw.state[cid]);independent.update({qby[cid]['source']}|{g.dest[slots[e]] for e in a['physical_edge_ids']});answers[cid]=a
   events.append(dict(net_id=net,**{k:v for k,v in result.items() if k not in ['answers','owner_nodes']}))
  assert all(v>=0 for v in ledger.values()) and all(v>=0 for v in independent.values());ledger=+ledger;independent=+independent
  records=[dict(q,answer=answers[q['connection_id']],floor_integer=floors[q['connection_id']],budget_integer=budgets[q['connection_id']],proxy_budget_integer=max(raw.rc.scale//10**9,(3*floors[q['connection_id']]+1)//2)) for q in sorted(queries,key=lambda q:q['connection_id'])]
  for r in records:assert r['floor_integer']<=r['answer']['delay']<=r['budget_integer']
  overflow=sum(max(0,v-raw.fields['capacities'][n]) for n,v in ledger.items())
  out=D/mode;out.mkdir();initial=dict(records=records,scale=raw.rc.scale,required_connections=len(queries),completed_connections=len(records),ledger=dict(ledger),independent_connection_ledger=dict(independent),history={},epochs={str(net):int(net in dirty) for net in groups},overflow_units=overflow,eligible_for_legal_route_commit=False,budget_policy='NATIVE_ENDPOINT_ANCHORED_PROXY_V2',initializer_policy=mode,graph_sha256=raw.digest,scope='Complete demand prediction. Native retained initializer is new policy; cached oldF source contracts, no new all-old minimum dual certificates.')
  with (out/'initial.json').open('x') as f:json.dump(initial,f);f.write('\n')
  pairs={}
  for r in records:
   pair=r['source'],r['sink'];F=r['floor_integer'];assert pair not in pairs or pairs[pair]==F;pairs[pair]=F
  with (out/'floors.json').open('x') as f:json.dump([dict(source=s,sink=t,minimum_integer=v) for (s,t),v in sorted(pairs.items())],f)
  with (out/'history.json').open('x') as f:json.dump({},f)
  with (out/'initializer_events.json').open('x') as f:json.dump(events,f,indent=2)
  if mode=='raw_min':assert dict(ledger)=={int(n):v for n,v in frame['ledger'].items()}
  retained=sum(len(x['retained_connection_ids']) for x in events);fallbacks=sum(x['whole_NET_fallback'] for x in events);outcomes[mode]=dict(overflow_units=overflow,retained_unchanged_siblings=retained,repair_calls=sum(x['repair_calls'] for x in events),fallback_NETs=fallbacks,initializer_and_output_seconds=time.perf_counter()-stage)
  print('INITIALIZER DONE',mode,outcomes[mode],flush=True)
 for p in [ep,route,target,D/'fresh_raw/initial.json',D/'fresh_raw/receipt.json']:bindings[str(p)]=sha(p)
 for spec in raw_result['certificates']:bindings[spec['path']]=spec['sha256']
 for mode in ['raw_min','native_retained']:
  for p in (D/mode).iterdir():bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items());g.close();raw.close()
result=dict(bindings=bindings,outcomes=outcomes,cold_raw_graph_native_source_seconds=cold,common_full480floor_prefix_call_seconds=raw_result['total_call_seconds'],retained_graph_and_index_setup_seconds=graph_seconds,paid_total_seconds=time.perf_counter()-tick,cached_oldF_minimum_dual_scope=False,independent_initial_audits_pending=True,feedback_on_arms_pending=True,digest=cache.snapshot(),scope='Full two-initializer off-arm correctness pilot, not balanced complete4arm/native/heldout/hardware or fullworkflow timing.')
with (D/'receipt.json').open('x') as f:json.dump(result,f,indent=2)
print('PRODUCER COMPLETE',outcomes,flush=True)
