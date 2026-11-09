"""Complete old/target endpoint identity census; no routing or cost inference."""
import json
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
P=R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json'
protocol=json.loads(P.read_text())
bindings={str(P):sha(P),str(Path(__file__)):sha(Path(__file__)),str(R/'tools/pre_route_endpoints.py'):sha(R/'tools/pre_route_endpoints.py')}
for path,h in protocol['sources'].items():assert sha(path)==h;bindings[path]=h
rows=[]
for case in protocol['cases']:
    for path,h in case['inputs'].items():assert sha(path)==h;bindings[path]=h
    old_path,target_path=Path(case['old']),Path(case['target'])
    old,target=[json.loads(p.read_text()) for p in [old_path,target_path]]
    bindings.update({str(p):sha(p) for p in [old_path,target_path]})
    for ep in [old,target]:
        for value in ep['inputs'].values():assert sha(value['path'])==value['sha256'];bindings[value['path']]=value['sha256']
    assert old['graph_sha256']==target['graph_sha256'] and old['inputs']['net']==target['inputs']['net']
    assert old['net_names']==target['net_names']
    previous={q['connection_id']:q for q in old['connections']}
    current={q['connection_id']:q for q in target['connections']}
    assert len(previous)==len(old['connections']) and len(current)==len(target['connections'])
    assert previous.keys()==current.keys()
    groups=defaultdict(list);changed=[]
    for cid,q in current.items():
        before=previous[cid];assert before['net_id']==q['net_id']
        groups[q['net_id']].append(cid)
        if (before['source'],before['sink'])!=(q['source'],q['sink']):changed.append(cid)
    dirty={current[cid]['net_id'] for cid in changed}
    released=sum(len(groups[n]) for n in dirty)
    rows.append(dict(width=case['width'],index=case['index'],connections=len(current),nets=len(groups),
        changed_endpoint_connections=len(changed),changed_endpoint_nets=len(dirty),
        whole_NET_released_connections=released,retained_endpoint_compatible_connections=len(current)-released,
        dirty_NET_fraction=len(dirty)/len(groups),released_connection_fraction=released/len(current)))
assert len(rows)==12 and all(sha(p)==h for p,h in bindings.items())
D=R/'experiments/endpoint_changed_incremental_scope_v1_2026-10-08';D.mkdir(exist_ok=False)
result=dict(bindings=bindings,complete_cases=len(rows),rows=rows,
    scope='All original connections of 12 known mux development moves. Same graph/packed NET IDs and named identities authenticated. Endpoint-compatible count alone proves neither retained route legality, unchanged weighted optimality under price changes, native QoR nor net speedup. Build/parse/audit costs and amortization must be measured, no strict heldout claim.')
(D/'diagnosis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(rows,indent=2))
