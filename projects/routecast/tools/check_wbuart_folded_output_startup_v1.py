"""Single folded-output startup obligation under a stated defined Boolean domain."""
import hashlib,json,os,resource,signal,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/wbuart_source_equivalence_v1_2026-10-20';O=R/'experiments/wbuart_folded_output_startup_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):
 with (O/n).open('x') as f:json.dump(d,f,indent=2);f.write('\n')
def main():
 O.mkdir(exist_ok=False);old=json.loads((P/'protocol.json').read_text());commands=old['commands'];prefix=commands[:commands.index('rename wbuart gold')];commands=prefix+['dffunmap','techmap','opt_clean','write_json '+str(O/'gold.json'),'sat -seq 2 -set-init-def -set-def-inputs -prove o_wb_data[31] 0 -prove-skip 1 -verify -show o_wb_data[31]'];(O/'commands.ys').write_text('\n'.join(commands)+'\n')
 tool=Path(next(p for p in old['bindings'] if p.endswith('/bin/yosys')));bindings={p:h for p,h in old['bindings'].items() if '/upstream/rtl/' in p or p.endswith('/bin/yosys') or p.endswith('/libtcl8.6.so')};bindings.update({str(p):sha(p) for p in [Path(__file__),O/'commands.ys',P/'protocol.json']})
 for n,h in bindings.items():assert sha(Path(n))==h
 save('protocol.json',{'commands':commands,'bindings':bindings,'timeout_seconds':60,'scope':'Only o_wb_data[31] after one rising edge; all initial registers defined with upstream explicit initial constraints retained, defined inputs at every step, no reset forcing. Frame1 pre-edge output is deliberately not claimed equal. No overall startup/full-HDL/family/physical qualification.'})
 env=os.environ.copy();env['LD_LIBRARY_PATH']=str(R/'experiments/prospective_external_family_runtime_v1_2026-10-18/tcl-root/usr/lib/x86_64-linux-gnu')+':'+env.get('LD_LIBRARY_PATH','');start=time.perf_counter();timeout=False
 def limit():resource.setrlimit(resource.RLIMIT_AS,(4*2**30,4*2**30))
 with (O/'proof.log').open('x') as f:
  child=subprocess.Popen([str(tool),'-Q','-T','-s',str(O/'commands.ys')],cwd=O,env=env,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limit,start_new_session=True)
  try:rc=child.wait(timeout=60)
  except subprocess.TimeoutExpired:timeout=True;os.killpg(child.pid,signal.SIGTERM);rc=child.wait()
 text=(O/'proof.log').read_text();passed=rc==0 and 'SAT proof finished - no model found: SUCCESS!' in text
 save('verification.json',{'status':'FOLDED_OUTPUT_POST_FIRST_EDGE_DEFINED_DOMAIN_PASS' if passed else 'FOLDED_OUTPUT_POST_FIRST_EDGE_UNPROVEN','passed':passed,'exit_status':rc,'timeout':timeout,'seconds':time.perf_counter()-start,'strict_initial_four_state_equivalence':False,'physical_input_admitted':False,'bindings':{p.name:sha(p) for p in O.iterdir() if p.is_file()}});print('FOLDED_OUTPUT_STARTUP',rc,passed,flush=True)
if __name__=='__main__':main()
