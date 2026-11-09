"""Freeze and launch serial native checks for completed private exchange trees."""
from pathlib import Path
import argparse,hashlib,json,subprocess,time
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('generation',type=Path);parser.add_argument('template_protocol',type=Path);a=parser.parse_args();D=a.generation.resolve();gp=json.loads((D/'protocol.json').read_text());m=json.loads((D/'manifest.json').read_text());assert m['status']=='budgeted_exchange_arms_terminal_require_review'
 template=json.loads(a.template_protocol.read_text());assert template['connections']==gp['connections'] and template['baseline_tree']==gp['baseline_tree'] and template['resources']==gp['resources']
 unique={};groups={}
 for arm in m['arms']:
  if arm.get('candidate_tree'):
   assert sha(arm['candidate_tree'])==arm['candidate_tree_sha256'];unique.setdefault(arm['candidate_tree_sha256'],arm);groups.setdefault(arm['candidate_tree_sha256'],[]).append(arm['name'])
 assert unique,'No complete candidates';queue=D/'native_queue';queue.mkdir();cases=[]
 for arm in unique.values():
  folder=queue/arm['name'];folder.mkdir();p={k:v for k,v in template.items() if k!='source_sha256'};p['candidate_tree']=arm['candidate_tree'];p['scope']='Completedprivateexchange,independentcapacity/nativechecks;originalcohortunchanged. Noqualityoradoptionclaimbeforeaudit.'
  runner=folder/'run.py';runner.write_text('from pathlib import Path\nimport sys\nsys.path.insert(0,'+repr(str(R/'tools'))+')\nimport audit_private_tree_capacity as pre\nimport run_elliptic_critical_net_restore as job\npre.main(Path(__file__).resolve().parent)\njob.D=Path(__file__).resolve().parent\njob.main()\n')
  files={Path(s) for cmd in p['commands'].values() for s in cmd if Path(s).is_file()};files.update(Path(p[k]) for k in ['candidate_tree','baseline_tree','connections','resources','node_die']);files.update([runner,R/'tools/audit_private_tree_capacity.py',R/'tools/run_elliptic_critical_net_restore.py',D/'protocol.json',D/'manifest.json',a.template_protocol.resolve(),Path(__file__).resolve()]);p['source_sha256']={str(f):sha(f) for f in files};(folder/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');cases.append({'net':arm['name'],'command':['python3',str(runner)]})
 supervisor_template=R/'work/elliptic_local_exchange_20261020/native_queue/supervise.py';(queue/'supervise.py').write_bytes(supervisor_template.read_bytes());(queue/'protocol.json').write_text(json.dumps({'cases':cases,'deduplicated_generation_groups':groups,'source_sha256':{str(queue/c['net']/'protocol.json'):sha(queue/c['net']/'protocol.json') for c in cases},'scope':'Serialnativechecksofuniquecompleteexchanges;retainallfailures.'},indent=2)+'\n')
 with (queue/'supervisor.stdout').open('x') as f:child=subprocess.Popen(['python3',str(queue/'supervise.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
 (queue/'launch_receipt.json').write_text(json.dumps({'pid':child.pid,'launched_ns':time.time_ns(),'protocol_sha256':sha(queue/'protocol.json'),'supervisor_sha256':sha(queue/'supervise.py')},indent=2)+'\n');print(json.dumps({'directory':str(D),'pid':child.pid,'unique_candidates':len(cases)}))
if __name__=='__main__':main()
