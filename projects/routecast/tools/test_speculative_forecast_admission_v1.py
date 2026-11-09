"""Physical/budget validation and no-mutation contract for explicit forecast-only guard."""
import json,hashlib,copy
from pathlib import Path
from speculative_forecast_objective_admission_v1 import prepare
from criticality_objective_admission_v1 import prepare as original
R=Path(__file__).resolve().parents[1];D=R/'experiments/speculative_forecast_admission_contract_v1_2026-10-19'
class RC:
 def initial(self,n):return 0
 def increment(self,e):return 1

def main():
 D.mkdir(exist_ok=False);fields=dict(capacities=[1]*4,edge_ids=[10,11,12,13],row_offsets=[0,2,3,4,4],dest_ranks=[1,2,3,3]);slots={x:i for i,x in enumerate(fields['edge_ids'])};q=dict(connection_id=0,net_id=7,source=0,sink=3);old=[dict(q,budget_integer=2,answer=dict(status='FOUND',physical_edge_ids=[10,12],delay=2))];new=[dict(q,budget_integer=2,answer=dict(status='FOUND',physical_edge_ids=[11,13],delay=2))];ledger={0:1,1:1,2:1,3:1};crit={0:dict(criticality_numerator=0,criticality_denominator=1)};before=copy.deepcopy([fields,old,new,ledger,crit]);tests=0
 for old_cost in range(1,11):
  for new_cost in range(1,11):
   costs={1:old_cost,2:new_cost};p=prepare(fields,RC(),slots,[q],old,new,ledger,crit,costs);o=original(fields,RC(),slots,[q],old,new,ledger,crit,costs);assert p['prospective_overflow_delta']==1 and p['updates']=={1:0,2:2};assert p['accepted']==(new_cost<=old_cost) and not o['accepted'];assert not p['eligible_for_legal_route_commit'];assert p['objective_delta']==new_cost-old_cost;tests+=1
 assert [fields,old,new,ledger,crit]==before
 errors=0
 for kind in ['budget','raw','metadata','missing_owner','bad_edge','multiple_parent']:
  f=copy.deepcopy(fields);a=copy.deepcopy(old);b=copy.deepcopy(new);l=ledger.copy();qs=[q]
  if kind=='budget':a[0]['budget_integer']=b[0]['budget_integer']=1
  elif kind=='raw':b[0]['answer']['delay']=3
  elif kind=='metadata':b[0]['budget_integer']=3
  elif kind=='missing_owner':l.pop(1)
  elif kind=='bad_edge':b[0]['answer']['physical_edge_ids']=[999]
  else:
   q2=dict(q,connection_id=1);qs=[q,q2];a.append(dict(a[0],connection_id=1));b.append(dict(b[0],connection_id=1,answer=dict(status='FOUND',physical_edge_ids=[10,12],delay=2)))
  try:prepare(f,RC(),slots,qs,a,b,l,crit,{1:10,2:1})
  except (ValueError,KeyError):errors+=1
  else:raise AssertionError(kind)
 assert errors==6
 files=[Path(__file__).resolve(),R/'tools/speculative_forecast_objective_admission_v1.py',R/'tools/criticality_net_admission_v1.py',R/'tools/criticality_objective_admission_v1.py'];(D/'verification.json').write_text(json.dumps(dict(status='FORECAST_ONLY_OBJECTIVE_GUARD_100_COST_FIXTURES_AND6_INVALID_PROPOSALS_PASS',cost_fixtures=tests,invalid_proposals=errors,input_state_unchanged=True,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='Unit proposal contract only. Positive forecast overflow permitted, no legal/native admission, original validation retained; no real prediction quality claim.'),indent=2)+'\n');print('FORECAST_ADMISSION_CONTRACT_PASS')
if __name__=='__main__':main()
