"""Same-binary complete certified live-search corpus; no prospective price decisions."""
import json,os,re,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];S=R/'experiments/sha_resident_cpu_profile_seed_complete_workflow_v1_2026-10-10';N=S/'seed/native/sha1';D=R/'experiments/native_cpu_profile_matched_replay_v1_2026-10-10';D.mkdir();bindings={}
for name in ['verification.json','wire_transaction_verification.json','handoff_parity_verification.json']:
 p=S/name;v=json.loads(p.read_text());assert all(sha(q)==h for q,h in v['bindings'].items());bindings[str(p)]=sha(p)
wirefile=N/'wire.jsonl';wire=[json.loads(l) for l in wirefile.read_text().splitlines()];sr=json.loads((N/'service_receipt.json').read_text());assert len(sr['calls'])==7459 and all(sha(q)==h for sec in ['bindings','files'] for q,h in sr[sec].items());bindings.update({str(p):sha(p) for p in [Path(__file__),wirefile,N/'queries.txt',N/'seed.route',N/'output.route']});builds={}
for mode,root in [('C','native_live_seed_cpu_profile_v1_2026-10-10')]:
 B=R/'build'/root;v=json.loads((B/'receipt.json').read_text());assert sha(B/'sequence_vpr')==v['binary_sha256'] and all(sha(p)==h for sec in ['bindings','source_sha256'] for p,h in v[sec].items());builds[mode]=B/'sequence_vpr';bindings[str(B/'receipt.json')]=sha(B/'receipt.json');bindings[str(B/'sequence_vpr')]=sha(B/'sequence_vpr')
order=['C','C'];(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,order=order,scope='Archived complete certified current search request/price transcript and audited seed, identical current graph/input/options/manifest for both binaries. Every returned line exact versus certified transcript; all actual route bytes compared. Balanced sequential Same-binary two simplified-controller repeats; controlled kernel/API experiment, not prospective new feedback or full workflow/heldout gain.'),indent=2)+'\n');rows=[]
for index,mode in enumerate(order):
 W=D/f'{index}_{mode}';W.mkdir()
 for name in ['design.blif','design.net','design.place']:shutil.copyfile(N/name,W/name);bindings[str(W/name)]=sha(W/name)
 r,w=os.pipe();a,b=os.pipe();cmd=sr['command'].copy();cmd[0]=str(builds[mode]);env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(ROUTECAST_INPROCESS_QUERIES=str(N/'queries.txt'),ROUTECAST_INPROCESS_FLOORS=str(W/'unused.tsv'),ROUTECAST_LIVE_REQUEST_FD=str(r),ROUTECAST_LIVE_RESPONSE_FD=str(b));tick=time.perf_counter();count=0
 with (W/'native.log').open('w') as log:
  proc=subprocess.Popen(cmd,cwd=W,env=env,stdout=log,stderr=subprocess.STDOUT,pass_fds=(r,b));os.close(r);os.close(b)
  with os.fdopen(w,'w') as writer,os.fdopen(a,'r') as reader:
   for event in wire:
    if 'send' in event:writer.write(event['send']);writer.flush()
    else:
     observed=reader.readline().rstrip('\n');assert observed==event['receive'],(index,count,observed,event['receive']);count+=1
  code=proc.wait(timeout=30)
 assert code==0 and (W/'output.route').read_bytes()==(N/'output.route').read_bytes();text=(W/'native.log').read_text();assert 'VPR succeeded' in text;kernel=sum(float(m[1]) for m in re.finditer(r'ROUTECAST_PROFILE phase=\d+ bidi=\d+ forward=\d+ kernel=([0-9.]+)',text));assert kernel>0
 row=dict(index=index,variant=mode,exit_code=code,matched_receive_lines=count,native_with_replay_seconds=time.perf_counter()-tick,native_kernel_seconds=kernel,all_response_lines_and_native_route_bytes_equal=True);rows.append(row);(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');bindings.update({str(p):sha(p) for p in [W/'native.log',W/'output.route']});print(row,flush=True)
assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all2_complete_corpus_replays_pass=True,scope='Same-binary CPU/wall corpus only, entire7459request/17176path response sequence each run. Archived prices/seed, no independent dynamic prospective utility claim or full workflow timing.'),indent=2)+'\n')
