"""One store, three native-certified generated updates, every checkpoint and epoch race."""
import json,time
from pathlib import Path
from collections import Counter,defaultdict
from threading import Thread,Barrier
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
from class_cached_rc_endpoint_context_v1 import load_endpoints
from transaction_shared_tree_ledger_v1 import TransactionLedger
from staged_place_route_transaction_v1 import PlaceRouteStore,StaleEpoch
from content_bound_path_audit_v1 import PathAudit
from fractions import Fraction
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'cached_history_publication_v1_2026-10-09';D.mkdir(exist_ok=False);start=time.perf_counter()
F=E/'adder_legal_route_budget_fixture_v1_2026-10-09';plans=json.loads((F/'receipt.json').read_text())['plans'];bindings=closure([Path(__file__)])
for namespace in ('fresh_history_workflow_v1_stage_6_2026-10-09','history_step2_v1_stage_6_2026-10-09','history_step3_v1_stage_6_2026-10-09'):
 p=E/namespace/'verification.json';v=json.loads(p.read_text());assert all(sha(f)==h for f,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
graph,digest,nodes,fields,rc,_=load_endpoints(plans[0]['endpoints']);length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
path_audit=PathAudit(graph,digest)
old={int(c):p for c,p in json.loads(Path(plans[0]['state']).read_text())['state'].items()};oq={q['connection_id']:q for q in json.loads(Path(plans[0]['endpoints']).read_text())['connections']};store=PlaceRouteStore(TransactionLedger(old,oq,fields['capacities'],length))
normalize=lambda obj:{k:dict(v) for k,v in obj.items() if v}
def image(t):return (t.state,t.queries,normalize(t.nodes),normalize(t.parents),normalize(t.parent_uses),dict(t.occupancy),dict(t.wire))
def check(t):
 counts=defaultdict(Counter);parents=defaultdict(dict);uses=defaultdict(Counter)
 for cid,path in t.state.items():
  q=t.queries[cid];assert path[0]==(q['source'],None) and path[-1][0]==q['sink'];net=q['net_id'];counts[net].update(n for n,s in path)
  for (u,_),(v,s) in zip(path,path[1:]):
   assert v not in parents[net] or parents[net][v]==(u,s);parents[net][v]=(u,s);uses[net][v]+=1
 occupancy=Counter(n for counts in counts.values() for n in counts);wire={net:sum(length.get(n,0) for n in used) for net,used in counts.items()}
 assert normalize(t.nodes)==normalize(counts) and normalize(t.parents)==normalize(parents) and normalize(t.parent_uses)==normalize(uses)
 assert t.occupancy==occupancy and all(c<=fields['capacities'][n] for n,c in occupancy.items()) and dict(t.wire)==wire
class Injected(RuntimeError):pass
rows=[]
for step,namespace in [(1,'fresh_history_workflow_v1_stage_2_2026-10-09'),(2,'history_step2_v1_stage_2_2026-10-09'),(3,'history_step3_v1_stage_2_2026-10-09')]:
 target={int(c):p for c,p in json.loads((E/namespace/'result.json').read_text())['paths'].items()};tq={q['connection_id']:q for q in json.loads(Path(plans[step]['endpoints']).read_text())['connections']}
 epoch,base=store.snapshot();assert epoch==step-1;before=image(base);old=base.state;oq=base.queries
 if step>=2:
  previous=json.loads((E/('fresh_history_workflow_v1_stage_2_2026-10-09' if step==2 else 'history_step2_v1_stage_2_2026-10-09')/'result.json').read_text())['paths'];assert old=={int(c):tuple(tuple(x) for x in p) for c,p in previous.items()}
 nets={tq[c]['net_id'] for c in target if tuple(tuple(x) for x in target[c])!=old[c] or oq[c]!=tq[c]};replacements={c:p for c,p in target.items() if tq[c]['net_id'] in nets}
 budgetp=E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step}_budgets.json'
 budgets={row['connection_id']:Fraction(*row['exact_delay_s']) for row in json.loads(budgetp.read_text())};bindings[str(budgetp)]=sha(budgetp)
 hits_before=path_audit.hits;misses_before=path_audit.misses
 def validate(t):
  check(t);assert t.state=={c:tuple(tuple(x) for x in p) for c,p in target.items()}
  path_audit.validate(t.state,t.queries,budgets)
 events=[];pending=store.stage(tq,replacements,events.append)
 def stop_before_publish(label):
  events.append(label)
  if label=='before_publish':raise Injected(label)
 try:store.commit(pending,validate,stop_before_publish)
 except Injected:pass
 else:raise AssertionError('publication stop missed')
 assert store.snapshot()[0]==epoch and image(store.snapshot()[1])==before
 tested_checkpoints=['snapshot','validated','before_publish']
 for label in tested_checkpoints:
  def fail(here):
   if here==label:raise Injected(here)
  try:store.commit(store.stage(tq,replacements,fail),validate,fail)
  except Injected:pass
  else:raise AssertionError('missed checkpoint '+label)
  assert store.snapshot()[0]==epoch and image(store.snapshot()[1])==before
 def reject(t):
  tightened=dict(budgets);cid=next(iter(t.state));delay=path_audit.certificate(t.state[cid])[0]
  assert delay>0;tightened[cid]=delay/2
  try:path_audit.validate(t.state,t.queries,tightened)
  except AssertionError:raise Injected('positive budget tightening rejected')
  raise AssertionError('cached validation accepted invalid budget')
 try:store.commit(pending,reject)
 except Injected:pass
 else:raise AssertionError('validator accepted')
 assert store.snapshot()[0]==epoch and image(store.snapshot()[1])==before
 candidates=[store.stage(tq,replacements),store.stage(tq,replacements)];barrier=Barrier(2);outcomes=[]
 def racer(candidate):
  def synchronized(t):validate(t);barrier.wait(timeout=30)
  try:outcomes.append(('committed',store.commit(candidate,synchronized)))
  except StaleEpoch:outcomes.append(('stale',None))
  except BaseException as error:outcomes.append(('error',repr(error)))
 threads=[Thread(target=racer,args=(candidate,)) for candidate in candidates]
 for thread in threads:thread.start()
 for thread in threads:thread.join(timeout=40)
 assert not any(thread.is_alive() for thread in threads)
 assert sorted(status for status,value in outcomes)==['committed','stale'],outcomes
 assert store.snapshot()[0]==epoch+1;validate(store.snapshot()[1]);after=image(store.snapshot()[1])
 try:store.commit(pending,validate)
 except StaleEpoch:pass
 else:raise AssertionError('stale accepted')
 assert store.snapshot()[0]==epoch+1 and image(store.snapshot()[1])==after
 p=D/f'step_{step}_committed.json';p.write_text(json.dumps(dict(epoch=epoch+1,paths=store.snapshot()[1].state),indent=2)+'\n');bindings[str(p)]=sha(p)
 row=dict(step=step,prior_epoch=epoch,committed_epoch=epoch+1,replaced_connections=len(replacements),fault_checkpoints=len(tested_checkpoints),cached_hits=path_audit.hits-hits_before,cached_misses=path_audit.misses-misses_before,all_failure_state_epoch_preserved=True,validator_rejection_atomic=True,one_concurrent_commit_one_stale=True,stale_commit_rejected=True,complete_target_matches=True);rows.append(row);print(row,flush=True)
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,component_seconds=time.perf_counter()-start,scope='Archived accepted selections, persistent graph/path certificate cache, targeted checkpoint qualification only. Not fresh production or timing benchmark. Same in-memory store carries actual generated/native-certified step1 then step2 then step3, epochs0->1->2->3; every checkpoint failure preserves actual prior committed epoch/state. Two threads compete each update. No native internal rollback, filesystem crash durability, generated step0 initial routing, independent timing specification or runtime gain.'),indent=2)+'\n')
