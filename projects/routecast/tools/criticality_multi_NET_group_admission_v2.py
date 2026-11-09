"""Pure group admission prototype; private preparation, no shared-state mutation.

A new multi-NET transaction unit, not the existing single-NET admission policy.
Caller must atomically publish the complete accepted plan after rechecking epochs.
One group-owner-excluded immutable price view must serve every old/new NET score.
"""
from collections import Counter
from fractions import Fraction
from criticality_net_admission_v1 import prepare as physical_prepare
from criticality_objective_admission_v1 import score

def prepare(fields,rc,slots,group_queries,old_records,candidate_records,ledger,criticalities,node_costs,epochs,expected_epochs):
 nets=set(group_queries)
 if not nets or any(type(n) is not int or n<0 for n in nets):raise ValueError('group NET domain')
 if any(set(x)!=nets for x in [old_records,candidate_records,expected_epochs]):raise ValueError('group coverage')
 if any(type(expected_epochs[n]) is not int or expected_epochs[n]<0 or type(epochs.get(n)) is not int or epochs.get(n)!=expected_epochs[n] for n in nets):raise ValueError('stale group epochs')
 seen=set();plans={};old_owners=Counter();new_owners=Counter();before=Fraction(0);after=Fraction(0)
 for net in sorted(nets):
  queries=group_queries[net];ids={q['connection_id'] for q in queries}
  if not queries or any(q['net_id']!=net for q in queries) or seen&ids:raise ValueError('group query identity')
  seen.update(ids)
  plan=physical_prepare(fields,rc,slots,queries,old_records[net],candidate_records[net],ledger);plans[net]=plan
  old_owners.update(plan['old_audit']['owned']);new_owners.update(plan['candidate_audit']['owned'])
  before+=score(fields,slots,old_records[net],criticalities,node_costs,plan['old_audit']['delays'])
  after+=score(fields,slots,candidate_records[net],criticalities,node_costs,plan['candidate_audit']['delays'])
 updates={};overflow_delta=0
 for node in old_owners.keys()|new_owners.keys():
  count=ledger.get(node,0)
  if type(count) is not int or count<old_owners[node]:raise ValueError('group old ownership absent')
  new=count-old_owners[node]+new_owners[node]
  if new!=count:
   updates[node]=new;cap=fields['capacities'][node];overflow_delta+=max(0,new-cap)-max(0,count-cap)
 delta=after-before;accepted=overflow_delta<=0 and delta<=0
 return dict(accepted=accepted,status='GROUP_ADMIT' if accepted else 'GROUP_RETAIN_OBJECTIVE_INCREASE' if delta>0 else 'GROUP_RETAIN_OVERFLOW_INCREASE',updates=updates,prospective_overflow_delta=overflow_delta,old_score=before,candidate_score=after,objective_delta=delta,NET_plans=plans,expected_epochs=dict(expected_epochs),scope='Private read-only plan; atomic publication and real-workload search/gain remain unimplemented.')
