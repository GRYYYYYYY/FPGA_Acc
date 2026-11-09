"""Separate policy: retain physical/budget guards; admit by frozen objective only.

Positive intermediate overflow is permitted and explicitly recorded. This is
not the original monotone-overflow contract or joint-route legality.
"""
from criticality_net_admission_v1 import prepare as physical_prepare
from criticality_objective_admission_v1 import score


def prepare(fields, rc, slots, queries, old_records, candidate_records,
            ledger, criticalities, node_costs):
    plan = physical_prepare(fields, rc, slots, queries, old_records,
                            candidate_records, ledger)
    before = score(fields, slots, old_records, criticalities, node_costs,
                   plan['old_audit']['delays'])
    after = score(fields, slots, candidate_records, criticalities, node_costs,
                  plan['candidate_audit']['delays'])
    delta = after - before
    updates = plan['rejected_updates'] if plan['prospective_overflow_delta'] > 0 else plan['updates']
    accepted = delta <= 0
    return dict(plan, updates=updates if accepted else {},
                rejected_updates={} if accepted else updates,
                accepted=accepted,
                status='COMMITTED' if accepted else 'RETAIN_OBJECTIVE_INCREASE',
                old_score=before, candidate_score=after, objective_delta=delta,
                original_monotone_overflow_gate_claimed=False,
                scope='Objective-only admission with unchanged physical paths, raw budgets and tree checks. Positive overflow changes permitted; no joint legality or timing/utility claim.')
