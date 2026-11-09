"""Pure complete-NET exact delay gate; caller authenticates RC witnesses."""
from fractions import Fraction


def admit_rc_net(baseline, candidate):
    if not baseline or set(baseline) != set(candidate):
        raise ValueError('complete identical connection cohort required')
    for values in (baseline, candidate):
        if any(not isinstance(v, Fraction) or v < 0 for v in values.values()):
            raise ValueError('nonnegative exact Fraction delay required')
    failures = sorted(cid for cid in baseline if candidate[cid] > baseline[cid])
    return {'accepted': not failures, 'failing_connections': failures}
