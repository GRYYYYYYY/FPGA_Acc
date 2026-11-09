"""Three frozen posterior whole-net restoration probes; retain native failures."""
from pathlib import Path
import csv,hashlib,json,os,subprocess,time
R=Path(__file__).resolve().parents[1];D=R/'work/elliptic_capacity_restore_closure_20261020'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 p=json.loads((D/'protocol.json').read_text())
 while True:
  state=json.loads(Path(p['prerequisite_manifest']).read_text())
  if state['status']=='all_three_restore_probes_terminal_requires_independent_review':break
  pid=p['prerequisite_owner']['pid']
  stat=Path(f'/proc/{pid}/stat').read_text();fields=stat[stat.rfind(')')+2:].split()
  assert fields[0]!='Z' and fields[19]==p['prerequisite_owner']['start_ticks'],'Original probe owner missing; reconcile'
  time.sleep(30)
 for f,h in p['source_sha256'].items():assert sha(f)==h,f
 def rows(path):
  with Path(path).open() as f:return list(csv.DictReader(f))
 baseline=rows(p['baseline_tree']);candidate=rows(p['candidate_tree']);results=[]
 state={'status':'running_frozen_restore_probes','pid':os.getpid(),'results':results,'research_complete':False,'adopted':False}
 def save():
  t=D/'manifest.tmp';t.write_text(json.dumps(state,indent=2)+'\n');t.replace(D/'manifest.json')
 assert not (D/'manifest.json').exists();save()
 env={k:v for k,v in os.environ.items() if not k.startswith(('DIEROUTE_','PERSISTROUTE_'))}
 for arm in p['arms']:
  start=time.monotonic_ns();folder=D/arm['name'];folder.mkdir();nets=set(arm['nets']);tree=folder/'route.route_trees.csv'
  selected=[v for v in candidate if int(v['net_id']) not in nets]+[v for v in baseline if int(v['net_id']) in nets]
  selected.sort(key=lambda v:(int(v['net_id']),int(v['child']),int(v['parent'])))
  with tree.open('w') as f:
   w=csv.DictWriter(f,fieldnames=['net_id','source','parent','child'],extrasaction='ignore');w.writeheader();w.writerows(selected)
  outcome={'name':arm['name'],'restored_nets':arm['nets'],'tree_sha256':sha(tree),'steps':[]};results.append(outcome);save()
  for name,template in p['commands'].items():
   cmd=[s.replace('ARM_DIRECTORY',str(folder)).replace('ARM_TREE',str(tree)) for s in template]
   with (folder/(name+'.log')).open('x') as log:rc=subprocess.run(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
   outcome['steps'].append({'name':name,'command':cmd,'returncode':rc});save()
   if rc:outcome['status']='rejected_'+name+'_failure';break
  else:
   q=json.loads((folder/'native_validation/validation.json').read_text());outcome['native_quality']=q;outcome['status']='native_terminal_requires_crossing_and_provenance_review'
  outcome['wall_ns']=time.monotonic_ns()-start;save()
 state['status']='all_three_restore_probes_terminal_requires_independent_review';save()
if __name__=='__main__':main()
