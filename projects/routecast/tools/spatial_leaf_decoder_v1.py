"""Exact coordinate descent for the frozen binary leaf-state objective.

Rows carry leaf indices, binary truth, and case-bin indices. Capacities are
positive integers. Bin indices must distinguish cases, even at equal geometry.
"""
from math import lcm


def solve(leaves, truth, memberships, capacities, initial, max_sweeps=16):
    n, b = len(leaves), len(capacities)
    if not n or not b or len(truth) != n or len(memberships) != n:
        raise ValueError('nonempty, aligned inputs required')
    if max_sweeps != 16 or any(type(c) is not int or c <= 0 for c in capacities):
        raise ValueError('frozen sweep limit and positive integer capacities required')
    states = dict(initial)
    if any(type(v) is not int or v not in (0, 1) for v in states.values()):
        raise ValueError('binary initial states required')
    stats = {leaf: [0, 0, {}] for leaf in states}
    target, predicted = [0] * b, [0] * b
    errors = 0
    for leaf, y, bins in zip(leaves, truth, memberships):
        if leaf not in states or type(y) is not int or y not in (0, 1):
            raise ValueError('unknown leaf or nonbinary truth')
        if len(set(bins)) != len(bins) or any(type(j) is not int or not 0 <= j < b for j in bins):
            raise ValueError('invalid or duplicate bin incidence')
        s = stats[leaf]
        s[0] += 1
        s[1] += y
        errors += states[leaf] != y
        for j in bins:
            s[2][j] = s[2].get(j, 0) + 1
            target[j] += y
            predicted[j] += states[leaf]
    denominator = lcm(n, *(b * c * c for c in capacities))
    resource_weight = denominator // n
    weights = [denominator // (b * c * c) for c in capacities]
    residual = [p - y for p, y in zip(predicted, target)]
    energy = resource_weight * errors + sum(w * d * d for w, d in zip(weights, residual))
    start = energy
    trace = []
    converged = False
    for sweep in range(16):
        flips = 0
        for leaf in sorted(states):
            count, positive, incidence = stats[leaf]
            sign = 1 - 2 * states[leaf]
            delta = resource_weight * sign * (count - 2 * positive)
            delta += sum(weights[j] * (2 * sign * residual[j] * k + k * k)
                         for j, k in incidence.items())
            accept = delta < 0
            trace.append({'sweep': sweep, 'leaf': leaf, 'before': energy,
                          'delta': delta, 'accepted': accept})
            if accept:
                states[leaf] ^= 1
                for j, k in incidence.items():
                    residual[j] += sign * k
                energy += delta
                flips += 1
        if not flips:
            converged = True
            break
    return {'states': states, 'denominator': denominator, 'initial_energy': start,
            'final_energy': energy, 'trace': trace, 'converged': converged,
            'sweeps': sweep + 1}
