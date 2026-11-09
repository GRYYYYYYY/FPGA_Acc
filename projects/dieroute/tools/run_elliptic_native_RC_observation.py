"""Serial native net-delay observations without injecting local-delay estimates."""
from pathlib import Path
import hashlib,json,os,subprocess,time
D=Path(__file__).resolve().parents[1]/'work/elliptic_native_RC_observation_20261020'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 p=json.loads((D/'protocol.json').read_text())
 for f,h in p['source_sha256'].items():assert sha(f)==h,f
 assert not (D/'manifest.json').exists();s={'status':'serial_native_RC_observations_running','pid':os.getpid(),'cases':[],'research_complete':False}
 def save():
  t=D/'manifest.tmp';t.write_text(json.dumps(s,indent=2)+'\n');t.replace(D/'manifest.json')
 save()
 for case in p['cases']:
  env={k:v for k,v in os.environ.items() if not k.startswith(('DIEROUTE_','PERSISTROUTE_'))};env.update(case['environment']);start=time.monotonic_ns()
  with (D/(case['name']+'.log')).open('x') as log:
   child=subprocess.Popen(case['command'],cwd=D,env=env,stdout=log,stderr=subprocess.STDOUT);s.update(active_case=case['name'],child_pid=child.pid);save();rc=child.wait()
  s['cases'].append({'name':case['name'],'returncode':rc,'wall_ns':time.monotonic_ns()-start});save()
  if rc:s['status']='native_observation_failed_requires_review';save();return
 s['status']='all_three_native_RC_observations_terminal_requires_review';save()
if __name__=='__main__':main()
