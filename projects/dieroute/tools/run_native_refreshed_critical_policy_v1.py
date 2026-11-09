"""Serial CPU development prototype: one native-STA-guarded joint delay/crossing-budget net sweep.

This is separately charged postprocessing, not an FPGA transaction or adoption.
"""
import collections,csv,hashlib,heapq,json,os,struct,subprocess,sys,time,traceback
from decimal import Decimal
from pathlib import Path
import xml.etree.ElementTree as ET
from shared_tree_budget_repair import repair
from native_STA_task_binding_v2 import make_binder
R=Path(__file__).resolve().parents[1];P=R/'work/native_refreshed_critical_policy_v1_20261016'

def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for b in iter(lambda:stream.read(1048576),b''):h.update(b)
 return h.hexdigest()

def csv_rows(path):
 with Path(path).open() as stream:return list(csv.DictReader(stream))

def atomic(path,data):
 tmp=Path(str(path)+'.tmp');tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(path)

def run_case(case,protocol):
 label=case['label'];D=P/label;D.mkdir(exist_ok=False)
 prior=Path(case['policy_parent_tree']).parent
 native=Path(case['native_case']);raw_nodes=list(struct.iter_unpack('<IHH',Path(case['input_prefix']+'.nodes').read_bytes()));edges=list(struct.iter_unpack('<IHH',Path(case['input_prefix']+'.edges').read_bytes()))
 resources=list(struct.iter_unpack('<HHHHII',Path(case['input_prefix']+'.resources').read_bytes()))
 dies=[v[0] for v in struct.iter_unpack('<H',Path(case['topology_prefix']+'.node_die').read_bytes())]
 assert len(raw_nodes)==len(resources)==len(dies)
 tasks={int(v['id']):v for v in csv_rows(case['connections'])};by_net=collections.defaultdict(list);sources={}
 for task,row in tasks.items():
  net=int(row['net_id']);by_net[net].append(task);sources[net]=int(row['source'])
 trees={net:{} for net in by_net}
 for row in csv_rows(prior/'route.route_trees.csv'):
  net=int(row['net_id']);assert int(row['source'])==sources[net];trees[net][int(row['child'])]=int(row['parent'])
 length=[0]*len(raw_nodes)
 for _,e in ET.iterparse(native/'rr_graph.xml',events=('end',)):
  if e.tag=='node':
   a=e.attrib;l=e.find('loc')
   if a['type'] in ['CHANX','CHANY'] and a.get('direction')!='NONE':length[int(a['id'])]=1+int(l.attrib['xhigh'])-int(l.attrib['xlow'])+int(l.attrib['yhigh'])-int(l.attrib['ylow'])
   e.clear()
  elif e.tag=='edge':e.clear()
 def wire(mapping):return sum(length[v] for parent in mapping.values() for v in parent)
 def crossings(mapping):return sum(dies[v]!=dies[u] for parent in mapping.values() for v,u in parent.items())
 baseline_tree={}
 for row in csv_rows(case['native_tree']):baseline_tree.setdefault(int(row['net_id']),{})[int(row['child'])]=int(row['parent'])
 baseline_cross=crossings(baseline_tree)
 def evaluate(mapping,name,existing_route=None):
  directory=D/name;directory.mkdir(exist_ok=False);tree=directory/'route.route_trees.csv'
  with tree.open('w') as stream:
   writer=csv.DictWriter(stream,fieldnames=['net_id','source','parent','child']);writer.writeheader()
   for net,parent in sorted(mapping.items()):
    writer.writerows(dict(net_id=net,source=sources[net],parent=u,child=v) for v,u in sorted(parent.items()))
  route=Path(existing_route) if existing_route else directory/'native.route'
  if not existing_route:
   with (directory/'writer.log').open('w') as log:
    rc=subprocess.run([sys.executable,protocol['writer'],str(native/'circuit.route'),str(native/'rr_graph.xml'),case['connections'],str(tree),str(route)],stdout=log,stderr=subprocess.STDOUT).returncode
   if rc:return dict(valid=False,stage='writer',returncode=rc),None,directory
  timing_input=directory/'observation.input.csv';timing_output=directory/'observation.output.csv'
  with timing_input.open('w') as stream:
   writer=csv.writer(stream);writer.writerow(['iteration','task_id','net_id','source','sink','routed','delay_ps','criticality_q'])
   for task,row in sorted(tasks.items()):writer.writerow([0,task,row['net_id'],row['source'],row['sink'],0,0,0])
  command=[sys.executable,protocol['validator'],'--vpr',protocol['vpr'],'--device','DieRouteSBScale3']
  for flag,f in [('arch','architecture.xml'),('circuit','circuit.blif'),('net','circuit.net'),('place','circuit.place'),('rr-graph','rr_graph.xml')]:command+=['--'+flag,str(native/f)]
  command+=['--route',str(route),'--channel-width','80','--work-dir',str(directory/'native_validation'),'--baseline-wirelength',str(case['baseline_wirelength']),'--baseline-cpd-ns',str(case['baseline_cpd_ns'])]
  env={k:v for k,v in os.environ.items() if not k.startswith(('PERSISTROUTE_','DIEROUTE_'))};env.update(PERSISTROUTE_VPR_TIMING_INPUT=str(timing_input),PERSISTROUTE_VPR_TIMING_OUTPUT=str(timing_output))
  with (directory/'native.log').open('w') as log:rc=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,env=env).returncode
  validation=directory/'native_validation/validation.json'
  if rc or not validation.exists():return dict(valid=False,stage='native',returncode=rc),None,directory
  quality=json.loads(validation.read_text());assert quality['legal'] and quality['total_wirelength']==wire(mapping)
  observation={int(v['task_id']):{k:int(x) for k,x in v.items()} for v in csv_rows(timing_output)};assert set(observation)==set(tasks)
  return dict(valid=True,quality=quality),observation,directory
 initial,observation,initial_directory=evaluate(trees,'initial',prior/'native.route');assert initial['valid']
 frozen_quality=json.loads((prior/'native_validation/validation.json').read_text());current=initial['quality'];assert (current['total_wirelength'],current['critical_path_delay_ns'])==(frozen_quality['total_wirelength'],frozen_quality['critical_path_delay_ns'])
 state=dict(status='running_single_sweep',case=label,initial_quality=current,baseline_crossings=baseline_cross,steps=[],accepted=0,current_quality=current,current_tree=str(initial_directory/'route.route_trees.csv'),research_complete=False,adopted=False)
 atomic(D/'manifest.json',state)
 binder=make_binder(native,case['connections']);attempted=set();epoch=0;rank=0
 while rank<len(trees):
  if Decimal(str(current['critical_path_delay_ns']))<=Decimal(str(case['baseline_cpd_ns'])):
   state['termination_reason']='native_CPD_baseline_met';break
  bound=binder(initial_directory/'native_validation/report_timing.setup.rpt',case['baseline_cpd_ns'])
  candidates=[]
  for arc in bound['arcs']:
   if arc['intracluster']:continue
   task=int(arc['task']['id']);net=int(arc['task']['net_id'])
   if net not in attempted:
    candidates.append((-Decimal(next(p['effective_delay_ns'] for p in bound['paths'] if p['endpoint']==arc['endpoint'])),-observation[task]['delay_ps'],task,net,arc['endpoint']))
  if not candidates:state['termination_reason']='no_unattempted_bound_net_in_current_state';break
  selected=min(candidates);critical_task=selected[2];net=selected[3];attempted.add(net)
  started=time.monotonic_ns();before=trees[net];source=sources[net]
  step=dict(rank=rank,epoch=epoch,net=net,critical_task=critical_task,selected_endpoint=selected[4],status='searching',searches=[],accepted=False);state['steps'].append(step);atomic(D/'manifest.json',state)
  owners=[set() for _ in raw_nodes]
  for other,parent in trees.items():
   if other!=net:
    for v in parent:owners[v].add(other)
  allowed=[len(values)<resources[v][1] for v,values in enumerate(owners)]
  limit=Decimal(str(case['baseline_cpd_ns']));limit_ps=int(limit*1000)
  other_cross=crossings({other:tree for other,tree in trees.items() if other!=net})
  net_budget=baseline_cross-other_cross
  assert net_budget>=0
  requests=[]
  for task in sorted(by_net[net],key=lambda t:(t!=critical_task,-observation[t]['criticality_q'],t)):
   requests.append(dict(id=task,sink=int(tasks[task]['sink']),
                        delay_budget=max(0,observation[task]['delay_ps']+limit_ps+observation[task]['slack_ps']),
                        max_hops=int(tasks[task]['max_hops'])))
  answer=repair(raw_nodes,edges,allowed,length,dies,source,requests,net_budget,maximum_labels=2097152)
  parent=answer.get('parent',answer.get('private_parent',{}));complete=answer['complete']
  step['net_crossing_budget']=net_budget
  step['repair_status']=answer['status']
  for request,entry in zip(requests,answer['steps']):
   result=entry['search']
   step['searches'].append(dict(task=request['id'],delay_cap_ps=request['delay_budget'],
    before_crossings=entry['before_crossings'],status=result['status'],labels=result['labels'],expanded=result['expanded']))
  if not complete:step['status']='incomplete_private_net'
  elif parent==before:step['status']='canonical_tree_unchanged'
  elif wire(trees)-sum(length[v] for v in before)+sum(length[v] for v in parent)>max(current['total_wirelength'],case['baseline_wirelength']):step['status']='global_wire_budget_rejected'
  else:
   candidate=trees.copy();candidate[net]=parent;cross=crossings(candidate);step['candidate_crossings']=cross
   if cross>baseline_cross:step['status']='baseline_crossing_limit_rejected'
   else:
    checked,new_observation,directory=evaluate(candidate,'trial_'+str(rank)+'_net'+str(net));step['native_evidence']=str(directory);step['validation']=checked
    if checked['valid']:
     q=checked['quality'];quality_ok=q['total_wirelength']<=max(current['total_wirelength'],case['baseline_wirelength']);strict=q['critical_path_delay_ns']<current['critical_path_delay_ns']
     if quality_ok and strict:
      trees=candidate;current=q;observation=new_observation;initial_directory=directory;attempted=set();epoch+=1;state['accepted']+=1;step['accepted']=True;step['status']='accepted_private_native_state';state['current_tree']=str(directory/'route.route_trees.csv')
     else:step['status']='global_native_quality_rejected'
    else:step['status']='native_validation_failed_rejected'
  step['wall_ns']=time.monotonic_ns()-started;state['current_quality']=current;atomic(D/'manifest.json',state)
  print(json.dumps(dict(case=label,rank=rank,net=net,status=step['status'],accepted=state['accepted'],wire=current['total_wirelength'],cpd=current['critical_path_delay_ns'])),flush=True)
  rank+=1
 state.update(status='single_sweep_complete_requires_independent_review',final_crossings=crossings(trees),current_quality=current);atomic(D/'manifest.json',state)
 return state

def main():
 protocol=json.loads((P/'protocol.json').read_text())
 for f,h in protocol['source_sha256'].items():assert digest(f)==h,f
 state=dict(status='running_cases',pid=os.getpid(),cases=[],research_complete=False,adopted=False);atomic(P/'manifest.json',state)
 try:
  for case in protocol['cases']:
   result=run_case(case,protocol);state['cases'].append(dict(case=case['label'],status=result['status'],accepted=result['accepted'],quality=result['current_quality']));atomic(P/'manifest.json',state)
  state['status']='three_case_single_sweeps_complete_requires_independent_review';atomic(P/'manifest.json',state)
 except BaseException as error:
  state.update(status='failed_preserve_evidence',error=repr(error),traceback=traceback.format_exc());atomic(P/'manifest.json',state);raise
if __name__=='__main__':main()
