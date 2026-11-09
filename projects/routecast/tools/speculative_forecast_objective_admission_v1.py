"""Private forecast proposal: preserve physical/budget checks, accept objective nonincrease.

May increase forecast overflow. Never an admission for a legal/native route commit.
"""
from criticality_net_admission_v1 import prepare as physical_prepare
from criticality_objective_admission_v1 import score

def prepare(fields,rc,slots,queries,old_records,candidate_records,ledger,criticalities,node_costs):
    plan=physical_prepare(fields,rc,slots,queries,old_records,candidate_records,ledger)
    before=score(fields,slots,old_records,criticalities,node_costs,plan['old_audit']['delays'])
    after=score(fields,slots,candidate_records,criticalities,node_costs,plan['candidate_audit']['delays'])
    delta=after-before
    updates=plan['rejected_updates'] if plan['prospective_overflow_delta']>0 else plan['updates']
    return dict(plan,updates=updates,accepted=delta<=0,status='COMMITTED' if delta<=0 else 'RETAIN_OBJECTIVE_INCREASE',old_score=before,candidate_score=after,objective_delta=delta,eligible_for_legal_route_commit=False)
