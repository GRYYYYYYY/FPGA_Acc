"""Exactly one same-binary repeat for all3current layouts; observational log path only relocated."""
import pathlib,json,hashlib,os,shutil,subprocess,time,resource,concurrent.futures
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def main():
 O=R/'experiments/mmc_current_layout_cold_repeat_v1_2026-10-19';O.mkdir(exist_ok=False);F=R/'experiments/mmc_prospective_pressure_protocol_v2_2026-10-19/protocol.json';f=json.loads(F.read_text());bindings={str(F):sha(F),str(pathlib.Path(__file__).resolve()):sha(pathlib.Path(__file__).resolve())};plans=[]
 for case in ['episode_01','episode_02','episode_03']:
  B=R/'experiments/mmc_prospective_pressure_native_v2_2026-10-19'/case;pp=B/'protocol.json';vp=B/'verification.json';p=json.loads(pp.read_text());v=json.loads(vp.read_text());assert v['all_native_physical_and_canonical_pass'];job=next(x for x in f['native_commands'] if x['episode']==case);cmd=p['commands']['cold'];assert cmd==job['argv'];assert job['environment_set']=={'ROUTECAST_NATIVE_OWNER_TRACE':str(B/'cold/owner_trace.tsv')};assert '--route' in cmd and not any('seed_file' in s for s in cmd)
  binary=pathlib.Path(cmd[0]);arch=pathlib.Path(cmd[1]);graph=pathlib.Path(cmd[cmd.index('--read_rr_graph')+1]);assert p['bindings'][str(binary)]==sha(binary) and p['bindings'][str(arch)]==sha(arch)
  for x in [pp,vp,binary,arch,graph]:bindings[str(x)]=sha(x)
  for name in ['design.blif','design.net','design.place','output.route','owner_trace.tsv','native.log']:
   x=B/'cold'/name;assert v['bindings'][str(x)]==sha(x);bindings[str(x)]=sha(x)
  plans.append(dict(case=case,reference=str(B/'cold'),command=cmd,environment_set={'ROUTECAST_NATIVE_OWNER_TRACE':str(O/case/'owner_trace.tsv')},environment_change='Logging-only owner output path relocated to private trial; all other ROUTECAST variables removed identically to original. Original routing source recovered exactly per bound binary proof.'))
 build=R/'build/native_owner_trace_cold_v1_2026-10-19/receipt.json';b=json.loads(build.read_text());assert b['read_only_hooks_original_routing_source_recovered_exactly'];assert all(sha(pathlib.Path(p['command'][0]))==b['binary_sha256'] for p in plans);bindings[str(build)]=sha(build)
 free=int(pathlib.Path('/sys/fs/cgroup/memory.max').read_text())-int(pathlib.Path('/sys/fs/cgroup/memory.current').read_text());assert free>=72*2**30
 write(O/'protocol.json',dict(cases=plans,bindings=bindings,replications_per_layout=1,parallel_workers=2,child_address_space_bytes=32*2**30,selection='All3current exposed development layouts, one repeat each fixed before new results, no retries.',acceptance='Exit/FULL/VPRsuccess; exact route and owner-trace bytes, exact all integer router work and present factors. Any mismatch retained, original labels and quality/QoR gates unchanged. Timings unmatched descriptive only.'))
 def run(plan):
  case=plan['case'];B=pathlib.Path(plan['reference']);D=O/case;D.mkdir()
  for name in ['design.blif','design.net','design.place']:shutil.copyfile(B/name,D/name);assert sha(D/name)==bindings[str(B/name)]
  env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(plan['environment_set']);start=time.perf_counter();print('CURRENT_REPEAT_START',case,flush=True)
  def limit():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30))
  with (D/'native.log').open('x') as log:
   child=subprocess.Popen(plan['command'],cwd=D,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit);ticks=pathlib.Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19];write(D/'live_process.json',dict(pid=child.pid,startticks=ticks,command=plan['command']));code=child.wait()
  elapsed=time.perf_counter()-start;text=(D/'native.log').read_text();row=dict(case=case,exit_status=code,native_seconds=elapsed,FULL_pass='Completed routing consistency check successfully.' in text,vpr_success='VPR succeeded' in text,route_bytes_equal=(D/'output.route').exists() and (D/'output.route').read_bytes()==(B/'output.route').read_bytes(),owner_trace_bytes_equal=(D/'owner_trace.tsv').exists() and sha(D/'owner_trace.tsv')==bindings[str(B/'owner_trace.tsv')],files={str(p):sha(p) for p in D.iterdir() if p.is_file() and p.name not in ['live_process.json','receipt.json']});write(D/'receipt.json',row);print('CURRENT_REPEAT_DONE',{k:v for k,v in row.items() if k!='files'},flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,plans))
 assert all(sha(pathlib.Path(p))==h for p,h in bindings.items());write(O/'results.json',dict(status='ALL3_FIXED_CURRENT_LAYOUT_REPETITIONS_TERMINAL',cases=rows,bindings=bindings,scope='One repeat per current layout, exact same binary/parameters/input bytes with private owner-log destination. Original labels, failed prediction/QoR gates and source state remain unchanged. No universal determinism or timing-gain claim.'))
if __name__=='__main__':main()
