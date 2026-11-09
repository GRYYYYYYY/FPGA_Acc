"""Original XML universe and direct model/native ledgers authenticate complete transition accounting."""
import json,xml.etree.ElementTree as E
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_feedback_resource_transitions_v1_2026-10-10';p=D/'diagnosis.json';v=json.loads(p.read_text());assert all(sha(q)==h for q,h in v['bindings'].items());bindings={str(p):sha(p),str(Path(__file__).resolve()):sha(Path(__file__))};checked=0
for case,model,native,ep in [('original','sha1_frozen_model_v1_2026-10-10/sha1','sha1_native_cold_v1_2026-10-10/sha1','sha1_native_demand_v1_2026-10-10/sha1'),('second_swap','sha_second_swap_complete_workflow_v1_2026-10-10/seed/model/sha1','sha_second_swap_complete_workflow_v1_2026-10-10/cold/native/sha1','sha_second_swap_complete_workflow_v1_2026-10-10/cold/demand/sha1')]:
 model=R/'experiments'/model;native=R/'experiments'/native;ep=R/'experiments'/ep/'endpoints.json';e=json.loads(ep.read_text());graph=Path(e['inputs']['graph']['path']);assert sha(graph)==e['graph_sha256'];universe=set();stack=[]
 for event,x in E.iterparse(graph,events=['start','end']):
  if event=='start':stack.append(x);continue
  if x.tag=='node' and x.get('type') in ['CHANX','CHANY'] and int(x.get('capacity'))>0:
   assert int(x.get('capacity'))==1;universe.add(int(x.get('id')))
  if x.tag in ['node','edge']:
   if len(stack)>1:stack[-2].remove(x)
   x.clear()
  stack.pop()
 assert len(universe)==28188
 truth=json.loads((native/'physical_audit.json').read_text())['node_occupancy'];initial=json.loads((model/'initial.json').read_text())['ledger']
 for method,filename in [('round0_shared','round0.json'),('final_shared','sketch.json')]:
  row=next(r for r in v['rows'] if r['case']==case and r['method']==method);feedback=json.loads((model/filename).read_text())['ledger'];seen=set();totals={k:0 for k in row['totals']}
  for cell in row['matrix']:
   t,a,b=cell['truth'],cell['initial'],cell['feedback'];ids=cell['nodes'];n=cell['count'];assert n==len(ids)==len(set(ids)) and not seen.intersection(ids);seen.update(ids)
   for node in ids:assert (truth.get(str(node),0),initial.get(str(node),0),feedback.get(str(node),0))==(t,a,b)
   before,after=abs(a-t),abs(b-t)
   terms=dict(resources=1,truth_occupied=t,initial_absolute_error=before,feedback_absolute_error=after,improved_nodes=int(after<before),worsened_nodes=int(after>before),improvement_units=max(0,before-after),worsening_units=max(0,after-before),removed_true_occupancy=int(t==1 and a>0 and b==0),added_false_occupancy=int(t==0 and a==0 and b>0),removed_false_occupancy=int(t==0 and a>0 and b==0),added_true_occupancy=int(t==1 and a==0 and b>0))
   for key,value in terms.items():totals[key]+=n*value
  assert seen==universe and totals==row['totals'];checked+=1
  bindings[str(model/filename)]=sha(model/filename)
 for q in [graph,ep,native/'physical_audit.json',model/'initial.json']:bindings[str(q)]=sha(q)
assert checked==4 and all(sha(q)==h for q,h in bindings.items());(D/'independent_verification.json').write_text(json.dumps(dict(bindings=bindings,all4_complete_XML_universe_direct_native_and_model_ledger_transition_accounting_pass=True,scope='Exact discrete count error decomposition; no causal explanation or unseen-family prediction proof.'),indent=2)+'\n');print('FULL TRANSITION ACCOUNTING PASS',checked)
