"""Independent Fraction full-rebuild oracle for every proposed leaf flip."""
import json
import random
from fractions import Fraction as F
from pathlib import Path
from spatial_leaf_decoder_v1 import solve
from exact_factor_elimination_v1 import sha


def energy(leaves, truth, memberships, capacities, states):
    point = [states[v] for v in leaves]
    value = F(sum(p != y for p, y in zip(point, truth)), len(truth))
    for j, capacity in enumerate(capacities):
        predicted = sum(p for p, bins in zip(point, memberships) if j in bins)
        target = sum(y for y, bins in zip(truth, memberships) if j in bins)
        value += F((predicted - target) ** 2, len(capacities) * capacity ** 2)
    return value


def main():
    rng = random.Random(20261020)
    decisions = accepted = ties = 0
    for trial in range(500):
        n, b, k = rng.randint(1, 50), rng.randint(1, 12), rng.randint(1, 10)
        leaves = [rng.randrange(k) for _ in range(n)]
        truth = [rng.randrange(2) for _ in range(n)]
        memberships = [[j for j in range(b) if rng.randrange(4) == 0] for _ in range(n)]
        capacities = [rng.randint(1, 20) for _ in range(b)]
        initial = {v: rng.randrange(2) for v in range(k)}
        original = initial.copy()
        result = solve(leaves, truth, memberships, capacities, initial)
        assert initial == original and result['states'] is not initial
        states = initial.copy()
        current = energy(leaves, truth, memberships, capacities, states)
        assert current == F(result['initial_energy'], result['denominator'])
        index = 0
        for sweep in range(16):
            flips = 0
            for leaf in sorted(states):
                proposal = {**states, leaf: 1 - states[leaf]}
                candidate = energy(leaves, truth, memberships, capacities, proposal)
                expected = candidate < current
                trace = result['trace'][index]
                assert trace == {'sweep': sweep, 'leaf': leaf,
                                 'before': int(current * result['denominator']),
                                 'delta': int((candidate - current) * result['denominator']),
                                 'accepted': expected}
                assert F(trace['delta'], result['denominator']) == candidate - current
                decisions += 1
                ties += candidate == current
                if expected:
                    states, current = proposal, candidate
                    flips += 1
                    accepted += 1
                index += 1
            if flips == 0:
                break
        assert index == len(result['trace']) and states == result['states']
        assert current == F(result['final_energy'], result['denominator'])
        if result['converged']:
            for leaf in states:
                assert energy(leaves, truth, memberships, capacities,
                              {**states, leaf: 1 - states[leaf]}) >= current
    root = Path(__file__).resolve().parents[1]
    out = root / 'experiments/spatial_leaf_decoder_contract_v1_2026-10-20'
    out.mkdir(exist_ok=False)
    files = [Path(__file__), root / 'tools/spatial_leaf_decoder_v1.py',
             root / 'experiments/wbuart_spatial_leaf_decoder_design_v1_2026-10-20/protocol.json']
    record = {'status': 'PASS_INDEPENDENT_FRACTION_FULL_REBUILD', 'tiny_trials': 500,
              'decisions': decisions, 'accepted': accepted, 'retained_ties': ties,
              'bindings': {str(p): sha(p) for p in files},
              'scope': 'Solver qualification only; no real models fitted or quality claim.'}
    (out / 'verification.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k: v for k, v in record.items() if k != 'bindings'}))


if __name__ == '__main__':
    main()
