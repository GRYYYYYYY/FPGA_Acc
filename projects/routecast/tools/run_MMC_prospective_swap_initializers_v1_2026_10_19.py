"""Fixed pre-label initialization and independent audits, sequential resource use."""
import json,sys,subprocess,hashlib,resource,os
from pathlib import Path
R=Path(__file__).resolve().parents[1]
I=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19'
O=R/'experiments/mmc_prospective_swap_initializers_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2)
scripts=['run_mmc_multiplacement_initializers_v1_2026_10_18.py','verify_mmc_multiplacement_raw_floor_xml_v1_2026_10_18.py','verify_mmc_multiplacement_initializers_v1_2026_10_18.py']
proof=I/'verification.json';v=json.loads(proof.read_text());assert v['status']=='three_predictor_input_adapters_verified'
for p,h in v['bindings'].items():assert sha(p)==h,p
bindings={str(proof):sha(proof),str(Path(__file__).resolve()):sha(__file__)}
for s in scripts:bindings[str(R/'tools'/s)]=sha(R/'tools'/s)
O.mkdir(); commands=[]
for i in range(1,4):
 name=f'episode_{i:02d}';d=O/name;d.mkdir()
 protocol=dict(bindings=bindings,episode=name,policy='Unmodified V2 raw_min and native_retained initializers; no feedback tuning',labels_read=False,timing_scope='Correctness production and independent audits; no complete-flow speed claim',strict_unseen_family_admitted=False)
 write(d/'protocol.json',protocol)
 for s in scripts:commands.append(dict(episode=name,argv=[sys.executable,str(R/'tools'/s),str(I/name),str(d)],log=str(d/(s+'.log'))))
write(O/'protocol.json',dict(bindings=bindings,commands=commands,max_concurrency=1,child_address_space_limit_bytes=32*2**30,native_target_route_jobs=0,predictor_policy_frozen_before_new_labels=True,scope='Input-only known-MMC new-layout prospective production. No target route read. Outcome/evaluation protocol remains pending.'))
def limits():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
rows=[]
for c in commands:
 print('START',c['episode'],Path(c['argv'][1]).name,flush=True)
 with Path(c['log']).open('x') as f:code=subprocess.run(c['argv'],cwd=R,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limits).returncode
 row=dict(episode=c['episode'],script=Path(c['argv'][1]).name,exit_code=code);rows.append(row)
 tmp=O/'stages.tmp';tmp.write_text(json.dumps(rows,indent=2));os.replace(tmp,O/'stages.json')
 print('TERMINAL',row,flush=True)
 if code:
  write(O/'terminal.json',dict(status='FAILED',rows=rows));raise SystemExit(code)
write(O/'terminal.json',dict(status='ALL_THREE_INITIALIZERS_AND_INDEPENDENT_AUDITS_PASS',rows=rows,native_target_routes_generated=False,quality_and_full_workflow_gates_pending=True))
