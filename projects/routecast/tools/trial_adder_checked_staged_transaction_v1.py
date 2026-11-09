"""Actual archived cross-place hybrid transaction fault-injection experiment."""
import json,time
from threading import Barrier,Thread
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from transaction_shared_tree_ledger_v1 import TransactionLedger
from staged_place_route_transaction_v1 import PlaceRouteStore,StaleEpoch
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_checked_staged_transaction_v1_2026-10-09';D.mkdir(exist_ok=False);start=time.perf_counter()
F=E/'adder_legal_route_budget_fixture_v1_2026-10-09';H=E/'adder_direct_from_inputs_checked_wire_paths_verification_v6_2026-10-09';V=E/'adder_direct_from_inputs_checked_wire_native_quality_v6_2026-10-09/verification.json'
v=json.loads(V.read_text());bindings={**v['bindings'],str(V):sha(V),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());plans=json.loads((F/'receipt.json').read_text())['plans'];graph,digest,nodes,fields,rc,_=load_endpoints(plans[0]['endpoints']);length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
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
for step in range(3,4):
 old={int(c):p for c,p in json.loads(Path(plans[step-1]['state']).read_text())['state'].items()};target={int(c):p for c,p in json.loads((H/'selection.json').read_text())['paths'].items()};oq={q['connection_id']:q for q in json.loads(Path(plans[step-1]['endpoints']).read_text())['connections']};tq={q['connection_id']:q for q in json.loads(Path(plans[step]['endpoints']).read_text())['connections']}
 nets={tq[c]['net_id'] for c in target if tuple(tuple(x) for x in target[c])!=tuple(tuple(x) for x in old[c]) or oq[c]!=tq[c]};replacements={c:p for c,p in target.items() if tq[c]['net_id'] in nets};base=TransactionLedger(old,oq,fields['capacities'],length);store=PlaceRouteStore(base);before=image(store.snapshot()[1]);events=[];staged=store.stage(tq,replacements,events.append)
 def validate(t):check(t);assert t.state=={c:tuple(tuple(x) for x in p) for c,p in target.items()}
 store.commit(staged,validate,events.append);assert image(base)==before;assert store.snapshot()[0]==1;check(store.snapshot()[1])
 # Each failure reruns from the same committed source, including late validation/publication.
 faults=0
 for label in events:
  trial=PlaceRouteStore(base)
  def fail(here):
   if here==label:raise Injected(here)
  try:trial.commit(trial.stage(tq,replacements,fail),validate,fail)
  except Injected:pass
  else:raise AssertionError('missed checkpoint '+label)
  epoch,unchanged=trial.snapshot();assert epoch==0 and image(unchanged)==before;faults+=1
 trial=PlaceRouteStore(base);pending=trial.stage(tq,replacements)
 def reject(t):raise Injected('validator rejected')
 try:trial.commit(pending,reject)
 except Injected:pass
 else:raise AssertionError('validator accepted')
 assert trial.snapshot()[0]==0 and image(trial.snapshot()[1])==before
 trial.commit(pending,validate);after=image(trial.snapshot()[1])
 try:trial.commit(pending,validate)
 except StaleEpoch:pass
 else:raise AssertionError('stale accepted')
 assert trial.snapshot()[0]==1 and image(trial.snapshot()[1])==after
 # Two independently staged candidates race at the same epoch.
 race=PlaceRouteStore(base);first=race.stage(tq,replacements);second=race.stage(tq,replacements);barrier=Barrier(2);outcomes=[]
 def racer(candidate):
  def synchronized_validate(t):validate(t);barrier.wait(timeout=30)
  try:outcomes.append(('committed',race.commit(candidate,synchronized_validate)))
  except StaleEpoch:outcomes.append(('stale',None))
  except BaseException as error:outcomes.append(('error',repr(error)))
 threads=[Thread(target=racer,args=(candidate,)) for candidate in (first,second)]
 for thread in threads:thread.start()
 for thread in threads:thread.join(timeout=40)
 assert not any(thread.is_alive() for thread in threads)
 assert sorted(status for status,value in outcomes)==['committed','stale'],outcomes
 assert race.snapshot()[0]==1;validate(race.snapshot()[1])
 row=dict(step=step,released_and_inserted_connections=len(replacements),fault_checkpoints=faults,all_failure_committed_state_and_epoch_unchanged=True,validator_rejection_atomic=True,stale_commit_rejected=True,concurrent_same_epoch_one_commit_one_stale=True,success_matches_native_certified_hybrid=True);rows.append(row);print(row,flush=True)
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,component_seconds=time.perf_counter()-start,scope='In-memory isolated copy staging and publication, single step3 cross-place fault injection with fresh-produced checked-v6 native-certified paths. Not native internal rollback, filesystem crash durability, online path production, broad concurrent stress, independent timing targets or speedup.'),indent=2)+'\n')
