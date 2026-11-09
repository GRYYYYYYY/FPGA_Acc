"""Frozen all3 native import-only probes, no routing or success-case selection."""
import json,sys,shutil,subprocess,os,time,resource,concurrent.futures
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
E=R/'experiments';I=E/'prospective_external_family_native_utility_seed_inputs_v1_2026-10-19';D=E/'prospective_external_family_tree_delay_probe_v1_2026-10-19';B=R/'build/native_external_tree_delay_probe_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def limit():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def main():
 build=read(B/'receipt.json');assert all(sha(p)==h for p,h in build['bindings'].items()) and sha(build['binary'])==build['binary_sha256'];original=read(E/'prospective_external_family_native_shared_sink_native_v1_2026-10-19/protocol.json');D.mkdir(exist_ok=False);cases=[];bindings={str(B/'receipt.json'):sha(B/'receipt.json'),build['binary']:build['binary_sha256'],str(Path(__file__).resolve()):sha(__file__)}
 for old in original['cases']:
  if not old['case'].endswith('/cold'):continue
  case=old['case'].removesuffix('/cold');cmd=old['command'].copy();cmd[0]=build['binary'];seed=str(Path(old['output'])/'output.route');bindings[seed]=sha(seed);cases.append(dict(case=case,command=cmd,inputs=old['inputs'],seed=seed,directory=str(D/case)))
 assert len(cases)==3
 (D/'protocol.json').write_text(json.dumps(dict(cases=cases,bindings=bindings,policy='ALL3 import-only diagnostic; same current inputs/native options as original route. Explicit seed/probe env after ROUTECAST sanitation. Expected exit before native timing/search; no FULL/STA or utility success assertion. All failed cases retained.'),indent=2)+'\n')
 def run(c):
  out=Path(c['directory']);out.mkdir(parents=True);files={}
  for key,name in [('blif','design.blif'),('net','design.net'),('place','design.place')]:shutil.copyfile(c['inputs'][key],out/name);files[str(out/name)]=sha(out/name)
  shutil.copyfile(c['seed'],out/'seed.route');assert sha(out/'seed.route')==sha(c['seed']);files[str(out/'seed.route')]=sha(out/'seed.route');env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};sets=dict(ROUTECAST_NATIVE_SEED=str(out/'seed.route'),ROUTECAST_IMPORT_ONLY='1');env.update(sets);tick=time.perf_counter()
  with (out/'native.log').open('x') as log:code=subprocess.run(c['command'],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit).returncode
  text=(out/'native.log').read_text();row=dict(case=c['case'],exit_status=code,seconds=time.perf_counter()-tick,import_probe_marker_present='RC_IMPORT_ONLY_VERIFIED ' in text,router_search_completed='Successfully routed after ' in text,environment_set=sets,files={str(p):sha(p) for p in out.iterdir() if p.is_file()},source_input_files=files,native_FULL_canonical_STA_admitted=False)
  with (out/'receipt.json').open('x') as f:json.dump(row,f,indent=2)
  print(json.dumps({k:v for k,v in row.items() if k not in ['files','source_input_files','environment_set']}),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
 assert all(sha(p)==h for p,h in bindings.items());(D/'terminal.json').write_text(json.dumps(dict(status='ALL3_FROZEN_IMPORT_ONLY_PROBE_PROCESSES_TERMINAL',rows=rows,bindings=bindings),indent=2)+'\n')
if __name__=='__main__':main()
