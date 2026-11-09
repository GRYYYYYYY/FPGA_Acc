"""Independent occurrence-driven RUP checker; no solver or core-extractor imports."""
from collections import defaultdict, deque


def verify(clauses, result):
    database = [frozenset(c) for c in clauses]
    occurrences = defaultdict(set)
    for index, clause in enumerate(database):
        for literal in clause:
            occurrences[literal].add(index)
    for addition in result['rup_additions']:
        assignment = {}
        active = {i: set(c) for i, c in enumerate(database)}
        pending = deque(-literal for literal in addition)
        pending.extend(next(iter(c)) for c in database if len(c) == 1)
        conflict = any(not c for c in database)
        while pending and not conflict:
            literal = pending.popleft()
            variable = abs(literal)
            if variable in assignment:
                conflict = assignment[variable] != (literal > 0)
                continue
            assignment[variable] = literal > 0
            for index in occurrences[literal]:
                active.pop(index, None)
            for index in occurrences[-literal]:
                residual = active.get(index)
                if residual is None:
                    continue
                residual.discard(-literal)
                if not residual:
                    conflict = True
                    break
                if len(residual) == 1:
                    pending.append(next(iter(residual)))
        assert conflict, 'non-RUP addition'
        index = len(database)
        clause = frozenset(addition)
        database.append(clause)
        for literal in clause:
            occurrences[literal].add(index)
    if result['status'] == 'UNSAT':
        assert [] in result['rup_additions']
    if result['status'] == 'SAT':
        model = {int(k): v for k, v in result['model'].items()}
        assert all(any(model[abs(x)] == (x > 0) for x in c) for c in clauses)
    else:
        assert result['model'] is None
