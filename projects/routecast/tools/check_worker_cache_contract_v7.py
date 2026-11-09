"""Real graph FIFO, deadline non-publication, identity, and close contracts."""
import json,sys,time,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from remaining_delay_worker_cache_v7 import RemainingDelayCache
base=R/'experiments/bound_local_cost_v6_2026-10-07';ep=R/'experiments/mcnc_prospective_v1_2026-10-07/dsip/endpoints.json';out=R/'experiments/worker_cache_contract_v7_2026-10-07';out.mkdir();binary=R/'build/capped_bound_worker_cpp_v2_2026-10-07/compute';source=R/'tools/capped_bound_worker_cpp_v2/main.cpp';vp=base/'verification.json';v=json.loads(vp.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());cp=base/'0_old_cache.json';c=json.loads(cp.read_text());events=c['events'][:3];bindings={**closure([Path(__file__)]),str(ep):sha(ep),str(cp):sha(cp),str(vp):sha(vp),str(binary):sha(binary),str(source):sha(source)};bindings.update({r['path']:r['sha256'] for r in json.loads(ep.read_text())['inputs'].values()})
fixture=out/'partial_worker.py';fixture.write_text('#!/usr/bin/env python3\nimport sys,struct,time\nf=open(sys.argv[1],"rb");magic,n,m=struct.unpack("<3Q",f.read(24));cap=int(sys.argv[2]);sys.stdout.buffer.write(struct.pack("<3Q",2026100710,n,cap));sys.stdout.buffer.flush()\nsink=int(sys.stdin.readline());sys.stdout.buffer.write(struct.pack("<3Q",sink,n,0));sys.stdout.buffer.flush();time.sleep(30)\n');fixture.chmod(0o700);bindings[str(fixture)]=sha(fixture)
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Real dsip graph isolated contract. FIFO2 with reload, full byte parity, pre-expired request, deliberate partial response, model identity replacement, graph mutation and close rejection. Not performance or full routing evidence.'))+'\n')
graph,digest,nodes,f,rc,queries=load_endpoints(ep);cache=RemainingDelayCache(graph,digest,f,rc,out/'fifo',max_entries=2)
try:
 for e in events:
  data=cache.get(e['sink']);assert data.values.tobytes()==Path(e['path']).read_bytes()
 assert events[0]['sink'] not in cache.entries
 assert cache.get(events[1]['sink']) is cache.entries[events[1]['sink']]
 assert list(cache.entries)==[events[1]['sink'],events[2]['sink']]
 cache.get(events[0]['sink']);assert list(cache.entries)==[events[2]['sink'],events[0]['sink']]
 before=len(cache.events)
 try:cache.get(events[2]['sink'],deadline=time.perf_counter()-1)
 except TimeoutError:pass
 else:raise AssertionError('expired hit accepted')
 assert len(cache.events)==before;cache.finalize();assert cache.worker.closed and cache.summary()['closed'] and cache.hits==1 and cache.evictions==2 and cache.misses==4
 try:cache.get(events[0]['sink'])
 except ValueError:pass
 else:raise AssertionError('closed request accepted')
 assert not cache.summary()['invalid']
finally:
 if not cache._closed:cache.abort()
partial=RemainingDelayCache(graph,digest,f,rc,out/'partial',binary=fixture)
try:
 try:partial.get(events[0]['sink'],deadline=time.perf_counter()+0.1)
 except TimeoutError:pass
 else:raise AssertionError('partial published')
 assert not partial.events and not partial.entries and partial.aborted==1 and partial.worker.closed and partial.worker.process.poll() is not None
 partial.finalize();assert partial.close_proof and partial._closed
finally:
 if not partial._closed:partial.abort()
model=RemainingDelayCache(graph,digest,f,rc,out/'model')
try:
 model.rc.increments=tuple(list(model.rc.increments))
 try:model.get(events[0]['sink'])
 except ValueError:pass
 else:raise AssertionError('replaced model accepted')
 assert model._invalid and model.worker.closed
finally:model.abort()
copygraph=out/'graph_copy.xml';shutil.copyfile(graph,copygraph);mutated=RemainingDelayCache(copygraph,digest,f,rc,out/'graph')
try:
 with copygraph.open('ab') as stream:stream.write(b'\n')
 try:mutated.get(events[0]['sink'])
 except ValueError:pass
 else:raise AssertionError('changed graph accepted')
 assert mutated._invalid and mutated.worker.closed and not mutated.events
finally:mutated.abort()
assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),fifo2_reload_and_hit_order_pass=True,three_real_bounds_exact=True,expired_hit_nonpublication_pass=True,partial_timeout_nonpublication_and_reaping_pass=True,model_and_graph_change_rejected=True,mandatory_close_and_closed_rejection_pass=True,bindings=bindings),indent=2)+'\n');print('PASS real worker cache FIFO/deadline/identity/close',flush=True)
