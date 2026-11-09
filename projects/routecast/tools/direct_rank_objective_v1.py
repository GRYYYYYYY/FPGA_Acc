"""Exact training-only ranking objective; original evaluation remains separate."""
from fractions import Fraction as F

def components(predicted, truth, k):
    if set(predicted) != set(truth) or not predicted or not 1 <= k <= len(truth):
        raise ValueError('aligned nonempty domain and valid K required')
    keys = sorted(truth)
    def ranks(values):
        order = sorted(keys, key=lambda key: values[key])
        result = {}; i = 0
        while i < len(order):
            j = i + 1
            while j < len(order) and values[order[j]] == values[order[i]]:
                j += 1
            for key in order[i:j]: result[key] = i + j - 1
            i = j
        return result
    a, b = ranks(predicted), ranks(truth)
    center = len(keys) - 1
    covariance = sum((a[key]-center)*(b[key]-center) for key in keys)
    variance = sum((a[key]-center)**2 for key in keys)*sum((b[key]-center)**2 for key in keys)
    rank = F(covariance*abs(covariance), variance) if variance else F(-2)
    p = sorted(keys, key=lambda key: (-predicted[key], key))[:k]
    t = sorted(keys, key=lambda key: (-truth[key], key))[:k]
    return (rank, F(len(set(p)&set(t)), k))

def objective(cases):
    """Each item: {'candidate': four Fractions, 'controls': two four-vectors}."""
    failed = negative = 0; deficit = gain = F(0)
    if not cases: raise ValueError('nonempty cases required')
    for case in cases:
        candidate, controls = case['candidate'], case['controls']
        if len(candidate) != 4 or len(controls) != 2 or any(len(c) != 4 for c in controls):
            raise ValueError('four metrics and two original controls required')
        for control in controls:
            diff = [F(a)-F(b) for a,b in zip(candidate,control)]
            # A sentinel candidate is never a valid nonregressing rho.
            valid = candidate[0] != -2 and candidate[2] != -2 and control[0] != -2 and control[2] != -2
            failed += not (valid and all(d >= 0 for d in diff) and any(d > 0 for d in diff))
            negative += sum(d < 0 for d in diff)
            deficit += sum((-d for d in diff if d < 0), F(0))
            gain += sum(diff, F(0))
    return (failed, negative, deficit, -gain)
