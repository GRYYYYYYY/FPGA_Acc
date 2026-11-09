"""Preserve old admission except changed-path neutral transactions."""
from criticality_objective_admission_v1 import prepare as original_prepare

def filter_plan(plan,old,candidate):
 before={q['connection_id']:(q['source'],q['sink'],tuple(q['answer']['physical_edge_ids'])) for q in old}
 after={q['connection_id']:(q['source'],q['sink'],tuple(q['answer']['physical_edge_ids'])) for q in candidate}
 if set(before)!=set(after):raise ValueError('CID mismatch')
 result=dict(plan)
 if plan['accepted'] and before!=after and plan['objective_delta']==0 and plan['prospective_overflow_delta']==0:
  result.update(accepted=False,status='RETAIN_NO_STRICT_PROGRESS')
 return result

def prepare(*args):
 return filter_plan(original_prepare(*args),args[4],args[5])
