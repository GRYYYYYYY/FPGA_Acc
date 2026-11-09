"""Real graph response parity and transport timeout fixture."""
import json,sys,time,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from capped_bound_worker_client_v1 import BoundWorker
from pre_route_endpoints import sha
from source_binding_v2 import closure
base=R/'experiments/bound_local_cost_v6_2026-10-07';out=R/'experiments/capped_bound_worker_contract_v1_2026-10-07';out.mkdir();binary=R/'build/capped_bound_worker_cpp_v2_2026-10-07/compute';source=R/'tools/capped_bound_worker_cpp_v2/main.cpp';gf=base/'certificate_graph.bin';cp=base/'0_old_cache.json';c=json.loads(cp.read_text());vp=base/'verification.json';v=json.loads(vp.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());bindings={**closure([Path(__file__)]),str(binary):sha(binary),str(source):sha(source),str(gf):sha(gf),str(cp):sha(cp),str(vp):sha(vp)};n=c['retained_distance_bytes']//178//8
fixture=out/'partial_worker.py';fixture.write_text('#!/usr/bin/env python3\nimport sys,struct,time\nsys.stdout.buffer.write(struct.pack("<3Q",2026100710,2,1));sys.stdout.buffer.flush()\nsink=int(sys.stdin.readline());sys.stdout.buffer.write(struct.pack("<3Q",sink,2,0));sys.stdout.buffer.flush();time.sleep(30)\n');fixture.chmod(0o700);bindings[str(fixture)]=sha(fixture)
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='178 on-demand real graph frames, repeated request, expired-before-send and partial-response transport fixture. No FIFO/session integration, graph conversion paid accounting, full routing or end-to-end claim.'))+'\n')
start=time.perf_counter();worker=BoundWorker(binary,gf,n,c['cutoff_integer'])
try:
 for event in c['events']:
  data=worker.get(event['sink'],deadline=time.perf_counter()+30);assert len(data)==n*8 and data==Path(event['path']).read_bytes();bindings[event['path']]=event['sha256']
 try:worker.get(c['events'][0]['sink'],deadline=time.perf_counter()-1)
 except TimeoutError:pass
 else:raise AssertionError('expired request accepted')
 assert not worker.closed
 assert worker.get(c['events'][0]['sink'],deadline=time.perf_counter()+30)==Path(c['events'][0]['path']).read_bytes()
finally:worker.close()
elapsed=time.perf_counter()-start;assert worker.process.returncode==0
partial=BoundWorker(fixture,gf,2,1)
try:partial.get(0,deadline=time.perf_counter()+0.1)
except TimeoutError:pass
else:raise AssertionError('partial response returned')
assert partial.closed and partial.process.poll() is not None
assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),all178_response_bytes_exact=True,repeated_request_exact=True,expired_before_send_preserves_worker=True,partial_response_timeout_kills_and_reaps=True,real_worker_close_exit0=True,diagnostic_elapsed_including_reference_reads_seconds=elapsed,bindings=bindings),indent=2)+'\n');print('PASS178 real requests and timeout/close transport',elapsed,flush=True)
