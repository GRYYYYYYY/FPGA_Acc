"""All archived actual-old fallback calls replayed exactly; instrumented cost."""
import cProfile,json,sys,time,pstats
from collections import defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from class_cached_rc_endpoint_context_v1 import load_endpoints
from resident_actual_old_fallback_adapter_v1 import fallback
base=R/'experiments/ultraembedded_mmc_actual_old_linear_direct_lattice_workflow_v13_2026-10-10'
admission=base/'verification.json';v=json.loads(admission.read_text());assert v['all_cases_both_complete_arms_authenticated']
assert all(sha(p)==h for p,h in v['bindings'].items())
model=base/'seed/model/mmc';rp=model/'receipt.json';r=json.loads(rp.read_text());assert v['bindings'][str(rp)]==sha(rp)
assert all(sha(p)==h for sec in ['bindings','files'] for p,h in r[sec].items())
endpoint=next(Path(p) for p in r['bindings'] if p.endswith('/endpoints.json'))
D=R/'experiments/mmc_complete_actual_old_fallback_profile_v1_2026-10-10';D.mkdir()
bindings={**closure([Path(__file__)]),str(admission):sha(admission),str(rp):sha(rp),str(endpoint):sha(endpoint)}
for filename in ['initial.json','round0.json','round1.json']:
 p=model/filename;bindings[str(p)]=sha(p)
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Archived complete development actual-old fallback replay at authenticated original prices and primary attempts. All calls and outputs compared, no sampling. cProfile instrumentation, not fresh prospective prediction, independent physical audit, ordinary timing or fullworkflow gain.'),indent=2)+'\n')
graph,digest,nodes,f,rc,queries=load_endpoints(endpoint);slots={eid:i for i,eid in enumerate(f['edge_ids'])};groups=defaultdict(list);records=defaultdict(list)
for q in queries:groups[q['net_id']].append(q)
for rec in json.loads((model/'initial.json').read_text())['records']:records[rec['net_id']].append(rec)
prof=cProfile.Profile();rows=[];events=0;accepted=retained=0
for round_index,roundrow in enumerate(r['rounds']):
 state=json.loads((model/f'round{round_index}.json').read_text());prices={int(k):x for k,x in state['prices'].items()};del state
 for event in roundrow['events']:
  net=event['net_id'];events+=1
  if 'fallback' in event:
   qs=sorted(groups[net],key=lambda q:q['connection_id']);source=qs[0]['source'];parents={};settled=set()
   assert {a['connection_id'] for a in event['primary_attempts']}=={q['connection_id'] for q in qs}
   byid={q['connection_id']:q for q in qs}
   for attempt in event['primary_attempts']:
    path=attempt['physical_edge_ids'];q=byid[attempt['connection_id']]
    if path is None:continue
    u=source;seen={u}
    for eid in path:
     slot=slots[eid];assert f['row_offsets'][u]<=slot<f['row_offsets'][u+1]
     dest=f['dest_ranks'][slot];assert dest not in seen
     if dest in parents:assert parents[dest]==(u,slot)
     parents[dest]=(u,slot);seen.add(dest);u=dest
    assert u==q['sink'];settled.add(u)
   tick=time.perf_counter();prof.enable()
   try:answer=fallback(f,rc,slots,qs,records[net],parents,settled,prices,rc.scale//(20*10**9),10000)
   finally:prof.disable()
   elapsed=time.perf_counter()-tick
   assert {k:x for k,x in answer.items() if k!='records'}==event['fallback']
   if answer['status']=='ACCEPT_STRICT_IMPROVEMENT':assert answer['records']==event['records'];accepted+=1
   else:assert answer['records']==records[net];retained+=1
   rows.append(dict(round_index=round_index,net_id=net,connections=len(qs),seconds_instrumented=elapsed,status=answer['status'],states=answer['states']))
  if event['status']=='COMMITTED':records[net]=event['records']
 assert sorted([x for recs in records.values() for x in recs],key=lambda x:x['connection_id'])==json.loads((model/f'round{round_index}.json').read_text())['records']
 print('ROUND COMPLETE',round_index,len(rows),flush=True)
assert events==96888 and len(rows)==145 and accepted==115 and retained==30
profile=D/'fallback.prof';prof.dump_stats(str(profile));stats=pstats.Stats(prof);top=[]
for key,(primitive,calls,selftime,cumulative,callers) in sorted(stats.stats.items(),key=lambda kv:kv[1][3],reverse=True)[:30]:
 top.append(dict(file=key[0],line=key[1],function=key[2],primitive_calls=primitive,calls=calls,self_seconds=selftime,cumulative_seconds=cumulative))
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,files={str(profile):sha(profile),str(D/'protocol.json'):sha(D/'protocol.json')},all_145_fallback_outputs_and_complete_round_record_replay_equal=True,events=events,accepted=accepted,retained=retained,rows=rows,top_cumulative=top,instrumented_fallback_seconds=sum(x['seconds_instrumented'] for x in rows),scope='All authenticated original archived actual-old fallback calls exactly replayed; primary paths and round prices frozen. Instrumented nested cumulative times not additive or normal timing. Not independent physical/event audit or fresh prospective model, no optimization/fullworkflow gain.'),indent=2)+'\n')
print('PASS complete 145 fallback replay profile',flush=True)
