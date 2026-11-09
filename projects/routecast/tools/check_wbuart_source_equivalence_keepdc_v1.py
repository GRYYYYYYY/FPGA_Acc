"""Time-bounded no-reset-assumption Yosys-model equivalence experiment."""
import datetime,hashlib,json,os,resource,signal,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];S=R/'experiments/wbuart_source_candidate_v2_2026-10-20';M=R/'experiments/wbuart_boolean_cut_keepdc_v1_2026-10-20';O=R/'experiments/wbuart_source_equivalence_keepdc_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):
 with (O/n).open('x') as f:json.dump(d,f,indent=2);f.write('\n')
def main():
 O.mkdir(exist_ok=False)
 proof=R/'experiments/wbuart_cut_keepdc_projection_audit_v2_2026-10-20/verification.json';assert json.loads(proof.read_text())['status']=='ARBITRARY_UNDRIVEN_DOMAIN_PROJECTION_AND_MAPPING_CEC_PASS'
 files=[S/'upstream/rtl'/n for n in json.loads((S/'hierarchy_fileset_verification_v1.json').read_text())['files']]
 tool=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';lib=R/'experiments/prospective_external_family_runtime_v1_2026-10-18/tcl-root/usr/lib/x86_64-linux-gnu'
 commands=['read_verilog '+' '.join(str(p) for p in files),'hierarchy -check -top wbuart','proc','flatten','memory_map','opt','hierarchy -top wbuart','splitnets -ports','rename wbuart gold','design -stash gold_store','read_blif '+str(M/'design.blif'),'hierarchy -check -top wbuart','splitnets -ports','rename wbuart gate','design -stash gate_store','design -copy-from gold_store -as gold gold','design -copy-from gate_store -as gate gate','equiv_make gold gate equiv','hierarchy -top equiv','equiv_simple -undef -seq 2','equiv_induct -undef -seq 2','equiv_status -assert']
 (O/'commands.ys').write_text('\n'.join(commands)+'\n');bindings={str(p):sha(p) for p in [*files,M/'design.blif',tool,lib/'libtcl8.6.so',proof,Path(__file__),O/'commands.ys']}
 save('protocol.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commands':commands,'bindings':bindings,'timeout_seconds':120,'AS_limit_bytes':8*2**30,'assumptions':'No added reset or input constraints. Pinned Yosys parsed/process/memory-lowered semantics and undef-aware induction only. Not independent HDL four-state proof.','policy':'Single fixed bounded proof, retain failure/timeout. No outcome-driven source/parameter change.'})
 env=os.environ.copy();env['LD_LIBRARY_PATH']=str(lib)+':'+env.get('LD_LIBRARY_PATH','')
 def limits():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
 start=time.perf_counter();timeout=False
 with (O/'proof.log').open('x') as log:
  p=subprocess.Popen([str(tool),'-Q','-T','-s',str(O/'commands.ys')],cwd=O,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,preexec_fn=limits)
  stat=Path(f'/proc/{p.pid}/stat').read_text().rsplit(') ',1)[1].split();save('live_process.json',{'pid':p.pid,'start_ticks':stat[19]});print('WBUART_EQUIV_CHILD',p.pid,flush=True)
  try:rc=p.wait(timeout=120)
  except subprocess.TimeoutExpired:
   timeout=True;os.killpg(p.pid,signal.SIGTERM);rc=p.wait()
 text=(O/'proof.log').read_text();passed=rc==0 and 'Equivalence successfully proven' in text
 for n,h in bindings.items():assert sha(Path(n))==h
 save('verification.json',{'status':'YOSYS_MODEL_EQUIVALENCE_PASS' if passed else 'YOSYS_MODEL_EQUIVALENCE_UNPROVEN','exit_status':rc,'timeout':timeout,'seconds':time.perf_counter()-start,'equivalence_proven':passed,'full_original_HDL_four_state_certificate':False,'strict_unseen_admitted':False,'new_placement_route_jobs':False,'bindings':{'protocol.json':sha(O/'protocol.json'),'proof.log':sha(O/'proof.log')}});print('WBUART_EQUIV_TERMINAL',rc,passed,timeout,flush=True)
if __name__=='__main__':main()
