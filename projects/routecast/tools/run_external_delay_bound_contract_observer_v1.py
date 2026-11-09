"""Fixed all3 cold/seed native feasibility pairs; no end-to-end timing claim."""
import json,sys,copy,subprocess,concurrent.futures,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
E=R/'experiments';S=E/'prospective_external_family_native_utility_seed_inputs_v1_2026-10-19';I=E/'prospective_external_family_seed_import_probe_v1_2026-10-19';D=E/'prospective_external_family_native_delay_bound_contract_observer_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 import_proof=read(I/'verification.json');assert import_proof['all3_import_admitted'] and all(r['native_overflow_units']==r['native_occupancy_residual_nodes']==0 for r in import_proof['rows']);assert all(sha(p)==h for p,h in import_proof['bindings'].items());D.mkdir(exist_ok=False);base=read(E/'prospective_external_family_supplementary_development_v1_2026-10-19/native_manifest.json');cases=[]
 for arm in ['cold','seed']:
  for i in (1,2,3):
   case=f'w160/episode_{i:02d}';old=next(c for c in base['cases'] if c['case']==case);c=copy.deepcopy(old);c['case']=case+'/'+arm;c['output']=str(D/case/arm/'native')
   if arm=='seed':c['inputs']['seed']=str(S/case/'seed.route')
   cases.append(c)
 build=R/'build/native_external_delay_bound_contract_observer_v1_2026-10-19';receipt=read(build/'receipt.json');assert sha(receipt['binary'])==receipt['binary_sha256'];assert all(sha(p)==h for p,h in receipt['bindings'].items())
 for c in cases:c['command'][0]=receipt['binary']
 base['bindings'].update({receipt['binary']:receipt['binary_sha256'],str(build/'receipt.json'):sha(build/'receipt.json'),str(build/'protocol.json'):sha(build/'protocol.json')})
 base['cases']=cases;base['scope']='Native feasibility/QoR only, not matched complete RouteCast timing';base['bindings'].update({str(I/'verification.json'):sha(I/'verification.json'),str(Path(__file__).resolve()):sha(__file__),str(R/'tools/run_external_seeded_native_feasibility_case_v1.py'):sha(R/'tools/run_external_seeded_native_feasibility_case_v1.py')})
 for c in cases:
  if 'seed' in c['inputs']:base['bindings'][c['inputs']['seed']]=sha(c['inputs']['seed'])
 mp=D/'manifest.json';mp.write_text(json.dumps(base,indent=2)+'\n');(D/'protocol.json').write_text(json.dumps(dict(cases=cases,order='all3 cold then all3 seed; at most3 isolated processes',source_model='fixed same primary-budget-repair frames all3',timing_scope='Native component only. Fresh prediction/selection/serialization/admission not run inside this timer. NO end-to-end or speedup acceptance from this pilot.',required_percase_CIDs=15616,policy='All omitted seed NETs remain required; original native options unchanged, explicit seed only seeded arm. Corrected native lower-bound indices apply symmetrically to cold/seed; compare corrected cold for fairness; source/object byte-equivalence audit and four-index-only private patch bound in build receipt. Isolated external-seed LOOKAHEAD-preserving policy; retained_input/nonlookahead unchanged. Initial perpin cold/seed equality and all3 cold archived support equivalence must be independently checked. Full physical/canonical and CPD/wirelength nonregress needed; all outcomes retained, no case winner. Original forecasting/full9/family/hardware gates unchanged.'),indent=2)+'\n')
 def run(c):
  out=Path(c['output']);out.parent.mkdir(parents=True);tick=time.perf_counter()
  with (out.parent/'execution.log').open('x') as log:code=subprocess.run([sys.executable,str(R/'tools/run_external_seeded_native_feasibility_case_v1.py'),str(mp),c['case']],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
  vp=out/'verification.json';a=read(vp) if vp.exists() else {};case,arm=c['case'].rsplit('/',1);row=dict(case=case,arm=arm,process_exit=code,status=a.get('status','MISSING_NATIVE_VERIFICATION'),error=a.get('error'),native_component_plus_audit_wall_seconds=time.perf_counter()-tick,wirelength=a.get('wirelength'),diagnostic_cpd_ns=a.get('diagnostic_cpd_ns'),iterations=a.get('iterations'));(out.parent/'execution_receipt.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row),flush=True);return row
 rows=[]
 for phase in (0,1):
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows+=list(pool.map(run,cases[phase*3:phase*3+3]))
 (D/'terminal.json').write_text(json.dumps(dict(status='ALL6_FIXED_NATIVE_FEASIBILITY_PAIR_PROCESSES_TERMINAL',rows=rows,scope='Native-only feasibility/QoR evidence; original end-to-end gain not assessed.'),indent=2)+'\n')
if __name__=='__main__':main()
