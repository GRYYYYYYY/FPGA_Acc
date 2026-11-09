"""Heuristic budget preservation; actual complete candidates require timing gates."""
from fractions import Fraction as F

def allocate_budget(floor, expanded, initial, target, restrictions, supported, evaluate):
    value = evaluate(floor)
    valid = supported and value <= target and all(floor[c] <= 1 for c in expanded)
    budget = {}
    policy = 'UNIFORM_INTERPOLATION'
    alpha = F(0)
    if valid:
        if not restrictions:
            budget = dict(initial)
            assert evaluate(budget) <= target
            assert all(floor[c] <= budget[c] <= 1 for c in expanded)
            policy = 'INITIAL_NET_SLACK_VECTOR'
            alpha = None
        else:
            preserved = {c: max(initial[c], v) for c, v in floor.items()}
            if all(preserved[c] <= 1 for c in expanded):
                budget = preserved
                policy = 'HEURISTIC_PRESERVE_WITH_CONDITIONAL_FLOORS'
                alpha = None
            else:
                budget = dict(floor)
                high = F(1)
                for _ in range(24):
                    mid = (alpha + high) / 2
                    trial = {c: v + mid * (1-v) if c in expanded else v
                             for c, v in floor.items()}
                    if evaluate(trial) <= target:
                        budget = trial
                        alpha = mid
                    else:
                        high = mid
    return value, valid, budget, policy, alpha
