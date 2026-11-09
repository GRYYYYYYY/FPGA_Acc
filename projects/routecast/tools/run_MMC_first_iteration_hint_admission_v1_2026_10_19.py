"""Frozen episode01 semantic pilot; no utility case admission or tuning."""
import pathlib,json,hashlib,shutil,os,subprocess,time,resource,concurrent.futures
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 O=R/'experiments/mmc_first_iteration_hint_admission_v1_2026-10-19';O.mkdir(exist_ok=False);B=R/'build/native_first_iteration_hint_v1_2026-10-19';bp=B/'receipt.json';b=json.loads(bp.read_text());assert b['strip_additions_recovers_bound_base_source_exactly'] and sha(B/'sequence_vpr')==b['binary_sha256'];P=R/'experiments/mmc_first_iteration_forecast_hint_protocol_v1_2026-10-19/protocol.json';p=json.loads(P.read_text())
 for doc in [p,b]:
  for f,h in doc['bindings'].items():assert sha(pathlib.Path(f))==h
 source=R/'experiments/mmc_native_excess_utility_v1_2026-10-19/episode_01/zero';sp=source/'protocol.json';s=json.loads(sp.read_text());vp=source/'verification.json';v=json.loads(vp.read_text());assert v['all_native_physical_and_canonical_pass'];cmd=s['commands']['cold'].copy();cmd[0]=str(B/'sequence_vpr');graph=pathlib.Path(cmd[cmd.index('--read_rr_graph')+1]);bindings={str(f):sha(f) for f in [P,bp,B/'sequence_vpr',sp,vp,graph,pathlib.Path(cmd[1]),pathlib.Path(__file__).resolve()]}
 for name in ['design.blif','design.net','design.place','output.route','native.log','design.net.post_routing']:
  f=source/'cold'/name;assert v['bindings'][str(f)]==sha(f);bindings[str(f)]=sha(f)
 plans=[]
 for arm in ['absent','zero','hint']:
  D=O/arm;env={'ROUTECAST_NATIVE_OWNER_TRACE':str(D/'owner_trace.tsv')}
  if arm!='absent':env.update(ROUTECAST_FIRST_ITERATION_HINT='1',ROUTECAST_EXCESS_PRELOAD=p['zero_input'] if arm=='zero' else p['cases'][0]['risk'],ROUTECAST_EXCESS_GRAPH_SHA256=sha(graph),ROUTECAST_EXCESS_STATE_DUMP=str(D/'initial.bin'),ROUTECAST_HINT_EXPIRY_BEFORE_DUMP=str(D/'before.bin'),ROUTECAST_HINT_EXPIRY_AFTER_DUMP=str(D/'after.bin'))
  plans.append(dict(arm=arm,command=cmd,environment_set=env))
 write(O/'protocol.json',dict(bindings=bindings,case='episode_01',arms=plans,parallel_workers=2,child_address_space_limit_bytes=32*2**30,reference_zero=str(source/'cold'),positive_reference=str(R/'experiments/mmc_native_excess_utility_v1_2026-10-19/episode_01/forecast/cold'),scope='Semantic admission only: all3 pilot arms fixed before native results; no work/quality tuning, performance acceptance, reference replacement or full-cohort utility claim. Original all3 utility study remains gated on independent semantic proof.'))
 assert int(pathlib.Path('/sys/fs/cgroup/memory.max').read_text())-int(pathlib.Path('/sys/fs/cgroup/memory.current').read_text())>=72*2**30
 def run(plan):
  D=O/plan['arm'];D.mkdir()
  for name in ['design.blif','design.net','design.place']:shutil.copyfile(source/'cold'/name,D/name);assert sha(D/name)==bindings[str(source/'cold'/name)]
  env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(plan['environment_set']);t=time.perf_counter();print('HINT_ADMISSION_NATIVE_START',plan['arm'],flush=True)
  def limit():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30))
  with (D/'native.log').open('x') as log:
   child=subprocess.Popen(plan['command'],cwd=D,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit);write(D/'live_process.json',dict(pid=child.pid,startticks=pathlib.Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19],command=plan['command']));code=child.wait()
  text=(D/'native.log').read_text();row=dict(arm=plan['arm'],exit_status=code,seconds=time.perf_counter()-t,FULL_pass='Completed routing consistency check successfully.' in text,VPR_success='VPR succeeded' in text,files={str(f):sha(f) for f in D.iterdir() if f.is_file() and f.name!='live_process.json'});write(D/'receipt.json',row);print('HINT_ADMISSION_NATIVE_DONE',{k:v for k,v in row.items() if k!='files'},flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,plans))
 assert all(sha(pathlib.Path(f))==h for f,h in bindings.items());write(O/'results.json',dict(status='ALL3_SEMANTIC_PILOT_NATIVE_ARMS_TERMINAL',rows=rows,bindings=bindings,independent_semantic_verification_pending=True))
if __name__=='__main__':main()
