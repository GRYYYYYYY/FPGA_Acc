"""Compare native partitions with independent all-pairs directed reachability."""
import hashlib
import json
import random
from pathlib import Path
from zero_rc_scc_bridge_v1 import partition

ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / 'experiments/zero_rc_scc_build_v1_2026-10-08/scc.so'
rng = random.Random(20261008)
pairs = 0
for case in range(200):
    n = rng.randrange(1, 40)
    cap = [rng.randrange(3) for _ in range(n)]
    adjacency = [[] for _ in range(n)]
    row, dest, inc = [0], [], []
    for u in range(n):
        for _ in range(rng.randrange(n * 2 + 1)):
            v, cost = rng.randrange(n), rng.choice([0, 0, 1, 2**63])
            dest.append(v)
            inc.append(cost)
            if cap[u] and cap[v] and cost == 0:
                adjacency[u].append(v)
        row.append(len(dest))
    labels, count = partition(dict(capacities=cap, row_offsets=row,
                                   dest_ranks=dest), inc, BINARY)
    reach = []
    for u in range(n):
        seen, todo = ({u}, [u]) if cap[u] else (set(), [])
        while todo:
            for v in adjacency[todo.pop()]:
                if v not in seen:
                    seen.add(v)
                    todo.append(v)
        reach.append(seen)
    enabled_labels = {labels[u] for u in range(n) if cap[u]}
    assert enabled_labels == set(range(count))
    for u in range(n):
        if not cap[u]:
            assert labels[u] == 2**64 - 1
            continue
        for v in range(n):
            if cap[v]:
                assert (labels[u] == labels[v]) == (v in reach[u] and u in reach[v])
                pairs += 1

files = [Path(__file__), ROOT/'tools/zero_rc_scc_bridge_v1.py',
         ROOT/'tools/soft_demand_cpp/zero_rc_scc_v1.cpp', BINARY]
result = dict(pass_all=True, graphs=200, enabled_node_pairs=pairs,
              bindings={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in files},
              scope='Primitive partition only; no real graph, path lifting or speed claim')
out = ROOT/'experiments/zero_rc_scc_contract_v1_2026-10-08'
out.mkdir(exist_ok=True)
(out/'verification.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result))
