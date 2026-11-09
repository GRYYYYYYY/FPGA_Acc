"""Separate non-divergence lemma, composed only with recorded reset-base proof."""
import hashlib,json,os,re,resource,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 parent=R/'experiments/prospective_external_family_source_equivalence_v1_2026-10-18';pp=parent/'protocol.json';p=json.loads(pp.read_text());base=R/'experiments/prospective_external_family_reset_base_v1_2026-10-18';bp=base/'receipt.json';b=json.loads(bp.read_text());assert b['reset_base_pass'] and b['assertion_points']==1970
 adapter_path=base/'receipt_binding_admission_v1.json';adapter=json.loads(adapter_path.read_text());assert adapter['status']=='reset_base_proof_admitted_with_explicit_self_binding_correction' and adapter['reset_base_pass']
 for name,h in adapter['bindings'].items():assert sha(name)==h
 out=R/'experiments/prospective_external_family_inductive_step_v1_2026-10-18';out.mkdir(exist_ok=False);prefix=p['commands'][:p['commands'].index('equiv_simple -undef')];commands=prefix+['write_json "'+str(out/'before.json')+'"','equiv_induct -undef -seq 2','equiv_status -assert']
 with (out/'commands.ys').open('x') as f:f.write('\n'.join(commands)+'\n')
 bindings={**p['bindings'],str(pp):sha(pp),str(bp):sha(bp),str(adapter_path):sha(adapter_path),str(base/'protocol.json'):sha(base/'protocol.json'),str(Path(__file__)):sha(__file__)}
 with (out/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,identical_equiv_model_prefix=prefix,commands=commands,scope='Non-divergence lemma under pinned Yosys undef-aware temporal induction with2prior agreeing observation frames. Combine only with the separately proved reset_n=0 base on frames2and3 and all1970points; not an arbitrary-power-up, arbitrary-clock-waveform or full original HDL/four-state certificate.',unrestricted_proof_process_preserved=dict(pid=990092,session=73780)),f,indent=2)
 v=json.loads((R/'experiments/prospective_external_family_source_v2_2026-10-18/source_verification.json').read_text());tool=Path(v['yosys_path']);env=os.environ.copy();runtime=R/'experiments/prospective_external_family_runtime_v1_2026-10-18';lib=runtime/'tcl-root/usr/lib/x86_64-linux-gnu';env['LD_LIBRARY_PATH']=str(lib)+(os.pathsep+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
 def limits():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
 tick=time.perf_counter()
 with (out/'check.log').open('x') as log:
  child=subprocess.Popen([str(tool),'-Q','-T','-s',str(out/'commands.ys')],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits)
  with (out/'live_process.json').open('x') as f:json.dump(dict(pid=child.pid),f)
  print('INDUCTIVE STEP CHILD',child.pid,flush=True);code=child.wait()
 text=(out/'check.log').read_text();counts=re.findall(r'Of those cells (\d+) are proven and (\d+) are unproven',text);before=json.loads((out/'before.json').read_text())['modules']['equiv'];properties=sum(c['type']=='$equiv' for c in before['cells'].values());assert properties==b['assertion_points']==1970
 passed=code==0 and counts and tuple(map(int,counts[-1]))==(properties,0) and 'Equivalence successfully proven' in text
 for name,h in bindings.items():assert sha(name)==h
 files={str(x):sha(x) for x in out.iterdir() if x.is_file()}
 with (out/'receipt.json').open('x') as f:json.dump(dict(status='reset_based_Yosys_model_nondivergence_composition_pass' if passed else 'inductive_step_not_proven',bindings=bindings,exit_code=code,properties=properties,step_pass=bool(passed),reset_base_pass=True,composed_after_reset_model_agreement=bool(passed),full_original_HDL_four_state_certificate=False,arbitrary_power_up_equivalence=False,component_seconds=time.perf_counter()-tick,files=files),f,indent=2)
 print('INDUCTIVE STEP TERMINAL',code,bool(passed),properties,flush=True)
if __name__=='__main__':main()
