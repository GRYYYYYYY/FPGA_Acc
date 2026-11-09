"""Freeze all9 observed targets, require exact old native trajectory parity."""
import json,subprocess,sys,concurrent.futures
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_expected_cost_targets_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);qualification=E/'wbuart_expected_cost_on_qualification_v1_2026-10-20/independent_expected_cost_verification_v1.json';q=read(qualification);assert q['samples']==1634 and all(sha(p)==h for p,h in q['bindings'].items());build=R/'build/wbuart_expected_cost_observer_v1_2026-10-20/receipt.json';b=read(build);assert sha(b['binary'])==b['binary_sha256'];cold=E/'wbuart_native_evaluation_v1_2026-10-20/cold_manifest.json';runner=R/'tools/run_wbuart_expected_cost_target_case_v1.py';cases=[];files=[Path(__file__),runner,qualification,build,Path(b['binary']),cold];bindings={str(p):sha(p) for p in files}
 for old in read(cold)['cases']:
  c=dict(old);c['command']=list(c['command']);c['command'][0]=b['binary'];case=c['target_case'];c.update(case=case+'/expected_observer',role='fixed_development_expected_cost_observation_only',output=str(D/case),utility_arm='disabled',reference_output=str(E/'wbuart_native_evaluation_v1_2026-10-20/utility'/case/'disabled'));cases.append(c)
  for p in [Path(c['endpoint']),Path(c['reference_output'])/'verification.json',Path(c['reference_output'])/'output.route',Path(c['reference_output'])/'owner_trace.tsv']:bindings[str(p)]=sha(p)
 mp=D/'manifest.json';mp.write_text(json.dumps({'schema':'WBUART_FROZEN_NATIVE_UTILITY_V1','phase':'target_native_control_and_utility','native_execution_admitted':True,'cases':cases,'bindings':bindings,'selection':'All9 fixed targets, previously registeredNET0/allpins only; no outcome-dependent query selection.','scope':'Pure observer qualification/capture, no forecast/risk preload/new label selection. Require original native route/owner trace/work/QoR byte/value parity, then perpin expected-priority samples. No model/native equivalence or speed/quality gain.'},indent=2)+'\n');print('ALL9_EXPECTED_COST_TARGET_CAPTURE_FROZEN',flush=True)
 def run(c):
  with (D/(c['target_case'].replace('/','_')+'.log')).open('x') as f:rc=subprocess.call([sys.executable,str(runner),str(mp),c['case']],stdout=f,stderr=subprocess.STDOUT)
  row={'case':c['target_case'],'exit_status':rc,'verification':str(Path(c['output'])/'verification.json')};print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
 (D/'terminal.json').write_text(json.dumps({'rows':rows,'all_pass':all(r['exit_status']==0 for r in rows)},indent=2)+'\n')
 if not all(r['exit_status']==0 for r in rows):raise RuntimeError('Keep fixed failed captures')
 parity=[]
 for c in cases:
  out=Path(c['output']);ref=Path(c['reference_output']);v,w=read(out/'verification.json'),read(ref/'verification.json');assert v['status']==w['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS';assert all(v[k]==w[k] for k in ['iterations','wirelength','diagnostic_cpd_ns','native_work']);assert sha(out/'output.route')==sha(ref/'output.route') and sha(out/'owner_trace.tsv')==sha(ref/'owner_trace.tsv');assert (out/'expected_cost.tsv').exists();parity.append({'case':c['target_case'],'route_trace_work_QoR_exact_parity':True})
 (D/'verification.json').write_text(json.dumps({'status':'ALL9_TARGET_EXPECTED_OBSERVER_PHYSICAL_CANONICAL_TRACE_AND_EXACT_PARITY_PASS','rows':parity,'bindings':{str(mp):sha(mp),**{r['verification']:sha(r['verification']) for r in rows}},'scope':'NET0 expected-cost sampling, CID/arithmetic audit pending, no model change/quality or gain claim.'},indent=2)+'\n')
if __name__=='__main__':main()
