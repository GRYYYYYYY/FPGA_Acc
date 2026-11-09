"""Endpoint-compatible branch opportunity, not a retained physical tree certificate."""
import json
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
prior=R/'experiments/endpoint_changed_incremental_scope_v1_2026-10-08/diagnosis.json'
certificate=json.loads(prior.read_text())
assert certificate['complete_cases']==12 and all(sha(p)==h for p,h in certificate['bindings'].items())
P=R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json'
bindings={**certificate['bindings'],str(prior):sha(prior),str(Path(__file__)):sha(Path(__file__))}
rows=[]
for case,expected in zip(json.loads(P.read_text())['cases'],certificate['rows']):
    previous={q['connection_id']:q for q in json.loads(Path(case['old']).read_text())['connections']}
    current=json.loads(Path(case['target']).read_text())['connections'];groups=defaultdict(list)
    for q in current:groups[q['net_id']].append(q)
    assert (case['width'],case['index'])==(expected['width'],expected['index'])
    dirty=set();source_changed=set();changed=0
    for net,qs in groups.items():
        assert len({q['source'] for q in qs})==len({previous[q['connection_id']]['source'] for q in qs})==1
        for q in qs:
            old=previous[q['connection_id']]
            if (q['source'],q['sink'])!=(old['source'],old['sink']):dirty.add(net);changed+=1
            if q['source']!=old['source']:source_changed.add(net)
    compatible=sum(q['net_id'] in dirty and q['net_id'] not in source_changed and q['sink']==previous[q['connection_id']]['sink'] for q in current)
    assert changed==expected['changed_endpoint_connections'] and len(dirty)==expected['changed_endpoint_nets']
    assert compatible+changed==expected['whole_NET_released_connections']
    rows.append(dict(width=case['width'],index=case['index'],source_changed_nets=len(source_changed),
        sink_only_changed_nets=len(dirty-source_changed),endpoint_compatible_branches_inside_changed_NETs=compatible,
        changed_endpoint_connections=changed,whole_NET_released_connections=expected['whole_NET_released_connections']))
assert len(rows)==12 and all(sha(p)==h for p,h in bindings.items())
D=R/'experiments/endpoint_changed_branch_scope_v1_2026-10-08';D.mkdir(exist_ok=False)
(D/'diagnosis.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,
    scope='Identity opportunity only for known development moves. Source-changed NETs require replacing every old rooted branch. Source-fixed/sink-changed NETs may retain endpoint-compatible paths only after shared-parent/tree, physical arcs, ownership, current budgets, changed prices and native import invariants are verified. No routing, speed, heldout or native QoR claim.'),indent=2)+'\n')
print(json.dumps(rows,indent=2))
