"""Exercise exact production audit function with valid and corrupted retry events."""
import ast,json,copy,hashlib
from pathlib import Path
from fractions import Fraction
from types import SimpleNamespace
R=Path(__file__).resolve().parents[1];D=R/'experiments/capacity_retry_event_auditor_contract_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);script=R/'tools/verify_external_capacity_retry_events_v1.py';node=next(x for x in ast.parse(script.read_text()).body if isinstance(x,ast.FunctionDef) and x.name=='audit_capacity_retry');us=[0,0,0,1,2,3];vs=[1,2,3,4,4,4];raw=[1,3,2,1,3,2];prices={1:0,2:10,3:2,4:0};query=dict(connection_id=0,net_id=0,source=0,sink=4);old=[dict(query,budget_integer=6,answer=dict(status='FOUND',physical_edge_ids=[1,4],delay=6))];original=[dict(old[0],answer=dict(status='FOUND',physical_edge_ids=[0,3],delay=2))];secondary=[dict(old[0],answer=dict(status='FOUND',physical_edge_ids=[2,5],delay=4))]
 def ownership(records):return {0}|{vs[e] for q in records for e in q['answer']['physical_edge_ids']}
 def physical(q,path,parents):
  u=0;total=0;seen={0}
  for e in path:
   assert us[e]==u and vs[e] not in seen;v=vs[e];assert v not in parents or parents[v]==(u,e);parents[v]=(u,e);seen.add(v);u=v;total+=raw[e]
  assert u==4;return total
 def objective(records):return sum((Fraction(q['answer']['delay'],2) for q in records),Fraction(0))+sum((Fraction(prices.get(n,0),2) for n in ownership(records)-{0}),Fraction(0))
 ns=dict(p={'capacity_retry':True},ownership=ownership,physical_path=physical,queries={0:query},ledger={0:1,1:1,2:1,4:1},xml=SimpleNamespace(graph=SimpleNamespace(nodes=[SimpleNamespace(capacity=1) for _ in range(5)])),union_objective=objective,Fraction=Fraction);exec(compile(ast.Module(body=[node],type_ignores=[]),str(script),'exec'),ns)
 retry=dict(original_candidate=original,original_pressure_delta=1,original_objective_guard=dict(old_score='8',candidate_score='1',objective_delta='-7'),original_status='RETAIN_OVERFLOW_INCREASE',secondary_candidate=secondary,selected=True,secondary_objective_guard=dict(old_score='8',candidate_score='3',objective_delta='-5'),secondary_pressure_delta=0,details=dict(max_labels=10000,old_owner_nodes=3,status='COMPLETE',prospective_overflow_delta=0));event=dict(status='COMMITTED',records=secondary,capacity_retry=retry);audit=ns['audit_capacity_retry'];clone=audit(event,old);assert clone['rejected_records']==original and clone['status']=='RETAIN_OVERFLOW_INCREASE'
 corruptions=[]
 def rejects(name,mutate):
  bad=copy.deepcopy(event);mutate(bad)
  try:audit(bad,old)
  except (AssertionError,ValueError):corruptions.append(name)
  else:raise AssertionError('corrupt event accepted: '+name)
 rejects('forbidden node candidate',lambda x:x['capacity_retry'].update(secondary_candidate=original))
 rejects('selection mismatch',lambda x:x['capacity_retry'].update(selected=False))
 rejects('raw budget drift',lambda x:x['capacity_retry']['secondary_candidate'][0].update(budget_integer=7))
 rejects('objective drift',lambda x:x['capacity_retry']['secondary_objective_guard'].update(candidate_score='2'))
 rejects('original overflow drift',lambda x:x['capacity_retry'].update(original_pressure_delta=0))
 unknown=copy.deepcopy(event);unknown['status']='RETAIN_OVERFLOW_INCREASE';unknown.pop('records');unknown['rejected_records']=original;unknown['capacity_retry'].update(secondary_candidate=None,selected=False,details=dict(max_labels=10000,old_owner_nodes=3,status='NO_COMPLETE_CANDIDATE'));audit(unknown,old)
 files=[Path(__file__),script,R/'tools/run_external_capacity_retry_v1.py'];(D/'verification.json').write_text(json.dumps(dict(status='VALID_RETRY_AND_UNKNOWN_ACCEPTED_FIVE_CORRUPTIONS_REJECTED',corruptions_rejected=corruptions,unknown_preserves_original_rejection=True,bindings={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}),indent=2)+'\n');print('VALID_RETRY_AND_UNKNOWN_ACCEPTED_FIVE_CORRUPTIONS_REJECTED')
if __name__=='__main__':main()
