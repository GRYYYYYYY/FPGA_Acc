"""Exact rational enumeration tests for weighted implication-closed assignments."""
import itertools,json,math,random
from fractions import Fraction
from pathlib import Path
from weighted_closed_state_marginals_v1 import calculate
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]


def main():
    out=R/'experiments/weighted_closed_state_marginals_contract_v1_2026-10-19';out.mkdir(exist_ok=False);checks=0;nodes=range(3);possible=[(u,v) for u in nodes for v in nodes if u!=v]
    for mask in range(64):
        edges=[e for i,e in enumerate(possible) if mask>>i&1]
        for odds in itertools.product([Fraction(1,2),Fraction(1),Fraction(2)],repeat=3):
            result=calculate({i:math.log(float(odds[i])) for i in nodes},edges);Z=Fraction();sums={i:Fraction() for i in nodes}
            for choice in range(8):
                selected={i for i in nodes if choice>>i&1}
                if not all(u not in selected or v in selected for u,v in edges):continue
                weight=math.prod(odds[i] for i in selected);Z+=weight
                for i in selected:sums[i]+=weight
            assert math.isclose(result['log_partition'],math.log(float(Z)),rel_tol=1e-12,abs_tol=1e-12)
            for i in nodes:assert math.isclose(result['marginals'][i],float(sums[i]/Z),rel_tol=1e-12,abs_tol=1e-12)
            checks+=1
    for theta in [1000.,-1000.]:
        result=calculate({0:theta,1:-theta},[(0,1)]);assert math.isfinite(result['log_partition']) and all(0<=p<=1 for p in result['marginals'].values())
    empty=calculate({},[]);assert empty['log_partition']==0 and empty['marginals']=={}
    # Long chain coverage without listing its exponentially many bit patterns:
    # a uniform chain has n+1 suffix states, P(x_i=1)=(i+1)/(n+1).
    n=80;result=calculate({i:0. for i in range(n)},[(i,i+1) for i in range(n-1)])
    assert math.isclose(result['log_partition'],math.log(n+1),abs_tol=1e-12)
    for i in range(n):assert math.isclose(result['marginals'][i],(i+1)/(n+1),abs_tol=1e-12)
    paths=[Path(__file__).resolve(),R/'tools/weighted_closed_state_marginals_v1.py'];(out/'verification.json').write_text(json.dumps(dict(status='ALL3NODE_GRAPHS_RATIONAL_WEIGHTED_ENUMERATION_EXTREME_LOGS_AND_CHAIN_MARGINALS_PASS',rational_enumeration_checks=checks,chain_nodes=n,bindings={str(p):sha(p) for p in paths},scope='Complete combinatorial coverage with stable floating log partition/marginals; numerical rather than exact rational output. No actual route ensemble or forecast quality claim.'),indent=2)+'\n');print('WEIGHTED_CLOSED_STATE_MARGINAL_CONTRACT_PASS',checks,flush=True)


if __name__=='__main__':main()
