"""All3 fixed scheduling cases in isolated processes, all failures retained."""
import json,sys,subprocess,concurrent.futures
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
D=R/'experiments/prospective_external_family_fanout_order_feedback_v1_2026-10-19'
def main():
 p=json.loads((D/'protocol.json').read_text());assert all(sha(q)==h for q,h in p['bindings'].items())
 def run(c):
  log=D/(c['case'].replace('/','_')+'.log')
  with log.open('x') as f:code=subprocess.run([sys.executable,str(R/'tools/run_external_fanout_order_case_v1.py'),c['case']],cwd=R,stdout=f,stderr=subprocess.STDOUT).returncode
  row=dict(case=c['case'],process_exit=code,log=str(log));rp=Path(c['output'])/'comparison.json'
  if code==0 and rp.exists():
   r=json.loads(rp.read_text());row.update(original_case_gate=r['pass_case_gate'],metrics={m:{scope:{k:v[k] for k in ['spearman','top_k_hits','k','universe_size']} for scope,v in scopes.items()} for m,scopes in r['metrics'].items()},checks=r['checks'])
  print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,p['cases']))
 bindings={str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__).resolve()):sha(__file__),str(R/'tools/run_external_fanout_order_case_v1.py'):sha(R/'tools/run_external_fanout_order_case_v1.py')}
 for c in p['cases']:
  for name in ['comparison.json','comparison_spec.json','complete_event_audit.json']:
   q=Path(c['output'])/name
   if q.exists():bindings[str(q)]=sha(q)
 with (D/'quality_summary.json').open('x') as f:json.dump(dict(status='ALL3_FROZEN_FANOUT_ONLY_CASE_PROCESSES_TERMINAL',rows=rows,bindings=bindings,unavailable_cases=p['unavailable_cases'],all9_availability_pass=False),f,indent=2)
if __name__=='__main__':main()
