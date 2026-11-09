"""Complete real-graph 64->128->64 corpus versus unchanged128 native reference."""
import json,os,re,shutil,subprocess,time
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];S=R/'experiments/sha_resident_work_profile_seed_complete_workflow_v1_2026-10-10';N=S/'seed/native/sha1';D=R/'experiments/native_width_mode_switch_v1_2026-10-10';D.mkdir();proof=json.loads((S/'verification.json').read_text());assert all(sha(p)==h for p,h in proof['bindings'].items());receipt=json.loads((N/'service_receipt.json').read_text());assert all(sha(p)==h for sec in ['bindings','files'] for p,h in receipt[sec].items());manifest=N/'queries.txt';groups=defaultdict(list)
for l in manifest.read_text().splitlines():
 x=l.split()
 if x[0]=='Q':groups[int(x[2])].append(int(x[1]))
assert len(groups)==2961 and sum(map(len,groups.values()))==6273
prices=[{},dict.fromkeys(range(91088),2**64-1),{}];weights=[0,50000000,50000000];bindings={str(p):sha(p) for p in [Path(__file__),S/'verification.json',N/'service_receipt.json',manifest]};rows=[];expected=[]
for mode,build in [('original128','native_live_seed_work_profile_v1_2026-10-10'),('adaptive','native_live_seed_adaptive_width_v1_2026-10-10')]:
 B=R/'build'/build;bp=B/'receipt.json';b=json.loads(bp.read_text());assert sha(B/'sequence_vpr')==b['binary_sha256'] and all(sha(p)==h for sec in ['bindings','source_sha256'] for p,h in b[sec].items());bindings[str(bp)]=sha(bp);bindings[str(B/'sequence_vpr')]=sha(B/'sequence_vpr');W=D/mode;W.mkdir()
 for name in ['design.blif','design.net','design.place']:shutil.copyfile(N/name,W/name);bindings[str(W/name)]=sha(W/name)
 cmd=receipt['command'].copy();cmd[0]=str(B/'sequence_vpr');r,w=os.pipe();a,bb=os.pipe();env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(ROUTECAST_INPROCESS_QUERIES=str(manifest),ROUTECAST_INPROCESS_FLOORS=str(W/'unused.tsv'),ROUTECAST_LIVE_REQUEST_FD=str(r),ROUTECAST_LIVE_RESPONSE_FD=str(bb));tick=time.perf_counter();responses=[]
 with (W/'native.log').open('w') as log,(W/'responses.jsonl').open('w') as capture:
  proc=subprocess.Popen(cmd,cwd=W,env=env,stdout=log,stderr=subprocess.STDOUT,pass_fds=(r,bb));os.close(r);os.close(bb)
  with os.fdopen(w,'w') as writer,os.fdopen(a,'r') as reader:
   assert reader.readline().rstrip()=='READY\t2961\t6273'
   for phase,(p,weight) in enumerate(zip(prices,weights)):
    writer.write(f'P {len(p)} {weight}\n'+''.join(f'{n} {v}\n' for n,v in p.items()));writer.flush();assert reader.readline().rstrip()==f'A\t{phase}'
    for net,cids in sorted(groups.items()):
     writer.write(f'S {net}\n');writer.flush();seen=set()
     for _ in cids:
      line=reader.readline().rstrip('\n');x=line.split();assert x[0]=='Q';cid,raw,count=map(int,x[1:4]);path=list(map(int,x[4:]));assert cid not in seen and count==len(path);seen.add(cid);record=dict(phase=phase,cid=cid,raw=raw,path=path);responses.append(record);capture.write(json.dumps(record)+'\n')
     assert seen==set(cids) and reader.readline().rstrip()==f'Z\t{net}\t{len(cids)}'
   writer.write('O\n');writer.flush();assert reader.readline().rstrip()=='DONE\t18819'
  code=proc.wait(timeout=30)
 assert code==0 and len(responses)==18819
 if mode=='original128':expected=responses
 else:assert responses==expected and (W/'output.route').read_bytes()==(D/'original128/output.route').read_bytes();widths=[int(m[1]) for m in re.finditer(r'ROUTECAST_WIDTH phase=\d+ bits=(\d+)',(W/'native.log').read_text())];assert widths==[64,64,128,64]
 rows.append(dict(mode=mode,exit_code=code,complete_response_paths=18819,seconds=time.perf_counter()-tick));bindings.update({str(p):sha(p) for p in [W/'native.log',W/'responses.jsonl',W/'output.route']});print(rows[-1],flush=True)
assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all18819_paths_and_raw_costs_equal_original128=True,all_actual_native_routes_byte_equal=True,observed_adaptive_widths=[64,64,128,64],scope='Complete3x6273 realgraph search corpus: zero prices, UINT64_MAX every node triggers128, then zero prices at feedbackweight returns64. Both forward/bidi and separate state/output ownership exercised. Controlled prices, no prospective feedback/accuracy or live budget transaction test.'),indent=2)+'\n')
