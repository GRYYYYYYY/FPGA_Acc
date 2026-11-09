"""Inductive equivalence under pinned Yosys frontend/undef semantics, not HDL cert."""
import hashlib,json,os,resource,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 source=R/'experiments/prospective_external_family_source_v2_2026-10-18';vp=source/'source_verification.json';v=json.loads(vp.read_text());cut=R/'experiments/prospective_external_family_compile_cut_v2_2026-10-18';cp=R/'experiments/prospective_external_family_compile_verification_v1_2026-10-18/verification.json';cv=json.loads(cp.read_text());assert cv['status']=='mapped_Boolean_cut_and_exact_FF_boundary_independently_verified';runtime=R/'experiments/prospective_external_family_runtime_v1_2026-10-18';tool=Path(v['yosys_path']);rtl=[Path(a['path']) for a in v['assets'] if a['relative'] in v['RTL_compilation_units']]
 for p,h in cv['bindings'].items():assert sha(p)==h
 out=R/'experiments/prospective_external_family_source_equivalence_v1_2026-10-18';out.mkdir(exist_ok=False)
 commands=['read_verilog '+' '.join('"'+str(p)+'"' for p in rtl),'hierarchy -check -top chacha','proc','flatten','memory_map','opt','hierarchy -top chacha','splitnets -ports','rename chacha gold','design -stash gold_store','read_blif "'+str(cut/'design.blif')+'"','hierarchy -check -top chacha','splitnets -ports','rename chacha gate','design -stash gate_store','design -copy-from gold_store -as gold gold','design -copy-from gate_store -as gate gate','equiv_make gold gate equiv','hierarchy -top equiv','equiv_simple -undef','equiv_induct -undef -seq 2','equiv_status -assert']
 bindings={str(p):sha(p) for p in [Path(__file__),vp,cp,tool,*rtl,cut/'design.blif',runtime/'verification.json']}
 with (out/'commands.ys').open('x') as f:f.write('\n'.join(commands)+'\n')
 with (out/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,commands=commands,AS_limit_bytes=8*2**30,scope='No input/reset assumptions added. Compare parsed+process/memory-lowered reference to restored mapped BLIF under this Yosys frontend and undef-aware inductive semantics. Not independent simulator, full original HDL/four-state/STA or native-routing proof; failures remain failures.'),f,indent=2)
 env=os.environ.copy();lib=runtime/'tcl-root/usr/lib/x86_64-linux-gnu';env['LD_LIBRARY_PATH']=str(lib)+(os.pathsep+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
 def limits():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
 tick=time.perf_counter()
 with (out/'check.log').open('x') as log:
  child=subprocess.Popen([str(tool),'-Q','-T','-s',str(out/'commands.ys')],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits)
  with (out/'live_process.json').open('x') as f:json.dump(dict(pid=child.pid),f)
  print('SOURCE EQUIVALENCE CHILD',child.pid,flush=True);code=child.wait()
 elapsed=time.perf_counter()-tick;text=(out/'check.log').read_text();passed=code==0 and 'Equivalence successfully proven' in text
 for p,h in bindings.items():assert sha(p)==h
 with (out/'receipt.json').open('x') as f:json.dump(dict(status='Yosys_model_inductive_equivalence_pass' if passed else 'Yosys_model_equivalence_not_proven',bindings=bindings,exit_code=code,component_seconds=elapsed,log_sha256=sha(out/'check.log'),equivalence_pass=passed,full_original_HDL_four_state_certificate=False,strict_unseen_admitted=False,new_placement_route_jobs=False),f,indent=2)
 print('SOURCE EQUIVALENCE TERMINAL',code,passed,flush=True)
if __name__=='__main__':main()
