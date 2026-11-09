"""Exact work attribution, legacy event projection and authenticated CID transfer."""
import sys,json,array,itertools
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from native_connection_work_trace_replay_v1 import replay
from versioned_digest_cache_v1 import Cache

def main():
 E=R/'experiments';source=E/'mmc_native_connection_work_cascade_trace_v1_2026-10-18';rp=source/'cohort_equivalence.json';r=json.loads(rp.read_text());assert r['all6_native_full_output_bytes_integer_counters_equal'];old=E/'mmc_native_connection_cascade_trace_v1_2026-10-18';oldp=old/'cohort_equivalence.json';oldproof=json.loads(oldp.read_text());cidp=E/'mmc_native_connection_CID_binding_v1_2026-10-18/independent_verification_v1.json';cidproof=json.loads(cidp.read_text());corep=E/'native_connection_work_replay_core_v1_2026-10-18/verification.json';core=json.loads(corep.read_text());assert core['status']=='heap_snapshot_trace_parser_core_fixtures_pass';queryp=E/'native_manifest_scope_preflight_v1_2026-10-10/mmc.queries';mapping={}
 for line in queryp.read_text().splitlines():
  t=line.split()
  if t[0]=='Q':cid,net,pin,src,sink=map(int,t[1:]);mapping[cid]=(net,pin)
 assert len(mapping)==115572 and sha(queryp)==cidproof['bindings'][str(queryp)];out=E/'mmc_native_connection_work_replay_v1_2026-10-18';out.mkdir(exist_ok=False);bindings={**r['bindings'],str(rp):sha(rp),str(oldp):sha(oldp),str(cidp):sha(cidp),str(corep):sha(corep),str(queryp):sha(queryp),str(Path(__file__)):sha(__file__),str(R/'tools/native_connection_work_trace_replay_v1.py'):sha(R/'tools/native_connection_work_trace_replay_v1.py')};rows=[]
 with Cache().installed():
  assert all(sha(p)==h for p,h in bindings.items())
  for row in r['rows']:
   case,arm=row['case'],row['arm'];trace=source/case/arm/'connection_trace.tsv';legacy=old/case/arm/'connection_trace.tsv';assert sha(trace)==bindings[str(trace)] and sha(legacy)==oldproof['bindings'][str(legacy)];projected=0
   with trace.open() as a,legacy.open() as b:
    assert a.readline()=='CONNECTION_TRACE 2\n' and b.readline()=='CONNECTION_TRACE 1\n'
    for x,y in itertools.zip_longest(a,b):
     assert x is not None and y is not None;t=x.split();n={'A':7,'C':5,'F':5,'S':4,'END':5}.get(t[0],len(t));assert t[:n]==y.split();projected+=1
   v=replay(trace);assert v['router_success'];assert v['successful']==row['successful_native_sink_operations'] and v['attributed_heap_pushes']==row['attributed_sink_heap_pushes'] and v['attributed_heap_pops']==row['attributed_sink_heap_pops'];assert all(i['native_counter_checked'] for i in v['iterations']);native_pushes=sum(i['native_heap_pushes'] for i in v['iterations']);native_pops=sum(i['native_heap_pops'] for i in v['iterations']);assert native_pushes-v['attributed_heap_pushes']==row['outside_sink_heap_pushes'] and native_pops-v['attributed_heap_pops']==row['outside_sink_heap_pops'];assert native_pushes==row['native_work']['total_heap_pushes'];assert set(k for k,n in v['heap_pushes_by_native_pin'].items() if n)<=set(mapping.values()) and set(k for k,n in v['heap_pops_by_native_pin'].items() if n)<=set(mapping.values())
   pushes=array.array('Q',[v['heap_pushes_by_native_pin'][mapping[cid]] for cid in range(115572)]);pops=array.array('Q',[v['heap_pops_by_native_pin'][mapping[cid]] for cid in range(115572)]);assert sum(pushes)==v['attributed_heap_pushes'] and sum(pops)==v['attributed_heap_pops'];folder=out/(case+'__'+arm);folder.mkdir();vectors={}
   for name,data in [('heap_pushes',pushes),('heap_pops',pops)]:
    p=folder/(name+'.u64');p.write_bytes(data.tobytes());vectors[name]=dict(path=str(p),sha256=sha(p),typecode='Q',itemsize=data.itemsize,values=len(data),byteorder=sys.byteorder)
   summary=dict(case=case,arm=arm,CIDs=115572,legacy_event_records_equal=projected,successful_sink_operations=v['successful'],native_heap_pushes=native_pushes,native_heap_pops=native_pops,attributed_heap_pushes=sum(pushes),attributed_heap_pops=sum(pops),outside_sink_heap_pushes=native_pushes-sum(pushes),outside_sink_heap_pops=native_pops-sum(pops),all_native_heap_work_attributed=native_pushes==sum(pushes) and native_pops==sum(pops),zero_heap_push_CIDs=sum(x==0 for x in pushes),iterations=v['iterations'],vectors=vectors);rows.append(summary);bindings[str(legacy)]=sha(legacy);print('CID HEAP WORK REPLAY PASS',case,arm,native_pushes,native_pops,summary['outside_sink_heap_pushes'],summary['outside_sink_heap_pops'],flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  with (out/'verification.json').open('x') as f:json.dump(dict(status='all6_actual_heap_snapshot_event_replays_and_CID_attributions_pass',bindings=bindings,rows=rows,scope='Measured native RouterStats heap deltas per explicit sink attempt, with complete CID zeros and explicit outside-call residual. Legacy full event sequence and input/output equivalence transfer existing physical CID/seed mapping. Heap operations are not elapsed time or independent causal costs; source/feedback/native/canonical full-flow and prior gates remain separate.'),f,indent=2)
 print('ALL6CID HEAP WORK REPLAYS PASS',flush=True)
if __name__=='__main__':main()
