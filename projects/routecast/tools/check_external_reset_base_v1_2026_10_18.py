"""Distinct reset-base lemma; preserve ongoing unconstrained proof process."""
import hashlib,json,os,resource,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 parent=R/'experiments/prospective_external_family_source_equivalence_v1_2026-10-18';pp=parent/'protocol.json';p=json.loads(pp.read_text());out=R/'experiments/prospective_external_family_reset_base_v1_2026-10-18';out.mkdir(exist_ok=False)
 for name,h in p['bindings'].items():assert sha(name)==h
 sv=json.loads((R/'experiments/prospective_external_family_source_v2_2026-10-18/source_verification.json').read_text());tool=Path(sv['yosys_path']);runtime=R/'experiments/prospective_external_family_runtime_v1_2026-10-18';env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime/'tcl-root/usr/lib/x86_64-linux-gnu')+(os.pathsep+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
 docs=subprocess.check_output([str(tool),'-Q','-T','-p','help equiv_induct; help equiv_miter; help sat'],env=env,text=True)
 with (out/'tool_semantics.txt').open('x') as f:f.write(docs)
 prefix=p['commands'][:p['commands'].index('equiv_simple -undef')];prefix+=['equiv_miter -assert -undef base_miter','hierarchy -top base_miter','flatten','opt_clean','write_json "'+str(out/'miter.json')+'"']
 with (out/'build.ys').open('x') as f:f.write('\n'.join(prefix)+'\n')
 bindings={**p['bindings'],str(pp):sha(pp),str(Path(__file__)):sha(__file__)}
 with (out/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,miter_commands=prefix,reset_base_assumptions='Three abstract positive-edge frames with reset_n=0 and all primary input bits defined. FF initial values are arbitrary defined values, not assumed equal between the two designs. Assert all generated equivalence observation points on frames2and3. Undef-aware comparison semantics remain those of the pinned tool.',main_proof_process_preserved=dict(pid=990092,session=73780),scope='Auxiliary initial-synchronization lemma only. Does not replace the ongoing unrestricted direct/inductive run, prove arbitrary reset/clock waveforms or full original HDL/four-state semantics. No native target labels.'),f,indent=2)
 with (out/'build.log').open('x') as log:code=subprocess.call([str(tool),'-Q','-T','-s',str(out/'build.ys')],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT)
 assert code==0;m=json.loads((out/'miter.json').read_text())['modules']['base_miter'];nassert=sum(c['type']=='$assert' for c in m['cells'].values());assert nassert>0 and 'reset_n' in m['ports'] and len(m['ports']['reset_n']['bits'])==1
 sat='read_json "'+str(out/'miter.json')+'"\nhierarchy -top base_miter\nsat -seq 3 -enable_undef -set-def-inputs -set-init-def -set reset_n 0 -prove-asserts -prove-skip 1 -verify\n'
 with (out/'prove.ys').open('x') as f:f.write(sat)
 def limits():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
 tick=time.perf_counter()
 with (out/'prove.log').open('x') as log:
  child=subprocess.Popen([str(tool),'-Q','-T','-s',str(out/'prove.ys')],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits)
  with (out/'live_process.json').open('x') as f:json.dump(dict(pid=child.pid,assertion_points=nassert),f)
  print('RESET BASE CHILD',child.pid,'POINTS',nassert,flush=True);code=child.wait()
 text=(out/'prove.log').read_text();passed=code==0 and 'SAT proof finished - no model found: SUCCESS!' in text
 for name,h in bindings.items():assert sha(name)==h
 with (out/'receipt.json').open('x') as f:json.dump(dict(status='reset_base_lemma_pass_under_recorded_assumptions' if passed else 'reset_base_lemma_not_proven',bindings=bindings,exit_code=code,assertion_points=nassert,reset_base_pass=passed,component_seconds=time.perf_counter()-tick,full_HDL_four_state_certificate=False,files={str(x):sha(x) for x in out.iterdir() if x.is_file()}),f,indent=2)
 print('RESET BASE TERMINAL',code,passed,flush=True)
if __name__=='__main__':main()
