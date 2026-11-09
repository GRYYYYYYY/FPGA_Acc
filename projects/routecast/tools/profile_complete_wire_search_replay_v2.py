"""Prospective complete three-pass search-cost diagnostic; not end-to-end timing."""
import json,sys,time
from collections import Counter,defaultdict
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from csr_integer_budget_search import query
from incremental_shared_tree_ledger_v1 import SharedTreeLedger
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
start=time.perf_counter()
names=('complete_wire_contraction_v1_2026-10-08','complete_wire_contraction_v2_2026-10-08','global_guard_wire_contraction_v1_2026-10-08')
proofnames=('verification.json','verification_v3.json','verification.json')
bindings=closure([Path(__file__)])
ledgerproof=R/'experiments/incremental_shared_tree_ledger_v1_2026-10-08/verification.json';lp=json.loads(ledgerproof.read_text());assert lp['all5787_query_constraints_equal_fresh_full_state'] and all(sha(f)==h for f,h in lp['bindings'].items());bindings.update(lp['bindings']);bindings[str(ledgerproof)]=sha(ledgerproof)
passes=[]
for name,proofname in zip(names,proofnames):
 directory=R/'experiments'/name;receipt=json.loads((directory/'receipt.json').read_text());proof=json.loads((directory/proofname).read_text());protocol=json.loads((directory/'protocol.json').read_text())
 assert proof['all1929_events_and_complete_original_xml_fraction_frame_pass'] and all(sha(f)==h for f,h in proof['bindings'].items())
 bindings.update(proof['bindings'])
 for f in (directory/'receipt.json',directory/proofname,directory/'protocol.json'):bindings[str(f)]=sha(f)
 assert sha(directory/'protocol.json')==receipt['protocol_sha256']
 passes.append((name,receipt,protocol))
basepath=R/'experiments/critical_owner_transaction_v1_2026-10-08/receipt.json';base=json.loads(basepath.read_text())['rows'][0]['state'];bindings[str(basepath)]=sha(basepath)
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2)
bindings[str(Path(case['target']))]=sha(Path(case['target']));bindings[str(Path(case['budget']))]=sha(Path(case['budget']))
D=R/'experiments/complete_wire_search_cost_replay_v2_2026-10-08';D.mkdir(exist_ok=False)
policy='All three frozen passes/all1929 queries each, exact original label limits/order/constraints and independently certified ceilings. Fresh one-process shared CSR context. Time search calls and incremental shared-tree state maintenance separately; ledger v1 complete trace proof required, authenticate every answer field including work counters. No dynamic timing recalculation, preprocessing budget/endpoint creation, native loading, canonicalization, or full audits charged: component diagnostic only, never full workflow speedup. No cherry picking/repeats/early quality exit.'
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,passes=list(names),policy=policy),indent=2)+'\n')
authentication_seconds=time.perf_counter()-start;context_start=time.perf_counter();graph,digest,nodes,fields,rc,queries=load_endpoints(Path(case['target']));context_seconds=time.perf_counter()-context_start
byid={q['connection_id']:q for q in queries};slots={eid:i for i,eid in enumerate(fields['edge_ids'])};length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
state={int(cid):tuple(tuple(x) for x in path) for cid,path in base.items()};reports=[]
ledger=SharedTreeLedger(state,byid,fields['capacities'],length)
def frame():
 union=defaultdict(set);parents=defaultdict(dict)
 for cid,path in state.items():
  net=byid[cid]['net_id'];union[net].update(n for n,s in path)
  for (u,_),(v,s) in zip(path,path[1:]):assert v not in parents[net] or parents[net][v]==(u,s);parents[net][v]=(u,s)
 ledger=Counter(n for ns in union.values() for n in ns);assert all(v<=fields['capacities'][n] for n,v in ledger.items());return union,ledger
for name,receipt,protocol in passes:
 pass_start=time.perf_counter();rows=[];counts=Counter();search_seconds=0.;maintenance_seconds=0.
 assert len(receipt['events'])==1929 and protocol['query_order']==sorted(byid) and receipt['scale']==rc.scale
 union,_=frame();assert sum(length.get(n,0) for ns in union.values() for n in ns)==receipt['initial_wire']
 for event in receipt['events']:
  cid=event['connection_id'];q=byid[cid];assert event['query']==q;counts[event['status']]+=1
  if event['status']=='RETAIN_ORIGINAL_CERTIFIED_BUDGET_INFEASIBLE':
   assert cid in (785,1637);rows.append(dict(connection_id=cid,status=event['status'],searched=False));continue
  tick=time.perf_counter();net=q['net_id'];kept,fixed=ledger.view(cid);outside=ledger.occupancy.copy();outside.subtract(ledger.nodes[net].keys())
  preparation=time.perf_counter()-tick;maintenance_seconds+=preparation
  allowed=lambda u,i:outside[fields['dest_ranks'][i]]<fields['capacities'][fields['dest_ranks'][i]] and (fields['dest_ranks'][i] not in fixed or fixed[fields['dest_ranks'][i]]==(u,fields['switch_ids'][i]))
  cost=lambda u,i:0 if fields['dest_ranks'][i] in kept else length.get(fields['dest_ranks'][i],0)
  tick=time.perf_counter();answer=query(rc,q['source'],q['sink'],event['budget_integer_ceiling'],allowed,cost,max_labels=protocol['max_labels_per_query']);seconds=time.perf_counter()-tick;search_seconds+=seconds
  assert answer==event['search']
  if answer['status']=='FOUND':
   u=q['source'];path=[(u,None)]
   for eid in answer['physical_edge_ids']:
    i=slots[eid];assert fields['row_offsets'][u]<=i<fields['row_offsets'][u+1] and allowed(u,i);u=fields['dest_ranks'][i];path.append((u,fields['switch_ids'][i]))
   newwire=sum(length.get(n,0) for n in kept|{n for n,s in path});oldwire=ledger.wire[net];assert newwire==event['new_net_wire'] and oldwire==event['old_net_wire']
   if newwire<oldwire:
    assert event['status']=='COMMIT' and event['new_path']==[list(x) for x in path];tick=time.perf_counter();ledger.replace(cid,path);state[cid]=tuple(path);commit_seconds=time.perf_counter()-tick;maintenance_seconds+=commit_seconds;preparation+=commit_seconds
   else:assert event['status']=='RETAIN_FOUND'
  else:assert event['status']=='RETAIN_'+answer['status']
  rows.append(dict(connection_id=cid,status=event['status'],searched=True,search_seconds=seconds,maintenance_seconds=preparation,labels_created=answer['labels_created'],labels_expanded=answer['labels_expanded'],examined_edges=answer['examined_edges']))
  if len(rows)%100==0:print(name,len(rows),'/1929 search seconds',round(search_seconds,3),flush=True)
 assert ledger.state==state and receipt['state']=={str(cid):[list(x) for x in path] for cid,path in state.items()}
 assert sum(ledger.wire.values())==receipt['final_wire']
 report=dict(name=name,complete_queries=len(rows),search_calls=sum(x['searched'] for x in rows),status_counts=dict(counts),search_seconds=search_seconds,maintenance_seconds=maintenance_seconds,pass_seconds=time.perf_counter()-pass_start,initial_wire=receipt['initial_wire'],final_wire=receipt['final_wire'],rows=rows)
 reports.append(report);(D/(name+'.json')).write_text(json.dumps(report,indent=2)+'\n');print('complete',name,'search seconds',search_seconds,flush=True)
assert all(sha(f)==h for f,h in bindings.items())
result=dict(bindings=bindings,protocol_sha256=sha(D/'protocol.json'),authentication_seconds=authentication_seconds,context_seconds=context_seconds,complete_passes=reports,total_search_seconds=sum(x['search_seconds'] for x in reports),elapsed_seconds=time.perf_counter()-start,all5787_events_and_search_answers_reproduced=True,scope=policy)
(D/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS complete three-pass search replay',result['total_search_seconds'],'search seconds',flush=True)
