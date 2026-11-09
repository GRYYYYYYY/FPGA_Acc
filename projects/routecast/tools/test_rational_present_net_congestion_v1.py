"""Independent branched oracle, native float32 coefficient decoding, unit-factor parity."""
import json,random,struct
from pathlib import Path
from fractions import Fraction
from rational_present_net_congestion_v1 import cost
from multiplicative_net_congestion_v1 import cost as old
from pre_route_endpoints import sha
rng=random.Random(20261010)
for i in range(5000):
 b=rng.randrange(1000000000);c=rng.randrange(1,30);o=rng.randrange(60);owner=bool(rng.randrange(2)) if o else False;h=rng.randrange(40);s=rng.randrange(1000000)
 pf=Fraction.from_float(struct.unpack('f',struct.pack('f',rng.random()*80))[0]);a=Fraction(1+h)
 remaining=o-(1 if owner else 0)
 if remaining<c: expected=Fraction(b*(1+h)+s)
 else:expected=Fraction(b*(1+h))+b*(1+h)*(remaining-c+1)*pf+s
 assert cost(b,a,o,c,pf,owner,s)==expected
 assert cost(b,a,o,c,Fraction(1),owner,s)==old(b,h,o,c,owner,s)
 assert cost(b,a,o,c,Fraction(0),owner,s)==b*(1+h)+s
 if owner:assert cost(b,a,o,c,pf,True,s)==cost(b,a,o-1,c,pf,False,s)
bad=[(1,Fraction(1),0,1,Fraction(-1)),(1,Fraction(0),0,1,Fraction(1)),(True,Fraction(1),0,1,Fraction(1)),(1,Fraction(1),0,1,1),(1,Fraction(1),0,1,Fraction(1),True)]
for args in bad:
 try:cost(*args)
 except ValueError:pass
 else:raise AssertionError('invalid input accepted')
R=Path(__file__).resolve().parents[1];O=R/'experiments/rational_present_cost_contract_v1_2026-10-10';O.mkdir()
files=[Path(__file__),R/'tools/rational_present_net_congestion_v1.py',R/'tools/multiplicative_net_congestion_v1.py']
(O/'verification.json').write_text(json.dumps({'bindings':{str(f.resolve()):sha(f) for f in files},'independent_branched_oracle_cases':5000,'unit_present_matches_existing_integer_cost':True,'zero_present_removes_occupancy_term':True,'virtual_release_identity_pass':True,'invalid_cases':len(bad),'scope':'Primitive cost contract only; no native graph replay, native float intermediate arithmetic parity, prediction/QoR/heldout/speed proof.'},indent=2)+'\n');print('RATIONAL PRESENT CONTRACT PASS')
