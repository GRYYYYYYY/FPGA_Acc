"""Pure, same-snapshot whole-NET objective and overflow admission."""
from fractions import Fraction
from criticality_net_admission_v1 import prepare as physical_prepare

def score(fields,slots,records,criticalities,node_costs,validated_delays):
 users={};raw=Fraction(0)
 for rec in records:
  cid=rec['connection_id'];row=criticalities[cid]
  c=Fraction(row['criticality_numerator'],row['criticality_denominator'])
  if not 0<=c<=1:raise ValueError('criticality range')
  raw+=c*validated_delays[cid]
  for eid in rec['answer']['physical_edge_ids']:
   node=fields['dest_ranks'][slots[eid]];users[node]=max(users.get(node,Fraction(0)),c)
 congestion=Fraction(0)
 for node,c in users.items():
  cost=node_costs.get(node,0)
  if type(cost) is not int or cost<0:raise ValueError('node cost')
  congestion+=(1-c)*cost
 return raw+congestion

def prepare(fields,rc,slots,queries,old_records,candidate_records,ledger,criticalities,node_costs):
 """Read-only proposal. Caller commits only when accepted is true.

 node_costs must be one frozen, old-owner-excluded snapshot shared by both
 scores. Ties preserve existing overflow-only admission semantics.
 """
 plan=physical_prepare(fields,rc,slots,queries,old_records,candidate_records,ledger)
 before=score(fields,slots,old_records,criticalities,node_costs,plan['old_audit']['delays'])
 after=score(fields,slots,candidate_records,criticalities,node_costs,plan['candidate_audit']['delays'])
 delta=after-before
 accepted=plan['prospective_overflow_delta']<=0 and delta<=0
 status='COMMITTED' if accepted else 'RETAIN_OBJECTIVE_INCREASE' if delta>0 else 'RETAIN_OVERFLOW_INCREASE'
 return dict(plan,accepted=accepted,status=status,old_score=before,candidate_score=after,objective_delta=delta)
