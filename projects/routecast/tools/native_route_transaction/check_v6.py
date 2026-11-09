"""Live-context producer handshake; no-op candidate and producer failure pilot."""
import json,sys,shutil,subprocess,os,re,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[2];out=R/'experiments/native_route_transaction_v6_2026-10-07';out.mkdir()
b=R/'experiments/native_resume_shared_cold_adder_step3_workflow_2026-10-07';base=b/'canonical';receipt=json.loads((b/'receipt.json').read_text());binary=R/'build/native_route_transaction_v6_2026-10-07/routecast_transaction_vpr'
rows=[]
for case in ('live_noop','producer_failure','tampered_identity'):
 w=out/case;w.mkdir()
 for name in ('design.blif','design.net','design.place','design.route'):shutil.copyfile(base/name,w/name)
 producer=w/'producer.py'
 producer.write_text('''#!/usr/bin/python3
import sys,json,hashlib,os
from pathlib import Path
stem=sys.argv[1];b=json.loads(Path(stem+'.binding.json').read_text())
def digest(p):return 'SHA256:'+hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert digest(stem+'.route')==b['export_route']
if os.environ['PILOT_CASE']=='producer_failure':sys.exit(7)
if os.environ['PILOT_CASE']=='tampered_identity':Path(stem+'.identity.jsonl').write_text('tampered')
assert digest(stem+'.identity.jsonl')==b['identity']
candidate=Path(os.environ['ROUTECAST_TX_CANDIDATE']);candidate.write_bytes(Path(stem+'.route').read_bytes())
fields={'epoch':str(b['epoch']),'next_epoch':str(b['epoch']+1),**{k:b[k] for k in ('graph','net','placement','architecture','parent_route')},'candidate':digest(candidate)}
Path(os.environ['ROUTECAST_TX_REQUEST']).write_text('ROUTECAST_NATIVE_TX_V1\\n'+'\\n'.join(k+' '+v for k,v in fields.items())+'\\nEND\\n')
''');producer.chmod(0o755)
 cmd=list(receipt['canonical']['command']);cmd[0]=str(binary)
 env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(ROUTECAST_TX_PRODUCER=str(producer),ROUTECAST_TX_EXPORT_PREFIX=str(w/'live'),ROUTECAST_TX_CANDIDATE=str(w/'candidate.route'),ROUTECAST_TX_REQUEST=str(w/'request.txt'),ROUTECAST_TX_PREFIX=str(w/'tx'),PILOT_CASE=case)
 start=time.monotonic()
 with (w/'run.log').open('w') as f:code=subprocess.run(cmd,cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=150).returncode
 elapsed=time.monotonic()-start;log=(w/'run.log').read_text();binding=json.loads((w/'live.binding.json').read_text())
 assert binding['epoch']==0 and sha(w/'design.route')==sha(base/'design.route')
 if case=='live_noop':
  assert code==0,(code,log[-2000:]);status=json.loads((w/'tx.attempt0.json').read_text());assert status['committed'] and status['epoch_after']==1
  assert (w/'candidate.route').read_bytes()==(w/'live.route').read_bytes()
  assert (w/'tx.attempt0.before.route').read_bytes()==(w/'tx.attempt0.after.route').read_bytes()
  assert float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1])==5.05896
 else:
  assert code!=0 and 'producer failed before import' in log,(case,code,log[-2000:]);assert not (w/'tx.attempt0.json').exists() and not (w/'candidate.route').exists()
 rows.append(dict(case=case,exit_code=code,wall_s=elapsed,files={str(p):sha(p) for p in w.iterdir() if p.is_file()}));print(case,code,elapsed,flush=True)
(out/'receipt.json').write_text(json.dumps(dict(rows=rows,binary_sha256=sha(binary),source_sha256=sha(__file__),scope='Live export/structured argv producer/no-op commit and fail-before-import pilot. Producer itself verifies exported identity; native request guard binds graph/NET/place/architecture/parent/candidate but does not authenticate arbitrary producer logic. Failure terminates process before import, not continued service recovery. No incremental search or speed claim.'),indent=2)+'\n')
