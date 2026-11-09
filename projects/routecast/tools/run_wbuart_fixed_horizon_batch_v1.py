"""Freeze all9/36arms16round convergence trial before execution."""
import json,subprocess,sys,resource,concurrent.futures
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_fixed_horizon_trial_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);preflight=E/'wbuart_fixed_horizon_preflight_v1_2026-10-20/verification.json';assert read(preflight)['status']=='FIRST16_ROUND_COMPLETE_AUDIT_AND_ORIGINAL_TWO_ROUND_PREFIX_EXACT_PASS';assert all(sha(p)==h for p,h in read(preflight)['bindings'].items());old=read(E/'wbuart_forecasts_v1_2026-10-20/manifest.json');cases=[dict(c,output=str(D/c['case'])) for c in old['cases']];runner=R/'tools/run_wbuart_fixed_horizon_case_v1.py';files=[Path(__file__),runner,R/'tools/run_wbuart_fixed_horizon_v1.py',R/'tools/verify_wbuart_fixed_horizon_events_v1.py',R/'tools/audit_wbuart_fixed_horizon_timing_v1.py',R/'tools/evaluate_wbuart_fixed_horizons_v1.py',E/'wbuart_fixed_horizon_design_v1_2026-10-20/protocol.json',preflight];bindings={**old['bindings'],**{str(p):sha(p) for p in files}};mp=D/'manifest.json';mp.write_text(json.dumps({'cases':cases,'bindings':bindings,'round_count':16,'report_horizons':[2,4,8,16],'original_primary_round_count':2,'workers':3,'per_worker_memory_GiB':32,'preflight_reuse':'w096episode01 native_retained updated arm only, costs retained','quality_gate':old['quality_gate'],'strict_unseen_admitted':False,'scope':'Development convergence diagnosis; all guards/budgets unchanged. No selection of best horizon or replacement of original failed two-round primary.'},indent=2)+'\n');print('ALL9_36_ARMS16ROUND_TRIAL_FROZEN',flush=True)
 def limit():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 def run(c):
  with (D/(c['case'].replace('/','_')+'.log')).open('x') as f:rc=subprocess.call([sys.executable,str(runner),str(mp),c['case']],stdout=f,stderr=subprocess.STDOUT,preexec_fn=limit)
  row={'case':c['case'],'exit_status':rc};print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
 (D/'terminal.json').write_text(json.dumps({'rows':rows,'all_pass':all(r['exit_status']==0 for r in rows)},indent=2)+'\n')
 if not all(r['exit_status']==0 for r in rows):raise RuntimeError('Preserve failed cases')
 subprocess.run([sys.executable,str(R/'tools/evaluate_wbuart_fixed_horizons_v1.py')],check=True)
if __name__=='__main__':main()
