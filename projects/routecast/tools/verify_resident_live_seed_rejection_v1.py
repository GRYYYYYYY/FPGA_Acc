"""Native process rejects premature seed import and controller disconnect before routing."""
import json,os,resource,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
from prepare_live_native_manifest_v1 import prepare
R=Path(__file__).resolve().parents[1];D=R/'experiments/native_resident_seed_rejection_v1_2026-10-10';D.mkdir();source=R/'experiments/sha_resident_live_seed_complete_workflow_v1_2026-10-10/cold';ep=source/'demand/sha1/endpoints.json';binary=R/'build/native_live_seed_service_v1_2026-10-10/sequence_vpr';arch=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml';graph=source/'rr/sha1/rr_graph.xml';bindings={str(p):sha(p) for p in [Path(__file__),ep,binary,arch,graph]};rows=[];resource.setrlimit(resource.RLIMIT_CORE,(0,0))
for mode in ['premature_seed','controller_EOF']:
 W=D/mode;W.mkdir()
 for name in ['design.blif','design.net','design.place']:shutil.copyfile(source/'rr/sha1'/name,W/name);bindings[str(W/name)]=sha(W/name)
 manifest=W/'queries.txt';prepare(ep,manifest);bindings[str(manifest)]=sha(manifest);r,w=os.pipe();a,b=os.pipe();env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(ROUTECAST_INPROCESS_QUERIES=str(manifest),ROUTECAST_INPROCESS_FLOORS=str(W/'unused.tsv'),ROUTECAST_LIVE_REQUEST_FD=str(r),ROUTECAST_LIVE_RESPONSE_FD=str(b));cmd=[str(binary),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full'];t=time.perf_counter()
 with (W/'native.log').open('w') as log:
  proc=subprocess.Popen(cmd,cwd=W,env=env,stdout=log,stderr=subprocess.STDOUT,pass_fds=(r,b));os.close(r);os.close(b)
  with os.fdopen(a) as reader:
   ready=reader.readline();assert ready.startswith('READY\t') and ready.rstrip().endswith('\t6273')
   if mode=='premature_seed':os.write(w,b'I missing_unaudited_seed.route\n')
   os.close(w);code=proc.wait(timeout=15)
 text=(W/'native.log').read_text();assert code!=0 and 'NET-aware seed imported' not in text and 'VPR succeeded' not in text and not (W/'output.route').exists();expected='seed handoff request' if mode=='premature_seed' else 'controller disconnected';assert expected in text
 rows.append(dict(case=mode,exit_code=code,seconds=time.perf_counter()-t,rejected_before_native_seed_import_and_routing=True));bindings[str(W/'native.log')]=sha(W/'native.log')
assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all2_reject_before_route_pass=True,scope='Same resident service binary, full current manifest preflight, two pre-search lifecycle failures. No full later-phase crash recovery or live budget-fallback exercise.'),indent=2)+'\n');print(rows)
