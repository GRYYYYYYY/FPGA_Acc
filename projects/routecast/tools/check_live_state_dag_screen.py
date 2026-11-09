"""Independent full-relaxation comparisons and unchanged published state."""
import json, random
from fractions import Fraction as F
from pathlib import Path
from live_state_dag_screen import LiveStateDAGScreen
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
def full(nodes,edges,sinks,delays):
    arrival=dict.fromkeys(nodes,F(0))
    for _ in nodes:
        for u,v,offset,c in edges:
            arrival[v]=max(arrival[v],arrival[u]+offset+(delays[c] if c is not None else 0))
    return max(arrival[n] for n in sinks)
rng=random.Random(1007);checks=0
for _ in range(100):
    nodes=list(range(20));sinks=[17,18,19]
    edges=[(u,v,F(rng.randrange(8),11),str(rng.randrange(6)) if rng.random()<.8 else None) for v in nodes for u in range(v) if rng.random()<.15]
    rng.shuffle(edges)
    old={str(c):F(rng.randrange(20),17) for c in range(6)}
    gate=LiveStateDAGScreen(nodes,edges,sinks,old,100)
    initial=(dict(gate._dag.arrivals),dict(gate._dag.budgets))
    for _ in range(30):
        new={str(c):F(rng.randrange(30),19) for c in range(6)};wire=rng.randrange(90,111)
        result=gate.trial(new,wire,complete=True)
        assert F(result['candidate_model_cpd_ns'])==full(nodes,edges,sinks,new)
        assert F(result['published_model_cpd_ns'])==full(nodes,edges,sinks,old)
        assert result['model_admitted']==(wire<=100 and full(nodes,edges,sinks,new)<=full(nodes,edges,sinks,old))
        assert (gate._dag.arrivals,gate._dag.budgets)==initial
        checks+=1
    assert gate.trial(old,100,complete=True)['model_admitted']
    assert not gate.trial(None,None,complete=False)['model_admitted']
    for vector,wire in [({},100),({**old,'extra':F(1)},100),({**old,'0':-1},100),({**old,'0':1.0},100),({**old,'0':True},100),(old,True),(old,-1),({**old,0:F(1)},100)]:
        try:gate.trial(vector,wire,complete=True)
        except ValueError:pass
        else:raise AssertionError('invalid input admitted')
        assert (gate._dag.arrivals,gate._dag.budgets)==initial
out=ROOT/'experiments/live_state_dag_screen_contract_2026-10-07';out.mkdir(exist_ok=True)
result=dict(sources={str(p):sha(p) for p in [Path(__file__),ROOT/'tools/live_state_dag_screen.py',ROOT/'tools/exact_incremental_timing_dag.py']},random_graphs=100,trial_comparisons=checks,invalid_input_checks=800,status='PASS',scope='Serial synthetic full recurrence parity, complete vector binding and published state preservation. No prospective/native quality/net gain claim.')
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
