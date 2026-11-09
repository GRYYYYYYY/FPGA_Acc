"""Execution preflight over previously verified floor proofs; never a QoR acceptance gate."""
import json
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha


class InvalidEvidence(ValueError):
    pass


def preflight(admission_path, authority_path, endpoints_path, budget_path):
    paths = [Path(p).resolve() for p in
             (admission_path, authority_path, endpoints_path, budget_path)]
    ap, vp, ep, bp = paths
    before = {str(p): sha(p) for p in paths}
    a, v, endpoints, budget = [json.loads(p.read_text()) for p in paths]
    if any(sha(p) != before[str(p)] for p in paths):
        raise InvalidEvidence('Input changed during evidence read')
    if v.get('all_twelve_cases_independent_admission_pass') is not True:
        raise InvalidEvidence('Missing independent complete-cohort verification')
    for document in (a, v):
        for path, digest in document['bindings'].items():
            if sha(path) != digest:
                raise InvalidEvidence('Stale binding: ' + path)
    if v['bindings'].get(str(ap)) != sha(ap):
        raise InvalidEvidence('Admission is not bound by independent verification')
    for p in (ep, bp):
        if a['bindings'].get(str(p)) != sha(p):
            raise InvalidEvidence('Current input differs from certified input: ' + str(p))
    queries = {q['connection_id']: q for q in endpoints['connections']}
    rows = a['rows']
    if (len(queries) != len(endpoints['connections']) or
            len(rows) != len(queries) or
            {r['connection_id'] for r in rows} != set(queries)):
        raise InvalidEvidence('Incomplete or duplicate connection coverage')
    blockers = []
    for r in rows:
        floor = Fraction(r['minimum_seconds']) * 10**9
        limit = Fraction(budget['budgets_ns'].get(
            str(r['connection_id']), budget['default_budget_ns']))
        feasible = floor <= limit
        if floor < 0 or limit < 0 or limit != Fraction(r['budget_ns']):
            raise InvalidEvidence('Invalid floor or budget')
        if r['relaxed_path_budget_feasible'] != feasible:
            raise InvalidEvidence('Incorrect admission arithmetic')
        if not feasible:
            blockers.append(dict(connection_id=r['connection_id'],
                                 minimum_ns=str(floor), budget_ns=str(limit),
                                 unavoidable_excess_ns=str(floor-limit)))
    if a['admitted'] != (not blockers):
        raise InvalidEvidence('Incorrect aggregate admission')
    if any(sha(p) != before[str(p)] for p in paths):
        raise InvalidEvidence('Input changed during admission verification')
    return dict(
        decision=('SKIP_CERTIFIED_MODEL_INFEASIBLE' if blockers
                  else 'CONTINUE_FULL_ROUTING_AND_ACCEPTANCE'),
        run_candidate_pipeline=not blockers, connections=len(queries),
        blockers=blockers,
        bindings=before,
        scope='Consumes prior verified, exact buffered-RC relaxed-floor proofs. '
              'Skip proves model-budget infeasibility only; continue does not '
              'prove joint capacity, native STA or HDL equivalence. Cache proof '
              'production cost is not timed or amortized here; no budgets changed.')
