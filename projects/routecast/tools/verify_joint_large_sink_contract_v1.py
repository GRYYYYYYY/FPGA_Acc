"""Synthetic cardinality/limit contracts, not a real RR performance trial."""
import hashlib,json
from pathlib import Path
from budget_joint_candidates_incremental_v2 import select
cases=[]
for n in (501,1001,5784):
    adj={0:[(s-1,s,1,2) for s in range(1,n+1)]}
    budgets={s:1 for s in range(1,n+1)}
    candidates={s:[[s-1]] for s in range(1,n+1)}
    limited=select(adj,0,budgets,candidates,max_states=n)
    assert limited==dict(status='UNKNOWN_STATE_LIMIT',paths=None,union_cost=None,states=n)
    result=select(adj,0,budgets,candidates,max_states=n+1)
    assert result['status']=='OPTIMAL_WITHIN_CANDIDATES' and result['states']==n+1
    assert set(result['paths'])==set(budgets) and result['union_cost']==3*n
    # Independent star graph oracle: all leaves require their distinct root arc.
    edge_ids=set()
    for sink,path in result['paths'].items():
        assert path==[sink-1] and budgets[sink]>=1
        edge_ids.add(path[0])
    assert len(edge_ids)==n
    cases.append(dict(sinks=n,complete_states=n+1,union_cost=3*n,limit_without_incumbent_is_unknown=True))
root=Path(__file__).resolve().parents[1]
out=root/'experiments/joint_large_sink_contract_v1_2026-10-09';out.mkdir(exist_ok=False)
files=[Path(__file__),root/'tools/budget_joint_candidates_incremental_v2.py',root/'tools/budget_NET_gate_reference_v1.py']
r=dict(all_pass=True,cases=cases,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='Synthetic single-candidate stars verify cardinality above recursive depth and exact state boundaries. Not realistic candidate branching, complete original RR coverage, memory bound or measured acceleration.')
(out/'verification.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
