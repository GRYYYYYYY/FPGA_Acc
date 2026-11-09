"""Both exact upstream testbenches on original pinned PRINCE RTL."""
import json,re,subprocess,time
from pathlib import Path
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prince_candidate_source_v2_2026-10-20';T=E/'prince_upstream_testbench_source_v1_2026-10-20';D=E/'prince_upstream_sim_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);proof=T/'verification.json';v=json.loads(proof.read_text());assert all(sha(p)==h for p,h in v['bindings'].items()) and all(sha(r['path'])==r['sha256'] for r in v['rows']);usr=E/'prospective_external_family_sim_runtime_v1_2026-10-18/root/usr';iv=usr/'bin/iverilog';vvp=usr/'bin/vvp';lib=usr/'lib/x86_64-linux-gnu/ivl';rtl=[S/'upstream/src/rtl/prince.v',S/'upstream/src/rtl/prince_core.v'];rows=[];files=[Path(__file__),proof,iv,vvp,*rtl,S/'upstream/src/rtl/prince_round_functions.vh',*[p for p in lib.iterdir() if p.is_file()]];bindings={str(p):sha(p) for p in files};(D/'protocol.json').write_text(json.dumps({'status':'FROZEN_BOTH_ORIGINAL_PRINCE_TESTBENCH_RUNS','testbenches':[r['relative'] for r in v['rows']],'policy':'Original RTL/testbench bytes unchanged, both outcomes retained. No mapped/native/full HDL or unseen admission.','bindings':bindings},indent=2)+'\n')
 for r in v['rows']:
  tb=Path(r['path']);out=D/tb.stem;out.mkdir();image=out/'sim.vvp';cmd=[str(iv),'-B',str(lib),'-g2012','-I',str(S/'upstream/src/rtl'),'-s',tb.stem,'-o',str(image),*[str(p) for p in rtl],str(tb)];tick=time.perf_counter()
  with (out/'compile.log').open('x') as log:code=subprocess.call(cmd,stdout=log,stderr=subprocess.STDOUT)
  assert code==0
  with (out/'simulation.log').open('x') as log:code=subprocess.call([str(vvp),'-M',str(lib),str(image)],stdout=log,stderr=subprocess.STDOUT)
  text=(out/'simulation.log').read_text();matches=re.findall(r'All\s+(\d+) test cases completed successfully',text);passed=code==0 and bool(matches) and 'Incorrect' not in text and 'did not complete successfully' not in text;rows.append({'testbench':tb.stem,'exit_code':code,'upstream_testcases':int(matches[-1]) if matches else None,'upstream_summary_pass':passed,'component_seconds':time.perf_counter()-tick,'compile_command':cmd});bindings[str(tb)]=sha(tb)
  for p in out.iterdir():
   if p.is_file():bindings[str(p)]=sha(p)
  print('PRINCE_UPSTREAM_RESULT',rows[-1],flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps({'status':'BOTH_ORIGINAL_UPSTREAM_TESTBENCHES_PASS' if all(r['upstream_summary_pass'] for r in rows) else 'UPSTREAM_TESTBENCH_FAILURE_RETAINED','rows':rows,'bindings':bindings,'scope':'Original finite upstream assertions/vectors only; does not strengthen their comparison semantics or prove full HDL equivalence, mapped/native behavior, reset timing or unseen family.'},indent=2)+'\n')
if __name__=='__main__':main()
