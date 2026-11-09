"""Early identity byte parity against six genuine post-routing packed states."""
import json,sys,shutil,subprocess,os,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
out=R/'experiments/native_identity_only_v2_2026-10-07';out.mkdir();binary=R/'build/native_net_identity_only_v2_2026-10-07/routecast_net_identity_vpr';rows=[];inputs={str(binary):sha(binary),str(Path(__file__)):sha(__file__)}
for mode in ('workflow','cold'):
 for i in (1,2,3):
  base=R/f'experiments/native_resume_postroute_batch_integrated_adder_step{i}_{mode}_2026-10-07';r=json.loads((base/'receipt.json').read_text());reference=base/'canonical/identity.jsonl';w=out/f'{mode}_{i}';w.mkdir()
  for name in ('design.blif','design.net','design.place'):shutil.copyfile(base/'canonical'/name,w/name)
  cmd=r['canonical']['command'].copy();cmd[0]=str(binary);cmd[cmd.index('--route_file')+1]='missing.route';table=w/'identity.jsonl';env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_NET_IDENTITY_FILE']=str(table);env['ROUTECAST_IDENTITY_ONLY']='1';start=time.perf_counter()
  with (w/'run.log').open('w') as f:code=subprocess.run(cmd,cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
  elapsed=time.perf_counter()-start;assert code==1 and table.exists(),(mode,i,code,(w/'run.log').read_text()[-2000:]);assert table.read_bytes()==reference.read_bytes();phase=json.loads(Path(str(table)+'.phase.json').read_text());assert phase['phase']=='after_placement_before_route_import' and phase['rr_graph_skipped'];log=(w/'run.log').read_text();assert 'Begin loading FPGA routing file' not in log
  inputs[str(reference)]=sha(reference);rows.append(dict(mode=mode,index=i,wall_s=elapsed,identity_bytes_equal=True,phase=phase,command=cmd,files={str(p):sha(p) for p in w.iterdir() if p.is_file()}));print(mode,i,elapsed,flush=True)
assert all(sha(p)==h for p,h in inputs.items());(out/'receipt.json').write_text(json.dumps(dict(rows=rows,inputs=inputs,scope='Six distinct actual post-routing packed NET states; identity exported after placement with RR graph loading skipped exactly equals original after-RR native identity bytes. No routing execution or timing proof replaced; early successful capture intentionally exits1 before missing.route read.'),indent=2)+'\n')
