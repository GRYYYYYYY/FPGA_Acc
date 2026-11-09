"""Native check of fixed-prefix first cross-limit alternative; no adoption."""
import csv,hashlib,json,os,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/first_crossing_rejection_repair_20261015';O=P/'native_review'
def main():
 O.mkdir(exist_ok=False);refs={}
 def sha(f):
  f=Path(f);h=hashlib.sha256()
  with f.open('rb') as stream:
   for b in iter(lambda:stream.read(1048576),b''):h.update(b)
  refs[str(f)]=h.hexdigest();return h.hexdigest()
 report=json.loads((P/'result.json').read_text());assert report['result']['complete']
 for f,h in report['source_sha256'].items():assert sha(f)==h,f
 root=R/'work/native_slack_guided_net_repair_v1_20261015';protocol=json.loads((root/'protocol.json').read_text());case=next(c for c in protocol['cases'] if c['label']=='ex5p');native=Path(case['native_case']);parent_dir=Path(report['parent_native_directory'])
 for key in ['writer','validator','vpr']:assert sha(protocol[key])==protocol['source_sha256'][protocol[key]]
 def tree(f):
  sha(f);answer={}
  for v in csv.DictReader(Path(f).open()):answer.setdefault(int(v['net_id']),{})[int(v['child'])]=int(v['parent'])
  return answer
 old=tree(parent_dir/'route.route_trees.csv');new=tree(P/'candidate.route_trees.csv');assert new.keys()==old.keys();assert {n for n in new if new[n]!=old[n]}<={report['net']}
 old_quality=json.loads((parent_dir/'native_validation/validation.json').read_text());route=O/'candidate.route'
 commands=[[sys.executable,protocol['writer'],str(native/'circuit.route'),str(native/'rr_graph.xml'),case['connections'],str(P/'candidate.route_trees.csv'),str(route)]]
 command=[sys.executable,protocol['validator'],'--vpr',protocol['vpr'],'--device','DieRouteSBScale3']
 for flag,f in [('arch','architecture.xml'),('circuit','circuit.blif'),('net','circuit.net'),('place','circuit.place'),('rr-graph','rr_graph.xml')]:command+=['--'+flag,str(native/f)]
 command+=['--route',str(route),'--channel-width','80','--work-dir',str(O/'native_validation'),'--baseline-wirelength',str(case['baseline_wirelength']),'--baseline-cpd-ns',str(case['baseline_cpd_ns'])];commands.append(command)
 (O/'protocol.json').write_text(json.dumps(dict(status='frozen_before_native_validation',commands=commands,source_sha256=refs.copy(),research_complete=False),indent=2)+'\n')
 env={k:v for k,v in os.environ.items() if not k.startswith(('PERSISTROUTE_','DIEROUTE_'))}
 for index,command in enumerate(commands):
  with (O/('step'+str(index)+'.log')).open('w') as out:completed=subprocess.run(command,stdout=out,stderr=subprocess.STDOUT,env=env)
  assert completed.returncode==0,index
 quality=json.loads((O/'native_validation/validation.json').read_text());assert quality['legal'] and quality['inputs']['route_sha256']==sha(route)
 assert quality['total_wirelength']==old_quality['total_wirelength']-report['old_native_wire']+report['result']['wire']
 for f in [P/'result.json',O/'protocol.json',O/'native_validation/validation.json',Path(__file__).resolve()]:sha(f)
 result=dict(status='first_crossing_rejection_alternative_native_legal',net=report['net'],native_wirelength=quality['total_wirelength'],native_cpd_ns=quality['critical_path_delay_ns'],parent_wirelength=old_quality['total_wirelength'],parent_cpd_ns=old_quality['critical_path_delay_ns'],global_crossings=report['fixed_other_crossings']+report['result']['crossings'],baseline_crossings=999,joint_baseline_pass=quality['total_wirelength']<=case['baseline_wirelength'] and quality['critical_path_delay_ns']<=case['baseline_cpd_ns'],source_sha256=refs,
  adopted=False,research_complete=False,scope='One first-rejection diagnostic at immutable earlier state;only selectednet changes,full native checks. Doesnotmodify ongoingcohort or establish generalpolicy/repeats/heldoutquality.')
 (O/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))
if __name__=='__main__':main()
