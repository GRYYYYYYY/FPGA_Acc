"""Pure whole-NET quality admission. Caller authenticates witnesses and budgets."""
from fractions import Fraction


def admit_net(baseline, candidate):
    """Exact no-regression gate, no state mutation or implicit graph validation."""
    if not baseline or set(baseline) != set(candidate):
        raise ValueError('complete identical connection cohort required')
    failures = []
    for cid in sorted(baseline):
        old, new = baseline[cid], candidate[cid]
        for row in (old, new):
            if type(row['scalar']) is not int or row['scalar'] < 0:
                raise ValueError('invalid scalar')
            if not isinstance(row['delay'], Fraction):
                raise ValueError('exact Fraction delay required')
        if new['scalar'] > old['scalar'] or new['delay'] > old['delay']:
            failures.append(cid)
    return {'accepted': not failures, 'failing_connections': failures}
