"""Discover all failures from a complete raw native route, attempt each in order."""
import json,sys,time,heapq
from pathlib import Path
from fractions import Fraction as F
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from transaction_shared_tree_ledger_v1 import TransactionLedger
from load_complete_route_state_v1 import load_complete
from native_bounded_wire_search_v1 import NativeBoundedSearch,MAX
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
started=time.perf_counter();stage_started=started;case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2)
ep=Path(case['target']);meta=json.loads(ep.read_text());route=R/'experiments/fresh_retained_branch_resume_v4_2026-10-08/resume/output.route';bp=Path(case['budget']);budget=json.loads(bp.read_text())
bindings={**closure([Path(__file__)]),str(ep):sha(ep),str(route):sha(route),str(bp):sha(bp)}
graph,digest,nodes,f,rc,queries=load_endpoints(ep);bindings[str(graph)]=digest
state,rows,ledger=load_complete(route,meta,nodes,f,rc);channel_geometry=dict(ledger.length);native=NativeBoundedSearch(rc,{});bindings.update(native.bindings)
byid={q['connection_id']:q for q in queries};delay={x['connection_id']:x['delay_integer'] for x in rows};limits={cid:F(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))*rc.scale/10**9 for cid in byid}
violations=sorted(cid for cid in byid if delay[cid]>limits[cid]);D=R/'experiments/raw_route_incremental_owner_candidate_v1_2026-10-08';D.mkdir(exist_ok=False)
protocol=dict(bindings=bindings,initial_complete_connections=len(state),attempt_order=violations,max_labels=len(f['edge_ids'])+1,policy='Import all raw post-resume native demands/physical paths afresh, discover budget violations, attempt ALL in ascending cid. Zero-objective exact Pareto reduces to min-delay Dijkstra; nonnegative increments, at most edges+1 created labels. Other owners and retained sameNET parents fixed, no whole NET released. Exhaustion means constrained budget path not found; no unconstrained infeasibility inferred. Original budgets never changed. Component starts at provided complete native route; excludes production of that route/endpoint/budget and downstream owners/wire/VPR/audits.')
(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');events=[];slots={eid:i for i,eid in enumerate(f['edge_ids'])}
for cid in violations:
 q=byid[cid];net=q['net_id'];kept,fixed=ledger.view(cid);outside=ledger.occupancy.copy();outside.subtract(ledger.nodes[net].keys());limit=limits[cid];ceiling=limit.numerator//limit.denominator;tick=time.perf_counter()
 answer=native.query(q['source'],q['sink'],ceiling,outside,kept,fixed,max_labels=len(f['edge_ids'])+1,cost_limit_exclusive=1)
 event=dict(connection_id=cid,query=q,old_path=[list(x) for x in ledger.state[cid]],old_delay_integer=delay[cid],budget_integer_ceiling=ceiling,search=answer,search_seconds=time.perf_counter()-tick,status='RETAIN_'+answer['status'])
 if answer['status']=='FOUND':
  u=q['source'];path=[(u,None)]
  for eid in answer['physical_edge_ids']:
   slot=slots[eid];assert f['row_offsets'][u]<=slot<f['row_offsets'][u+1];u=f['dest_ranks'][slot];path.append((u,f['switch_ids'][slot]))
  assert u==q['sink'] and answer['cost']==0;ledger.replace(cid,path);delay[cid]=answer['delay'];event.update(status='COMMIT',new_path=[list(x) for x in path])
 events.append(event);print(cid,event['status'],flush=True)

budget_stage=dict(initial_rows=rows,initial_budget_violation_ids=violations,events=events,state={str(cid):[list(x) for x in path] for cid,path in ledger.state.items()},final_budget_violation_ids=sorted(cid for cid in byid if delay[cid]>limits[cid]),elapsed_seconds=time.perf_counter()-stage_started)
base={cid:tuple(path) for cid,path in ledger.state.items()};base_delays={cid:F(value,rc.scale) for cid,value in delay.items()};delays=dict(base_delays);stage_started=time.perf_counter()
from exact_integer_global_timing_v2 import ExactGlobalTiming
from incremental_shared_tree_ledger_v1 import SharedTreeLedger
from collections import Counter,defaultdict
files=[R/'experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json',R/'experiments/mux_full_timing_rr_2026-10-06/w32.json',R/'experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json']
for path in files:bindings[str(path)]=sha(path)
tg,mapping,allocation=[json.loads(path.read_text()) for path in files];assert allocation['graph_sha256']==sha(files[0])==mapping['timing_graph_sha256'] and allocation['mapping_sha256']==sha(files[1])
model=ExactGlobalTiming(tg,mapping,allocation,rc.scale,F(1000)/10**9,delays);forward={n:0 for n in model.order};pred={}
for u in model.order:
 for dest,eid in model.adj[u]:
  value=forward[u]+model.weights[eid]
  if value>forward[dest]:forward[dest]=value;pred[dest]=eid
end=max(model.terminals,key=lambda n:forward[n]);assert forward==model.forward;critical=[]
while end in pred:eid=pred[end];critical.append(eid);end=model.edges[eid]['source']
critical.reverse();assert sum(model.weights[eid] for eid in critical)==model.cpd
selected=sorted({allocation['edge_connection_ids'][eid] for eid in critical if eid in allocation['edge_connection_ids']})
events=[]
from collections import Counter
for cid in selected:
 q=byid[cid];net=q['net_id'];kept,fixed=ledger.view(cid);outside=ledger.occupancy.copy();outside.subtract(ledger.nodes[net].keys());ceiling=limits[cid].numerator//limits[cid].denominator
 for scenario in ('FULL_CONSTRAINTS','RELAX_OTHER_OWNERS'):
  tick=time.perf_counter();answer=native.query(q['source'],q['sink'],ceiling,outside if scenario=='FULL_CONSTRAINTS' else Counter(),kept,fixed,len(f['edge_ids'])+1,1);blockers={}
  if answer['status']=='FOUND':
   if 'nextslot' not in globals():nextslot={eid:i for i,eid in enumerate(f['edge_ids'])}
   for eid in answer['physical_edge_ids']:
    node=f['dest_ranks'][nextslot[eid]]
    if outside[node]>=f['capacities'][node]:blockers[str(node)]=sorted(owner for owner,used in ledger.nodes.items() if owner!=net and node in used)
  events.append(dict(connection_id=cid,scenario=scenario,search=answer,search_seconds=time.perf_counter()-tick,blocking_nodes=blockers,blocking_net_ids=sorted({owner for owners in blockers.values() for owner in owners})))
owners=dict(selected_connections=selected,critical_timing_edge_ids=critical,model_cpd_ns=str(model.cpd_seconds()*10**9),events=events,elapsed_seconds=time.perf_counter()-stage_started)
minrc_calls=native.native_calls;minrc_fallback=native.fallback_calls;native.close();stage_started=time.perf_counter()
slotsource=[u for u in range(len(nodes)) for _ in range(f['row_offsets'][u],f['row_offsets'][u+1])]
plans=[]
for cid in owners['selected_connections']:
 full=next(e for e in owners['events'] if e['connection_id']==cid and e['scenario']=='FULL_CONSTRAINTS');relax=next(e for e in owners['events'] if e['connection_id']==cid and e['scenario']=='RELAX_OTHER_OWNERS')
 if full['search']['status']!='FOUND' or relax['search']['status']!='FOUND' or relax['search']['delay']>=full['search']['delay'] or not relax['blocking_net_ids']:continue
 blocking=relax['blocking_net_ids'];released=sorted(q['connection_id'] for q in queries if q['net_id'] in blocking)
 for order in ('ASCENDING','DESCENDING'):plans.append(dict(critical=cid,owners=blocking,released_connections=released,restore_order=released if order=='ASCENDING' else list(reversed(released)),order=order))
def frame(state):
 unions=defaultdict(set);parents=defaultdict(dict)
 for cid,path in state.items():
  q=byid[cid];assert path[0]==(q['source'],None) and path[-1][0]==q['sink'] and len({n for n,s in path})==len(path)
  unions[q['net_id']].update(n for n,s in path)
  for (u,_),(v,s) in zip(path,path[1:]):
   assert v not in parents[q['net_id']] or parents[q['net_id']][v]==(u,s);parents[q['net_id']][v]=(u,s)
 ledger=Counter(n for union in unions.values() for n in union);assert all(c<=f['capacities'][n] for n,c in ledger.items());return unions,parents,ledger
rows=[]
for ordinal,plan in enumerate(plans):
 state=dict(base);released=set(plan['released_connections'])|{plan['critical']}
 transaction=TransactionLedger(base,byid,f['capacities'],{})
 for cid in released:transaction.release(cid);del state[cid]
 events=[];success=True
 for cid in [plan['critical'],*plan['restore_order']]:
  q=byid[cid];net=q['net_id'];unions,parents,ledger=transaction.nodes,transaction.parents,transaction.occupancy;outside=ledger.copy();outside.subtract(unions[net].keys());fixed=parents[net];source,sink=q['source'],q['sink']
  limit=F(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))/10**9*rc.scale;ceiling=limit.numerator//limit.denominator
  allowed=lambda u,i:outside[f['dest_ranks'][i]]<f['capacities'][f['dest_ranks'][i]] and (f['dest_ranks'][i] not in fixed or fixed[f['dest_ranks'][i]]==(u,f['switch_ids'][i]))
  assert outside[source]<f['capacities'][source];dist={source:rc.initial(source)};pred={};queue=[(dist[source],source)];settled=set();found=False
  while queue:
   value,u=heapq.heappop(queue)
   if value>ceiling:break
   if u in settled or dist[u]!=value:continue
   settled.add(u)
   if u==sink:found=True;break
   for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    if not allowed(u,slot):continue
    dst=f['dest_ranks'][slot];nd=value+rc.increments[slot]
    if nd<=ceiling and nd<dist.get(dst,nd+1):dist[dst]=nd;pred[dst]=slot;heapq.heappush(queue,(nd,dst))
  clip=dist[sink] if found else ceiling+1;pot={n:d for n,d in dist.items() if d<clip};assert pot.get(source,clip)==min(rc.initial(source),clip)
  for u,value in pot.items():
   for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    if allowed(u,slot):assert pot.get(f['dest_ranks'][slot],clip)<=value+rc.increments[slot]
  cert=D/f'plan{ordinal}_query{cid}.json';cert.write_text(json.dumps(dict(clip=clip,potentials={str(n):v for n,v in pot.items()}),separators=(',',':'))+'\n');bindings[str(cert)]=sha(cert)
  event=dict(connection_id=cid,status='STAGED' if found else 'NO_CONSTRAINED_BUDGET_PATH',budget_integer_ceiling=ceiling,certificate=str(cert),certificate_sha256=sha(cert))
  if found:
   slots=[];u=sink
   while u!=source:slot=pred[u];slots.append(slot);u=slotsource[slot]
   slots.reverse();edges=[f['edge_ids'][slot] for slot in slots];path=tuple([(source,None)]+[(f['dest_ranks'][slot],f['switch_ids'][slot]) for slot in slots]);assert rc.path(source,sink,edges)==dist[sink]<=ceiling
   transaction.insert(cid,path);state[cid]=path;assert transaction.state==state;event.update(path=[list(x) for x in path],physical_edge_ids=edges,delay_integer=dist[sink])
  events.append(event)
  if not found:success=False;break
 assert set(base)==set(byid)
 if success:assert set(state)==set(base);frame(state)
 row=dict(plan=plan,events=events,transaction_complete=success,published=False,critical_delay_improved=success and F(events[0]['delay_integer'],rc.scale)<base_delays[plan['critical']],state={str(cid):[list(x) for x in path] for cid,path in (state if success else base).items()},scope='Completed candidate pending independent physical/budget/global/native checks' if success else 'Atomic whole transaction rollback; failed deterministic order does not prove joint infeasibility')
 rows.append(row);(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print(ordinal,plan['critical'],plan['order'],'complete',success,'stages',len(events),flush=True)
owner_stage=dict(rows=rows,elapsed_seconds=time.perf_counter()-stage_started)
eligible=[(row['plan']['critical'],0 if row['plan']['order']=='ASCENDING' else 1,i) for i,row in enumerate(rows) if row['transaction_complete']];selected=min(eligible)[2]
state={int(cid):tuple(tuple(x) for x in path) for cid,path in rows[selected]['state'].items()};delay=dict(base_delays)
for event in rows[selected]['events']:
 if event['status']=='STAGED':delay[event['connection_id']]=F(event['delay_integer'],rc.scale)
length=channel_geometry;native=NativeBoundedSearch(rc,length);bindings.update(native.bindings);shared=SharedTreeLedger(state,byid,f['capacities'],length);slots={eid:i for i,eid in enumerate(f['edge_ids'])}
wire_started=time.perf_counter();phases={};phase_calls={}
def measured(name):
 def decorate(fn):
  def wrapped(*args,**kwargs):
   tick=time.perf_counter()
   try:return fn(*args,**kwargs)
   finally:phases[name]=phases.get(name,0)+time.perf_counter()-tick;phase_calls[name]=phase_calls.get(name,0)+1
  return wrapped
 return decorate
protocol=dict(bindings=bindings,query_order=sorted(byid),active_pass_indices=[2],max_labels_by_pass=[10000,100000,100000],selected_owner_plan=selected,policy='Raw provided complete route through all budget repairs, critical/blocking owner discovery, all release/restore transactions with isolated incremental ledger and one direct dynamic global-guard wire pass. Shared RR CSR, minRC and wire contexts with different objectives. Single-process complete single-pass pipeline, one fresh CSR/native context/shared ledger. Original budgets unchanged. No preliminary wire scans; direct dynamic fixed-local timing target 2.87238ns and strict marginal wire bound. All1929 queries per pass, all failures retained. Selection from fresh completed owners by critical/order/index, independent of QoR. No historical candidate or ceiling input; excludes upstream production/native acceptance and audits, not complete workflow.')
(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');events=[]
def frame_state():
 return shared.nodes,shared.occupancy
initial_union,_=frame_state();initial_wire=sum(length.get(n,0) for ns in initial_union.values() for n in ns);assert initial_wire==12117 and sum(length.values())<MAX
tgp=R/'experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json';mp=R/'experiments/mux_full_timing_rr_2026-10-06/w32.json';ap=R/'experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json';tg=json.loads(tgp.read_text());mapping=json.loads(mp.read_text());allocation=json.loads(ap.read_text());assert allocation['graph_sha256']==sha(tgp)==mapping['timing_graph_sha256'] and allocation['mapping_sha256']==sha(mp)
for source in (tgp,mp,ap):bindings[str(source)]=sha(source)
target=F('2.87238')/10**9
@measured('full_dag_timing')
def construct_timing():return ExactGlobalTiming(tg,mapping,allocation,rc.scale,target,delay)
@measured('full_dag_timing')
def refresh_timing(cid):
 model.update(cid,delay[cid]);return model.cpd_seconds()
@measured('single_query_bound')
def safe_upper(cid,limit):return model.safe_upper(cid,limit)

setup_nonphase_seconds=time.perf_counter()-wire_started-sum(phases.values())
passes=[]
for pass_index in (2,):
 events=[];pass_started=time.perf_counter();pass_initial=sum(shared.wire.values())
 if pass_index==2:
  model=construct_timing();current_cpd=model.cpd_seconds()
  (D/'topology_certificate.json').write_text(json.dumps(model.topology_certificate(),indent=2)+'\n')
  bindings[str(D/'topology_certificate.json')]=sha(D/'topology_certificate.json')
 for ordinal,cid in enumerate(sorted(byid)):
  q=byid[cid];net=q['net_id'];before=state[cid];limit=F(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))/10**9;event=dict(connection_id=cid,query=q,old_delay_seconds=str(delay[cid]))
  if delay[cid]>limit:
   assert cid in (785,1637);event['status']='RETAIN_ORIGINAL_CERTIFIED_BUDGET_INFEASIBLE';events.append(event);continue
  preparation_tick=time.perf_counter()
  unions,ledger=frame_state();outside=ledger.copy();outside.subtract(unions[net].keys());kept,parents=shared.view(cid)
  strict_bound=shared.wire[net]-sum(length.get(n,0) for n in kept) if pass_index==2 else MAX;assert strict_bound>=0
  if pass_index==2:event['strict_wire_cost_bound']=strict_bound
  phases['state_preparation']=phases.get('state_preparation',0)+time.perf_counter()-preparation_tick
  if pass_index==2:
   upper_seconds,k,slack=safe_upper(cid,limit);event.update(global_upper_seconds=str(upper_seconds),model_cpd_before_ns=str(current_cpd*10**9),max_occurrences=k,min_edge_slack_seconds=str(slack) if slack is not None else None)
  else:upper_seconds=min(limit,delay[cid])
  upper=upper_seconds*rc.scale;ceiling=upper.numerator//upper.denominator
  allowed=lambda u,i:outside[f['dest_ranks'][i]]<f['capacities'][f['dest_ranks'][i]] and (f['dest_ranks'][i] not in parents or parents[f['dest_ranks'][i]]==(u,f['switch_ids'][i]))
  cost=lambda u,i:0 if f['dest_ranks'][i] in kept else length.get(f['dest_ranks'][i],0)
  tick=time.perf_counter();answer=native.query(q['source'],q['sink'],ceiling,outside,kept,parents,max_labels=protocol['max_labels_by_pass'][pass_index],cost_limit_exclusive=strict_bound);event['search_seconds']=time.perf_counter()-tick
  if pass_index<2 and answer['status']=='NO_STRICT_IMPROVEMENT':answer['status']='UNREACHABLE'
  event.update(search=answer,budget_integer_ceiling=ceiling,status='RETAIN_'+answer['status'])
  if answer['status']=='FOUND':
   source=q['source'];path=[(source,None)]
   for eid in answer['physical_edge_ids']:
    i=slots[eid];assert f['row_offsets'][source]<=i<f['row_offsets'][source+1] and allowed(source,i);source=f['dest_ranks'][i];path.append((source,f['switch_ids'][i]))
   assert source==q['sink'] and len({n for n,s in path})==len(path);old_wire=sum(length.get(n,0) for n in unions[net]);new_used=kept|{n for n,s in path};new_wire=sum(length.get(n,0) for n in new_used)
   assert sum(length.get(n,0) for n in new_used-kept)==answer['cost']
   event.update(old_net_wire=old_wire,new_net_wire=new_wire)
   if new_wire<old_wire:
    shared.replace(cid,path);state[cid]=tuple(path);delay[cid]=F(answer['delay'],rc.scale);frame_state();event.update(status='COMMIT',new_path=[list(x) for x in path],new_delay_seconds=str(delay[cid]))
    if pass_index==2:
     current_cpd=refresh_timing(cid);event['model_cpd_after_ns']=str(current_cpd*10**9)
  events.append(event)
  if ordinal%25==0:
   progress_tick=time.perf_counter()
   unions,_=frame_state();wire=sum(length.get(n,0) for ns in unions.values() for n in ns);print('pass',pass_index+1,'query',ordinal+1,'/1929','wire',wire,'commits',sum(x['status']=='COMMIT' for x in events),flush=True)
   (D/'progress.json').write_text(json.dumps(dict(pass_index=pass_index,completed_queries=len(events),wire=wire,commits=sum(e['status']=='COMMIT' for e in events)),indent=2)+'\n')
   phases['progress_output']=phases.get('progress_output',0)+time.perf_counter()-progress_tick
 passes.append(dict(pass_index=pass_index,initial_wire=pass_initial,final_wire=sum(shared.wire.values()),events=events,state={str(cid):[list(x) for x in path] for cid,path in state.items()},elapsed_seconds=time.perf_counter()-pass_started))
 assert len(events)==1929
unions,_=frame_state();final_wire=sum(length.get(n,0) for ns in unions.values() for n in ns);assert shared.state==state and len(events)==1929 and final_wire<=initial_wire and all(sha(f)==h for f,h in bindings.items())
candidate_seconds=time.perf_counter()-started
report=dict(protocol_sha256=sha(D/'protocol.json'),bindings=bindings,scale=rc.scale,budget_stage=budget_stage,discovery_stage=owners,owner_stage=owner_stage,selected_owner_plan=selected,passes=passes,state={str(cid):[list(x) for x in path] for cid,path in state.items()},final_wire=final_wire,minrc_native_calls=minrc_calls,wire_native_calls=native.native_calls,fallback_calls=minrc_fallback+native.fallback_calls,phases_seconds=phases,candidate_elapsed_seconds=candidate_seconds,scope='Single fresh provided raw post-resume route to complete candidate. No intermediate historical candidate/ceilings consumed. Shared CSR, separate exact native objectives, complete original cohort. Upstream raw route/endpoints/budgets generation and downstream VPR/canonical/audits excluded. Final receipt serialization and close not included in clock. Original budgets unchanged; no full-workflow speedup or original HDL equivalence.')
(D/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');native.close();print('raw route candidate complete',candidate_seconds,'wire',final_wire,flush=True)
