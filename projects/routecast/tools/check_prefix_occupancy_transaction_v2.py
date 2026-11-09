"""Transaction orchestration contract: multi-request commit and exact rollback."""
import copy,json
from unittest.mock import patch
from pathlib import Path
import mcnc_prefix_occupancy_sequence_v8 as module
queries=[dict(connection_id=i,net_id=i,source=0,sink=1) for i in range(3)]
old=dict(queries[0],answer=dict(physical_edge_ids=[],delay=0),budget_integer=1)
state=dict(records=[old],ledger={'0':1},failure=dict(status='NO_BUDGET_CAPACITY_PATH',query=queries[1]))
selection=dict(queries=queries[1:],requested_connection_ids=[1,2],released_net_ids=[0],removed_connection_ids=[0],witness_evidence=[],stop='ALL_PENDING_SELECTED')
new=[old]+[dict(q,answer=dict(physical_edge_ids=[],delay=0),budget_integer=1) for q in queries[1:]]
for success in (False,True):
 initial=copy.deepcopy(state);solution=dict(records=copy.deepcopy(new),ledger={'0':3},failure=None) if success else None
 calls=[]
 def predictor(*args,**kwargs):
  calls.append(copy.deepcopy(kwargs['seed_records']))
  if len(calls)==1:return copy.deepcopy(initial)
  return dict(records=copy.deepcopy(kwargs['seed_records']),ledger={'0':3},failure=None)
 def joint(*args,**kwargs):
  assert args[2]=={1:[queries[1]],2:[queries[2]],0:[queries[0]]} and args[4]==[]
  return dict(status='FOUND_JOINT_BATCH' if success else 'JOINT_NODE_LIMIT',solution=solution,branches=[])
 with patch.object(module,'base_predict',predictor),patch.object(module,'select',return_value=copy.deepcopy(selection)),patch.object(module,'joint_route',joint):
  result,events,stop=module.sequence({'edge_ids':[]},None,queries,{},spans=[])
 assert initial==state and len(events)==1
 if success:assert stop=='COMPLETE' and len(result['records'])==3 and calls==[[],new]
 else:assert stop=='BATCH_ROLLBACK' and result['records']==state['records'] and result['ledger']==state['ledger'] and calls==[[]]
 assert events[0]['committed']==success
out=Path(__file__).resolve().parents[1]/'experiments/prefix_occupancy_transaction_contract_v2_2026-10-07';out.mkdir(exist_ok=True);(out/'receipt.json').write_text(json.dumps(dict(multi_request_commit=True,exact_rollback=True,scope='Mock orchestration contract; physical routing independently audited on actual cohort.'))+'\n');print('PASS transaction commit/rollback')
