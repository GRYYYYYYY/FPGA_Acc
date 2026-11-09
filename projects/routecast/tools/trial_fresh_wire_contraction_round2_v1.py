"""Fixed all-query pass: exact budget/no-delay-regression marginal shared-tree wire minimization."""
import json,sys,time
started=time.perf_counter()
from fractions import Fraction as F
from collections import Counter,defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from native_bounded_wire_search_v1 import NativeBoundedSearch,MAX
from incremental_shared_tree_ledger_v1 import SharedTreeLedger
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
B=R/'experiments/fresh_wire_contraction_round1_v2_2026-10-08';proof=B/'verification.json';p=json.loads(proof.read_text());assert p['all1929_events_and_complete_original_xml_fraction_frame_pass'] and all(sha(f)==h for f,h in p['bindings'].items())
frame=p;base=json.loads((B/'receipt.json').read_text())['state'];state={int(cid):tuple(tuple(x) for x in path) for cid,path in base.items()};delay={x['connection_id']:F(x['delay_seconds']) for x in frame['rows']}
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2);graph,digest,nodes,f,rc,queries=load_endpoints(Path(case['target']));byid={q['connection_id']:q for q in queries};budget=json.loads(Path(case['budget']).read_text());assert set(state)==set(byid) and len(state)==1929
length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
native=NativeBoundedSearch(rc,length);assert sum(length.values())<MAX
shared=SharedTreeLedger(state,byid,f['capacities'],length)
slots={eid:i for i,eid in enumerate(f['edge_ids'])};D=R/'experiments/fresh_wire_contraction_round2_v1_2026-10-08';D.mkdir(exist_ok=False)
bindings={**p['bindings'],**closure([Path(__file__)]),str(proof):sha(proof),str(B/'receipt.json'):sha(B/'receipt.json')}
bindings.update(native.bindings)
protocol=dict(bindings=bindings,query_order=sorted(byid),max_labels_per_query=100000,base_pass=1,policy='Complete fixed1929 query single pass. Select first completed fresh owner plan by (critical cid, ascending before descending, index), independent of QoR. Original no-delay-worsening limits computed from current state, no historical ceilings consumed. Native CPU objective cap UINT64_MAX leaves simple path search unpruned. All current other owners and retained sameNET parents fixed per query. Original budget plus no individual delay worsening. Minimize new uniqueNET channel geometry; commit only strict NET wire reduction. Two original infeasible budgets explicitly retain, label limits retain, no optimality inferred on incomplete search. Original failed budgets not changed; no native or end-to-end success claim.')
(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');events=[]
def frame_state():
 return shared.nodes,shared.occupancy
initial_union,_=frame_state();initial_wire=sum(length.get(n,0) for ns in initial_union.values() for n in ns);assert initial_wire==11986
for ordinal,cid in enumerate(sorted(byid)):
 q=byid[cid];net=q['net_id'];before=state[cid];limit=F(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))/10**9;event=dict(connection_id=cid,query=q,old_delay_seconds=str(delay[cid]))
 if delay[cid]>limit:
  assert cid in (785,1637);event['status']='RETAIN_ORIGINAL_CERTIFIED_BUDGET_INFEASIBLE';events.append(event);continue
 unions,ledger=frame_state();outside=ledger.copy();outside.subtract(unions[net].keys());kept,parents=shared.view(cid)
 upper=min(limit,delay[cid])*rc.scale;ceiling=upper.numerator//upper.denominator
 allowed=lambda u,i:outside[f['dest_ranks'][i]]<f['capacities'][f['dest_ranks'][i]] and (f['dest_ranks'][i] not in parents or parents[f['dest_ranks'][i]]==(u,f['switch_ids'][i]))
 cost=lambda u,i:0 if f['dest_ranks'][i] in kept else length.get(f['dest_ranks'][i],0)
 tick=time.perf_counter();answer=native.query(q['source'],q['sink'],ceiling,outside,kept,parents,max_labels=100000,cost_limit_exclusive=MAX);event['search_seconds']=time.perf_counter()-tick
 if answer['status']=='NO_STRICT_IMPROVEMENT':answer['status']='UNREACHABLE'
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
 events.append(event)
 if ordinal%25==0:
  unions,_=frame_state();wire=sum(length.get(n,0) for ns in unions.values() for n in ns);print('query',ordinal+1,'/1929','wire',wire,'commits',sum(x['status']=='COMMIT' for x in events),flush=True)
  (D/'progress.json').write_text(json.dumps(dict(completed_queries=len(events),wire=wire,events=events),indent=2)+'\n')
unions,_=frame_state();final_wire=sum(length.get(n,0) for ns in unions.values() for n in ns);assert len(events)==1929 and final_wire<=initial_wire and all(sha(f)==h for f,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(D/'protocol.json'),bindings=bindings,scale=rc.scale,initial_wire=initial_wire,final_wire=final_wire,events=events,state={str(cid):[list(x) for x in path] for cid,path in state.items()},component_elapsed_seconds=time.perf_counter()-started,search_seconds=sum(e.get('search_seconds',0) for e in events),scope='Complete-model fresh native producer pass; all events/fullframe/global/native/canonical/performance evidence pending. Original two infeasible budgets remain.'),indent=2)+'\n');print('complete1929 wire',initial_wire,'->',final_wire,flush=True)

native.close()
