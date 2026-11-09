"""Execute frozen native/quality phase; retain every fixed failure, no retries."""
import concurrent.futures,hashlib,json,resource,subprocess,time
from pathlib import Path
from run_wbuart_native_target_case_v1 import validate as validate_cold
from run_wbuart_native_utility_case_v2 import validate as validate_utility
R=Path(__file__).resolve().parents[1];O=R/'experiments/wbuart_native_evaluation_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 plan=O/'workflow.json';p=json.loads(plan.read_text())
 for n,h in p['bindings'].items():assert sha(Path(n))==h
 assert len([c for c in p['commands'] if c['kind']=='cold'])==9 and len([c for c in p['commands'] if c['kind']=='utility'])==27;run=O/'execution';run.mkdir(exist_ok=False)
 for job in p['commands']:
  if job['kind']=='cold':m,row,ep=validate_cold(p['cold_manifest'],job['case']);assert m['native_target_execution_admitted'] and len(ep['connections'])==2493
  elif job['kind']=='utility':m,row,ep=validate_utility(p['utility_manifest'],job['case']);assert m['native_execution_admitted'] and m['phase']=='target_native_control_and_utility' and len(ep['connections'])==2493
 (run/'protocol.json').write_text(json.dumps({'workflow':str(plan),'workflow_sha256':sha(plan),'runner_sha256':sha(Path(__file__)),'max_parallel_native_jobs':3,'per_job_AS_limit_GiB':32,'all36_native_preflights_passed':True,'timing_scope':p['timing'],'failure_policy':p['failure_policy']},indent=2)+'\n')
 def limit():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 def execute(job):
  start=time.perf_counter();log=run/(job['kind']+'_'+job['case'].replace('/','_')+'.log')
  with log.open('x') as f:rc=subprocess.call(job['argv'],cwd=R,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limit)
  row={'kind':job['kind'],'case':job['case'],'exit_status':rc,'seconds':time.perf_counter()-start,'log':str(log)};print(json.dumps(row),flush=True);return row
 native=[c for c in p['commands'] if c['kind']!='compare']
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(execute,native))
 (O/'native_terminal.json').write_text(json.dumps({'status':'ALL36_FIXED_NATIVE_TARGET_CASES_TERMINAL','rows':rows,'all_pass':all(r['exit_status']==0 for r in rows)},indent=2)+'\n');comparisons=[execute(c) for c in p['commands'] if c['kind']=='compare']
 (O/'terminal.json').write_text(json.dumps({'status':'FIXED_NATIVE_PHASE_AND_ALL9_COMPARISON_COMMANDS_TERMINAL','native_rows':rows,'comparison_rows':comparisons,'bindings':{str(plan):sha(plan),str(run/'protocol.json'):sha(run/'protocol.json')},'strict_unseen_admitted':False,'full_paid_gain_proven':False},indent=2)+'\n')
if __name__=='__main__':main()
