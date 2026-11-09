"""Audit private slack-budget trees and validate every distinct native route."""
import collections,csv,hashlib,json,os,subprocess,sys,time,xml.etree.ElementTree as ET,struct
from decimal import Decimal
from pathlib import Path
R=Path(__file__).resolve().parents[1];UP=R/'work/sb3_STA_budget_displaced_repair_20261015';P=R/'work/sb3_STA_budget_repair_native_20261015'
def main():
 P.mkdir(exist_ok=False);refs={}
 def sha(f):
  f=Path(f);h=hashlib.sha256()
  with f.open('rb') as stream:
   for b in iter(lambda:stream.read(1048576),b''):h.update(b)
  refs[str(f)]=h.hexdigest();return h.hexdigest()
 def load(f):sha(f);return json.loads(Path(f).read_text())
 def rows(f):sha(f);return list(csv.DictReader(Path(f).open()))
 watch=load(UP/'launch_receipt.json')
 def live():
  try:
   f=Path('/proc/'+str(watch['pid'])+'/stat').read_text().rsplit(')',1)[1].split();return f[19]==watch['proc_start_ticks'] and f[0]!='Z'
  except FileNotFoundError:return False
 while not (UP/'result.json').exists():
  assert live(),'repair owner missing without result';time.sleep(5)
 # Wait for the owner exit receipt before trusting result publication.
 while load(UP/'manifest.json')['status']=='running_private_delay_bounded_repairs':time.sleep(2)
 terminal=load(UP/'manifest.json');assert terminal['status']=='producer_complete_requires_independent_review' and terminal['producer_returncode']==0
 result=load(UP/'result.json')
 for document in [result,load(UP/'protocol.json'),load(UP/'input_bindings.json')]:
  for f,h in document['source_sha256'].items():assert sha(f)==h,f
 base=R/'work/sb3_ex5p_two_net_native_validation_v2_20261015';protocol=load(base/'protocol.json');prior=load(base/'result.json');case=protocol['case'];native=Path(case['native_case'])
 for f,h in protocol['source_sha256'].items():assert sha(f)==h,f
 tasks={int(v['id']):v for v in rows(case['connections'])};nodes=list(struct.iter_unpack('<IHH',Path(case['input_prefix']+'.nodes').read_bytes()));edges=list(struct.iter_unpack('<IHH',Path(case['input_prefix']+'.edges').read_bytes()))
 lengths=[0]*len(nodes)
 for _,e in ET.iterparse(native/'rr_graph.xml',events=('end',)):
  if e.tag=='node':
   a=e.attrib;l=e.find('loc')
   if a['type'] in ['CHANX','CHANY'] and a.get('direction')!='NONE':lengths[int(a['id'])]=1+int(l.attrib['xhigh'])-int(l.attrib['xlow'])+int(l.attrib['yhigh'])-int(l.attrib['ylow'])
   e.clear()
  elif e.tag=='edge':e.clear()
 outcomes=[];seen={};target=int(Decimal(str(case['baseline_cpd_ns']))*1000)
 for index,trial in enumerate(result['outcomes']):
  name=trial['parent_trial'];net=trial['displaced_net'];record=dict(parent_trial=name,order=trial['order'],complete=trial['complete'])
  if not trial['complete']:
   assert trial['steps'][-1]['status'] in ['label_budget_exhausted','no_feasible_path'];outcomes.append(record);continue
  old=rows(base/name/'route.route_trees.csv');parent={int(v):u for v,u in trial['parent'].items()};old_parent={int(v['child']):int(v['parent']) for v in old if int(v['net_id'])==net}
  observation={int(v['task_id']):v for v in rows(R/'work/sb3_native_exchange_timing_observation_20261015'/name/'observe.output.csv')}
  expected={t for t,v in tasks.items() if int(v['net_id'])==net};assert set(map(int,trial['paths']))==expected
  reconstructed={};source=int(tasks[next(iter(expected))]['source'])
  for task in expected:
   path=trial['paths'][str(task)];assert path[-1]==int(tasks[task]['sink']) and len(set([source]+path))==len(path)+1 and len(path)<=int(tasks[task]['max_hops'])
   total=0;u=source
   for v in path:
    start,count,_=nodes[u];weights=[w for dst,_,w in edges[start:start+count] if dst==v];assert weights
    total+=min(weights);assert v not in reconstructed or reconstructed[v]==u;reconstructed[v]=u;u=v
   cap=max(0,int(observation[task]['delay_ps'])+target+int(observation[task]['slack_ps']));assert total<=cap
   step=next(v for v in trial['steps'] if v['task']==task);assert step['delay_cap_ps']==cap
  assert reconstructed==parent
  owners=collections.defaultdict(set)
  for row in old:
   if int(row['net_id'])!=net and row['child']!=row['source']:owners[int(row['child'])].add(int(row['net_id']))
  arm=name.split('_owner')[0];resources=list(struct.iter_unpack('<HHHHII',(R/'work/sb3_fixed_feedback_pair_20261015/native_runs'/('ex5p_'+arm+'_0')/'route.resources').read_bytes()))
  for v in parent:assert len(owners[v])+1<=resources[v][1]
  old_wire=sum(lengths[v] for v in old_parent);new_wire=sum(lengths[v] for v in parent)
  assert (old_wire,new_wire)==(trial['old_displaced_native_wire'],trial['new_displaced_native_wire'])
  canonical=(name,tuple(sorted(parent.items())))
  record.update(old_displaced_wire=old_wire,new_displaced_wire=new_wire)
  if canonical in seen:
   record.update(native_evidence=seen[canonical],duplicate_canonical_tree=True);outcomes.append(record);continue
  label=name+'_order'+str(index);directory=P/label;directory.mkdir();tree=directory/'route.route_trees.csv'
  with tree.open('w') as stream:
   writer=csv.DictWriter(stream,fieldnames=['net_id','source','parent','child']);writer.writeheader();writer.writerows(row for row in old if int(row['net_id'])!=net)
   writer.writerows(dict(net_id=net,source=source,parent=u,child=v) for v,u in sorted(parent.items()))
  with (directory/'writer.log').open('w') as log:rc=subprocess.run([sys.executable,protocol['writer'],str(native/'circuit.route'),str(native/'rr_graph.xml'),case['connections'],str(tree),str(directory/'native.route')],stdout=log,stderr=subprocess.STDOUT).returncode
  assert rc==0,label
  command=[sys.executable,protocol['validator'],'--vpr',protocol['vpr'],'--device','DieRouteSBScale3']
  for flag,f in [('arch','architecture.xml'),('circuit','circuit.blif'),('net','circuit.net'),('place','circuit.place'),('rr-graph','rr_graph.xml')]:command+=['--'+flag,str(native/f)]
  command+=['--route',str(directory/'native.route'),'--channel-width','80','--work-dir',str(directory/'native_validation'),'--baseline-wirelength',str(case['baseline_wirelength']),'--baseline-cpd-ns',str(case['baseline_cpd_ns'])]
  env={k:v for k,v in os.environ.items() if not k.startswith(('PERSISTROUTE_','DIEROUTE_'))}
  with (directory/'validation.log').open('w') as log:rc=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,env=env).returncode
  quality=load(directory/'native_validation/validation.json');assert rc==0 and quality['legal'],label
  parent_validation=next(v['validation'] for v in prior['outcomes'] if v['label']==name)
  assert quality['total_wirelength']==parent_validation['total_wirelength']-old_wire+new_wire
  sha(tree);sha(directory/'native.route');seen[canonical]=label;record.update(native_evidence=label,duplicate_canonical_tree=False,native_quality=quality)
  outcomes.append(record);print(json.dumps(dict(label=label,wire=quality['total_wirelength'],cpd=quality['critical_path_delay_ns'])),flush=True)
  (P/'partial_result.json').write_text(json.dumps(dict(outcomes=outcomes),indent=2)+'\n')
 sha(Path(__file__).resolve());report=dict(status='all_STA_budget_orders_audited_and_distinct_routes_native_validated',outcomes=outcomes,distinct_native_runs=len(seen),source_sha256=refs,adopted=False,research_complete=False,scope='Posterior ex5p diagnostics,conservativeSTA-derived budgets;allorders retained and identicalcanonicaltrees deduplicated.No generalpolicy/heldout/repeat/physicalclaim.')
 (P/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
