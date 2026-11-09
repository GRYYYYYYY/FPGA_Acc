"""Fixed all-query pass: exact budget/no-delay-regression marginal shared-tree wire minimization."""
import json,sys,time
started=time.perf_counter()
phases={};phase_calls={}
def measured(name):
 def decorate(fn):
  def wrapped(*args,**kwargs):
   tick=time.perf_counter()
   try:return fn(*args,**kwargs)
   finally:phases[name]=phases.get(name,0)+time.perf_counter()-tick;phase_calls[name]=phase_calls.get(name,0)+1
  return wrapped
 return decorate
from fractions import Fraction as F
from collections import Counter,defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from native_bounded_wire_search_v1 import NativeBoundedSearch
from exact_integer_global_timing_v2 import ExactGlobalTiming
from incremental_shared_tree_ledger_v1 import SharedTreeLedger
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
B=R/'experiments/critical_owner_transaction_v1_2026-10-08';proof=R/'experiments/complete_wire_contraction_v2_2026-10-08/native_quality_verification.json';p=json.loads(proof.read_text());assert p['full_chain_pass'] and all(sha(f)==h for f,h in p['bindings'].items())
previous=R/'experiments/complete_wire_contraction_v2_2026-10-08';frame=json.loads((previous/'verification_v3.json').read_text());assert all(sha(f)==h for f,h in frame['bindings'].items());base=json.loads((previous/'receipt.json').read_text())['state'];state={int(cid):tuple(tuple(x) for x in path) for cid,path in base.items()};delay={x['connection_id']:F(x['delay_seconds']) for x in frame['rows']}
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2);graph,digest,nodes,f,rc,queries=load_endpoints(Path(case['target']));byid={q['connection_id']:q for q in queries};budget=json.loads(Path(case['budget']).read_text());assert set(state)==set(byid) and len(state)==1929
length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
native=NativeBoundedSearch(rc,length)
shared=SharedTreeLedger(state,byid,f['capacities'],length)
slots={eid:i for i,eid in enumerate(f['edge_ids'])};D=R/'experiments/global_guard_wire_contraction_static_multiplicity_v1_2026-10-08';D.mkdir(exist_ok=False)
bindings={**p['bindings'],**frame['bindings'],str(previous/'verification.json'):sha(previous/'verification.json'),str(previous/'receipt.json'):sha(previous/'receipt.json'),**closure([Path(__file__)]),str(proof):sha(proof),str(B/'plan0_complete_frame.json'):sha(B/'plan0_complete_frame.json'),str(B/'receipt.json'):sha(B/'receipt.json')}
bindings.update(native.bindings)
protocol=dict(bindings=bindings,query_order=sorted(byid),max_labels_per_query=100000,base_pass=2,policy='Complete fixed1929 query single pass. All current other owners and retained sameNET parents fixed per query. Original budget plus dynamically recomputed global model CPD<=2.87238ns. Minimize new uniqueNET channel geometry with nonnegative-objective pruning at current exclusive marginal wire bound; incremental shared-tree ledger and range-checked exact native CPU search/Python fallback and exact integer fixed-local timing lattice, commit only strict NET wire reduction. Two original infeasible budgets explicitly retain, label limits retain, no optimality inferred on incomplete search. Original failed budgets not changed; no native or end-to-end success claim.')
(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');events=[]
def frame_state():
 return shared.nodes,shared.occupancy
initial_union,_=frame_state();initial_wire=sum(length.get(n,0) for ns in initial_union.values() for n in ns);assert initial_wire==11971
hp=R/'experiments/complete_wire_global_headroom_v1_2026-10-08/verification.json';hv=json.loads(hp.read_text());assert hv['all1929_single_connection_bound_certificates_pass'];hd=hp.with_name('diagnosis.json');assert hv['diagnosis_sha256']==sha(hd);head=json.loads(hd.read_text());assert all(sha(p)==h for p,h in head['bindings'].items());bindings.update(head['bindings']);bindings[str(hp)]=sha(hp)
tgp=R/'experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json';mp=R/'experiments/mux_full_timing_rr_2026-10-06/w32.json';ap=R/'experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json';tg=json.loads(tgp.read_text());mapping=json.loads(mp.read_text());allocation=json.loads(ap.read_text());assert allocation['graph_sha256']==sha(tgp)==mapping['timing_graph_sha256'] and allocation['mapping_sha256']==sha(mp)
for source in (tgp,mp,ap):bindings[str(source)]=sha(source)
target=F('2.87238')/10**9
@measured('full_dag_timing')
def construct_timing():return ExactGlobalTiming(tg,mapping,allocation,rc.scale,target,delay)
model=construct_timing();current_cpd=model.cpd_seconds()
(D/'topology_certificate.json').write_text(json.dumps(model.topology_certificate(),indent=2)+'\n')
bindings[str(D/'topology_certificate.json')]=sha(D/'topology_certificate.json')
@measured('full_dag_timing')
def refresh_timing(cid):
 model.update(cid,delay[cid]);return model.cpd_seconds()
(D/'global_policy.json').write_text(json.dumps(dict(bindings=bindings,target_model_cpd_ns='2.87238',initial_model_cpd_ns=str(current_cpd*10**9),policy='All1929 fixed query order, per-query original budget unchanged. Recompute full-DAG current arrival/back values after each accepted commit; single-query repeated-edge multiplicity bound. Strict wire reduction, global model guard, no individual RC nonregression requirement. Original two infeasible budgets retained; native STA/complete quality proof still required.'),indent=2)+'\n')
@measured('single_query_bound')
def safe_upper(cid,limit):return model.safe_upper(cid,limit)

setup_nonphase_seconds=time.perf_counter()-started-sum(phases.values())
for ordinal,cid in enumerate(sorted(byid)):
 q=byid[cid];net=q['net_id'];before=state[cid];limit=F(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))/10**9;event=dict(connection_id=cid,query=q,old_delay_seconds=str(delay[cid]))
 if delay[cid]>limit:
  assert cid in (785,1637);event['status']='RETAIN_ORIGINAL_CERTIFIED_BUDGET_INFEASIBLE';events.append(event);continue
 preparation_tick=time.perf_counter()
 unions,ledger=frame_state();outside=ledger.copy();outside.subtract(unions[net].keys());kept,parents=shared.view(cid)
 strict_bound=shared.wire[net]-sum(length.get(n,0) for n in kept);assert strict_bound>=0;event['strict_wire_cost_bound']=strict_bound
 phases['state_preparation']=phases.get('state_preparation',0)+time.perf_counter()-preparation_tick
 upper_seconds,k,slack=safe_upper(cid,limit);upper=upper_seconds*rc.scale;ceiling=upper.numerator//upper.denominator;event.update(global_upper_seconds=str(upper_seconds),model_cpd_before_ns=str(current_cpd*10**9),max_occurrences=k,min_edge_slack_seconds=str(slack) if slack is not None else None)
 allowed=lambda u,i:outside[f['dest_ranks'][i]]<f['capacities'][f['dest_ranks'][i]] and (f['dest_ranks'][i] not in parents or parents[f['dest_ranks'][i]]==(u,f['switch_ids'][i]))
 cost=lambda u,i:0 if f['dest_ranks'][i] in kept else length.get(f['dest_ranks'][i],0)
 tick=time.perf_counter();answer=native.query(q['source'],q['sink'],ceiling,outside,kept,parents,max_labels=100000,cost_limit_exclusive=strict_bound);event['search_seconds']=time.perf_counter()-tick;event.update(search=answer,budget_integer_ceiling=ceiling,status='RETAIN_'+answer['status'])
 if answer['status']=='FOUND':
  source=q['source'];path=[(source,None)]
  for eid in answer['physical_edge_ids']:
   i=slots[eid];assert f['row_offsets'][source]<=i<f['row_offsets'][source+1] and allowed(source,i);source=f['dest_ranks'][i];path.append((source,f['switch_ids'][i]))
  assert source==q['sink'] and len({n for n,s in path})==len(path);old_wire=sum(length.get(n,0) for n in unions[net]);new_used=kept|{n for n,s in path};new_wire=sum(length.get(n,0) for n in new_used)
  assert sum(length.get(n,0) for n in new_used-kept)==answer['cost']
  event.update(old_net_wire=old_wire,new_net_wire=new_wire)
  if new_wire<old_wire:
   shared.replace(cid,path);state[cid]=tuple(path);delay[cid]=F(answer['delay'],rc.scale);frame_state();current_cpd=refresh_timing(cid);event.update(status='COMMIT',new_path=[list(x) for x in path],new_delay_seconds=str(delay[cid]),model_cpd_after_ns=str(current_cpd*10**9))
 events.append(event)
 if ordinal%25==0:
  progress_tick=time.perf_counter()
  unions,_=frame_state();wire=sum(length.get(n,0) for ns in unions.values() for n in ns);print('query',ordinal+1,'/1929','wire',wire,'commits',sum(x['status']=='COMMIT' for x in events),flush=True)
  (D/'progress.json').write_text(json.dumps(dict(completed_queries=len(events),wire=wire,events=events),indent=2)+'\n')
  phases['progress_output']=phases.get('progress_output',0)+time.perf_counter()-progress_tick
unions,_=frame_state();final_wire=sum(length.get(n,0) for ns in unions.values() for n in ns);assert shared.state==state and len(events)==1929 and final_wire<=initial_wire and all(sha(f)==h for f,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(D/'protocol.json'),bindings=bindings,scale=rc.scale,initial_wire=initial_wire,final_wire=final_wire,events=events,state={str(cid):[list(x) for x in path] for cid,path in state.items()},timing_lattice_scale=model.scale,phases_seconds=phases,phase_calls=phase_calls,setup_nonphase_seconds=setup_nonphase_seconds,elapsed_seconds=time.perf_counter()-started,search_seconds=sum(e.get('search_seconds',0) for e in events),native_calls=native.native_calls,fallback_calls=native.fallback_calls,native_input_preparation_seconds=native.preparation_seconds,scope='Complete-model native CPU producer pass; all events/fullframe/global/native/canonical/performance evidence pending. Original two infeasible budgets remain.'),indent=2)+'\n');print('complete1929 wire',initial_wire,'->',final_wire,flush=True)

native.close()
