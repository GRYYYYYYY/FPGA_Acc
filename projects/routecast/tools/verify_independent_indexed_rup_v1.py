"""Exhaustive oracle and deliberate invalid-certificate rejection."""
import itertools, json, random
from pathlib import Path
from certified_cnf_dependency_cdcl_v2 import solve
from independent_indexed_rup_verify_v1 import verify
from native_resume_prototype.source_binding_v2 import closure
from pre_route_endpoints import sha

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    out = root / 'experiments/independent_indexed_rup_verification_v1_2026-10-09'
    out.mkdir(exist_ok=False)
    rng = random.Random(93742)
    counts = {}; additions = 0
    cases = [[], [[]], [[1, -1]], [[1, 1], [-1]], [[1], [-1]]]
    cases += [[[rng.choice([-1, 1])*rng.randint(1, 6) for _ in range(rng.randint(1, 3))] for _ in range(rng.randint(3, 24))] for _ in range(80)]
    for clauses in cases:
        truth = any(all(any(v[abs(x)-1] == (x > 0) for x in c) for c in clauses) for v in itertools.product([False, True], repeat=6))
        result = solve(clauses, 6)
        assert (result['status'] == 'SAT') == truth
        verify(clauses, result)
        counts[result['status']] = counts.get(result['status'], 0) + 1
        additions += len(result['rup_additions'])
    rejected = 0
    for clauses, result in [([[1, 2]], dict(status='UNSAT', model=None, rup_additions=[[]])), ([[1]], dict(status='SAT', model={1: False}, rup_additions=[])), ([[1]], dict(status='UNSAT', model=None, rup_additions=[[2], []]))]:
        try:
            verify(clauses, result)
        except AssertionError:
            rejected += 1
        else:
            raise AssertionError('invalid certificate accepted')
    bindings = closure([Path(__file__)])
    assert all(sha(p) == h for p, h in bindings.items())
    report = dict(bindings=bindings, cases=len(cases), status_counts=counts, rup_additions=additions, invalid_certificates_rejected=rejected)
    (out / 'verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print({k:v for k,v in report.items() if k != 'bindings'})
