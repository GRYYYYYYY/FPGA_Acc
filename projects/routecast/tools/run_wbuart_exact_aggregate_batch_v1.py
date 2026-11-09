"""Freeze all72 numeric exact label diagnostics; no hard-arm omission."""
import json,sys,subprocess,resource,concurrent.futures
from pathlib import Path
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_exact_aggregate_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);design=E/'wbuart_exact_aggregate_solver_design_v1_2026-10-20/protocol.json';assert all(sha(p)==h for p,h in read(design)['bindings'].items());kernel=E/'exact_min_sum_kernel_contract_v1_2026-10-20/verification.json';model=E/'exact_factor_elimination_contract_v1_2026-10-20/verification.json';reduced=E/'wbuart_reduced_L1_factor_profile_v1_2026-10-20/verification.json';ind=reduced.parent/'independent_verification_v1.json'
 for proof in [kernel,model,ind]:assert all(sha(p)==h for p,h in read(proof)['bindings'].items())
 cases=sorted({r['case'] for r in read(reduced)['rows']});assert len(cases)==9 and len(read(reduced)['rows'])==72;files=[Path(__file__),R/'tools/run_wbuart_exact_aggregate_case_v1.py',R/'tools/exact_factor_elimination_v1.py',R/'tools/compiled_exact_min_sum_v1.py',R/'build/exact_min_sum_v1_2026-10-20/minsum.so',kernel,model,reduced,ind,design,E/'wbuart_joint_aggregate_L1_v1_2026-10-20/verification.json'];m={'schema':'ALL72_EXACT_AGGREGATE_LABEL_DIAGNOSTICS_V1','cases':cases,'output':str(D),'reduced_profile':str(reduced),'local_diagnostics':str(E/'wbuart_joint_aggregate_L1_v1_2026-10-20/verification.json'),'workers':9,'per_worker_memory_GiB':8,'bindings':{str(p):sha(p) for p in files},'scope':'Exact finite-pool target-dependent loss/switch minimum only; no deployable forecast/route/native/time/family success. Original scalar batch unchanged.'};mp=D/'manifest.json';mp.write_text(json.dumps(m,indent=2)+'\n');print('ALL72_EXACT_LABEL_DIAGNOSTICS_FROZEN',flush=True)
 def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 def run(case):
  path=D/(case.replace('/','_')+'.log')
  with path.open('x') as f:p=subprocess.run([sys.executable,str(R/'tools/run_wbuart_exact_aggregate_case_v1.py'),str(mp),case],cwd=R,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limit)
  result={'case':case,'exit_status':p.returncode,'log':str(path)};print(json.dumps(result),flush=True);return result
 with concurrent.futures.ThreadPoolExecutor(max_workers=9) as pool:rows=list(pool.map(run,cases))
 (D/'terminal.json').write_text(json.dumps({'rows':rows,'all_pass':all(r['exit_status']==0 for r in rows)},indent=2)+'\n')
 if not all(r['exit_status']==0 for r in rows):raise RuntimeError('preserve failed exact cases and packed banks')
 rows=[r for case in cases for r in read(D/case/'verification.json')['rows']];assert len(rows)==72;(D/'verification.json').write_text(json.dumps({'status':'ALL72_EXACT_AGGREGATE_DIAGNOSTIC_CERTIFICATES_PRODUCED','rows':rows,'bindings':{str(mp):sha(mp),str(D/'terminal.json'):sha(D/'terminal.json')},'independent_full_certificate_and_metric_audit_pending':True},indent=2)+'\n');print('ALL72_EXACT_NUMERIC_PRODUCED',flush=True)
if __name__=='__main__':main()
