"""Execute frozen cold development cases serially, preserve failures and paid clocks."""
import json,hashlib,shutil,subprocess,resource,time,re,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'experiments/prince_native_cohort_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
def main():
 pp=O/'protocol.json';p=json.loads(pp.read_text());assert all(sha(f)==h for f,h in p['bindings'].items());results=[];start=time.perf_counter()
 env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
 for job in p['jobs']:
  d=Path(job['directory']);d.mkdir(parents=True,exist_ok=False)
  for name,source in {**p['staging'],'design.place':job['place']}.items():shutil.copyfile(source,d/name);assert sha(d/name)==sha(source)
  tick=time.perf_counter()
  with (d/'native.log').open('x') as f:
   child=subprocess.Popen(job['command'],cwd=d,env=env,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limit);(d/'live_process.json').write_text(json.dumps(dict(pid=child.pid,command=job['command'])));code=child.wait()
  text=(d/'native.log').read_text();success=code==0 and 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text
  result=dict(case=job['case'],exit_code=code,native_full_check_pass=success,native_seconds=time.perf_counter()-tick,iterations=re.findall(r'Successfully routed after (\d+) routing iterations',text),independent_physical_audit_pending=success,canonical_reload_pending=success,protocol_sha256=sha(pp),files={str(f):sha(f) for f in d.iterdir() if f.is_file() and f.name!='live_process.json'})
  (d/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result);(O/'progress.json').write_text(json.dumps(dict(results=results),indent=2)+'\n');print('PRINCE_NATIVE_TERMINAL',job['case'],code,success,flush=True)
 assert all(sha(f)==h for f,h in p['bindings'].items())
 (O/'receipt.json').write_text(json.dumps(dict(results=results,continuous_seconds=time.perf_counter()-start,protocol_sha256=sha(pp),full_workflow_gain_proven=False,strict_unseen_admitted=False),indent=2)+'\n')
if __name__=='__main__':main()
