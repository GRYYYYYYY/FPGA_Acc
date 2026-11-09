"""Transaction orchestration contract: multi-request commit and exact rollback."""
import copy,json
from unittest.mock import patch
from pathlib import Path
import mcnc_pending_swap_sequence_v12 as module
queries=[dict(connection_id=i,net_id=i,source=0,sink=1) for i in range(3)]
old=dict(queries[0],answer=dict(physical_edge_ids=[],delay=0),budget_integer=1)
state=dict(records=[old],ledger={'0':1},failure=dict(status='NO_BUDGET_CAPACITY_PATH',query=queries[1]))
selection=dict(queries=queries[1:],requested_connection_ids=[1,2],released_net_ids=[0],removed_connection_ids=[0],witness_evidence=[],stop='ALL_PENDING_SELECTED')
new=[old]+[dict(q,answer=dict(physical_edge_ids=[],delay=0),budget_integer=1) for q in queries[1:]]
for primary_success,fallback_success,swap_success in ((True,False,False),(False,False,False),(False,True,False),(False,False,True)):
 success=primary_success or fallback_success or swap_success
 initial=copy.deepcopy(state);solution=dict(records=copy.deepcopy(new),ledger={'0':3},failure=None) if success else None
 calls=[];joint_calls=[]
 def predictor(*args,**kwargs):
  calls.append(copy.deepcopy(kwargs['seed_records']))
  if len(calls)==1:return copy.deepcopy(initial)
  return dict(records=copy.deepcopy(kwargs['seed_records']),ledger={'0':3},failure=None)
 def joint(*args,**kwargs):
  joint_calls.append(1);found=primary_success or (len(joint_calls)>1 and swap_success)
  assert args[2]=={1:[queries[1]],2:[queries[2]],0:[queries[0]]} and args[4]==[]
  return dict(status='FOUND_JOINT_BATCH' if found else 'JOINT_NODE_LIMIT',solution=solution if found else None,branches=[])
 def fallback(*args,**kwargs):
  assert args[3]==queries[1:] and args[2]==state['records']
  return dict(status='FOUND_JOINT_BATCH' if fallback_success else 'REPAIR_EXHAUSTED',solution=solution if fallback_success else None,released_net_ids=[0],attempts=[])
 with patch.object(module,'propose',return_value=dict(proposed=[[0]] if swap_success else [],domains=[],checks=[])),patch.object(module,'repair',fallback),patch.object(module,'base_predict',predictor),patch.object(module,'select',return_value=copy.deepcopy(selection)),patch.object(module,'joint_route',joint):
  result,events,stop=module.sequence({'edge_ids':[]},None,queries,{},spans=[])
 assert initial==state and len(events)==1
 if success:assert stop=='COMPLETE' and len(result['records'])==3 and calls==[[],new]
 else:assert stop=='BATCH_ROLLBACK' and result['records']==state['records'] and result['ledger']==state['ledger'] and calls==[[]]
 assert events[0]['committed']==success
out=Path(__file__).resolve().parents[1]/'experiments/pending_swap_transaction_contract_v4_2026-10-07';out.mkdir(exist_ok=True);(out/'receipt.json').write_text(json.dumps(dict(multi_request_commit=True,exact_rollback=True,scope='Mock orchestration contract; physical routing independently audited on actual cohort.'))+'\n');print('PASS transaction commit/rollback')
