import json,os,shutil,subprocess,re
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_candidate_sequence_2026-10-06';out.mkdir();work=root/'work/native_candidate_sequence_2026-10-06';work.mkdir()
parent=root/'experiments/native_scoped_sync_next_move_2026-10-06';v=json.loads((parent/'verification.json').read_text());assert all(sha(f)==h for f,h in v['sha256'].items())
command=json.loads((parent/'accept_next/command.json').read_text());source=Path(command['cwd']);cmd=command['command'];cmd[0]=str(root/'build/native_candidate_sequence_2026-10-06/sequence_vpr');graph=cmd[cmd.index('--read_rr_graph')+1];results=[]
for sequence in ('A','AR','AA','ARA','ARR','AAAR'):
 cwd=work/sequence;cwd.mkdir();case=out/sequence;case.mkdir()
 for name in ('design.blif','design.net','design.place','seed.route'):shutil.copyfile(source/name,cwd/name)
 inputs={str(f):sha(f) for f in cwd.iterdir()};env=os.environ.copy();env.update(ROUTECAST_NATIVE_SEED=str(cwd/'seed.route'),ROUTECAST_TIMING_RESTORE_PROBE='1',ROUTECAST_MOVE_SEQUENCE=sequence);env.pop('ROUTECAST_SYNC_TICKET_FAULT',None)
 with (case/'run.log').open('w') as f:code=subprocess.run(cmd,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
 assert all(sha(f)==h for f,h in inputs.items());result={'sequence':sequence,'exit_code':code,'inputs_sha256':inputs,'log_sha256':sha(case/'run.log')}
 if code==0:
  log=(case/'run.log').read_text();assert len(re.findall('ROUTECAST sequence step=',log))==len(sequence)
  for path in [cwd/'output.route',*sorted(cwd.glob('candidate_*.route'))]:
   a=audit(graph,path);assert len(a['connections'])==129 and a['overflow_units']==0;(case/(path.stem+'_audit.json')).write_text(json.dumps(a,indent=2)+'\n')
  result.update(route_sha256=sha(cwd/'output.route'),packed_sha256=sha(cwd/'design.net.post_routing'),cpd_ns=float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[1]))
  assert 'Placement_ID: SHA256:'+sha(cwd/'accepted.place') in (cwd/'output.route').read_text().splitlines()[0]
 results.append(result);print(sequence,code,flush=True)
(out/'receipt.json').write_text(json.dumps({'results':results,'command':cmd,'binary_sha256':sha(cmd[0]),'scope':'Actual serial candidate moves and packing sync/STA in same native process, fixed pair; external reconstruction not used between steps.'},indent=2)+'\n')
