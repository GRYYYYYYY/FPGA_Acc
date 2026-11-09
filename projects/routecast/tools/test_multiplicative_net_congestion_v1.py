"""Independent Fraction native-factor oracle and owner-release metamorphic checks."""
from pathlib import Path
from fractions import Fraction
import random,json,sys
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from multiplicative_net_congestion_v1 import cost
from source_binding_v2 import closure
from pre_route_endpoints import sha
rng=random.Random(20261010);cases=0
for _ in range(5000):
 base=rng.randrange(10**9);history=rng.randrange(20);cap=rng.randrange(1,10);occ=rng.randrange(30);owner=bool(occ and rng.randrange(2));static=rng.randrange(10**9)
 # Native form expressed independently by branch on virtual released occupancy.
 released=occ-int(owner);pres=Fraction(1) if released<cap else Fraction(2+released-cap)
 oracle=Fraction(base)*Fraction(1+history)*pres+static
 actual=cost(base,history,occ,cap,owner,static);assert actual==oracle
 assert actual==cost(base,history,released,cap,False,static)
 assert cost(base,history+1,occ,cap,owner,static)-actual==base*pres
 assert cost(base,history,occ,cap,owner,static+1)==actual+1
 cases+=1
for args in [(-1,0,0,1),(1,-1,0,1),(1,0,0,1,True),(1,0,1,0),(True,0,0,1)]:
 try:cost(*args)
 except ValueError:pass
 else:raise AssertionError('invalid domain accepted')
assert cost(143062507,1,1,1,True)==286125014
assert cost(572250026,1,1,1,True)==1144500052
out=R/'experiments/multiplicative_net_congestion_contract_v1_2026-10-10';out.mkdir(exist_ok=False)
b=closure([Path(__file__)]);assert all(sha(p)==h for p,h in b.items())
(out/'verification.json').write_text(json.dumps(dict(bindings=b,cases=cases,invalid_cases=5,fraction_native_factor_and_virtual_release_checks_pass=True,scope='Cost primitive only, chosen acc/pres factors1; static span separate. Not native runtime parameters, full transactions, hotspot quality, heldout or end-to-end proof.'),indent=2)+'\n')
print('MULTIPLICATIVE COST CONTRACT PASS',cases)
