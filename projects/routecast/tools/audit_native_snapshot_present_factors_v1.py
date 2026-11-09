"""Full-node frozen-state normalized cost factor diagnostic; no path search."""
import json,struct
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
from rational_present_net_congestion_v1 import cost
R=Path(__file__).resolve().parents[1];O=R/'experiments/mmc_native_iteration_state_observer_v2_2026-10-10'
v=json.loads((O/'common_state_projection_verification_v1.json').read_text());assert v['all21rounds_common_state_fields_exactly_equal'];assert all(sha(p)==h for p,h in v['bindings'].items())
rows=[]
for iteration in range(1,22):
 path=O/'states'/f'round_{iteration}.tsv';assert sha(path)==v['bindings'][str(path)];cases=changed=0;maximum_ratio=Fraction(0)
 with path.open() as s:
  for line in s:
   f=line.split()
   if f[0]=='H':pf=Fraction.from_float(struct.unpack('f',struct.pack('f',float(f[2])))[0])
   elif f[0]=='N':
    occ,cap=int(f[2]),int(f[3]);acc=Fraction.from_float(struct.unpack('f',struct.pack('f',float(f[4])))[0])
    for owner in ([False,True] if occ else [False]):
     observed=cost(1,acc,occ,cap,pf,owner);fixed=cost(1,acc,occ,cap,Fraction(1),owner)
     pressure=occ-int(owner)-cap+1
     expected=acc if pressure<=0 else acc+acc*pressure*pf
     assert observed==expected;cases+=1;changed+=observed!=fixed;maximum_ratio=max(maximum_ratio,observed/fixed)
 rows.append({'iteration':iteration,'cases':cases,'changed_normalized_cost_cases':changed,'maximum_observed_to_unit_ratio':str(maximum_ratio),'present_factor':str(pf)})
 print('PRESENT FACTOR',iteration,cases,changed,flush=True)
b={**v['bindings'],str(O/'common_state_projection_verification_v1.json'):sha(O/'common_state_projection_verification_v1.json'),str(Path(__file__).resolve()):sha(Path(__file__)),str(R/'tools/rational_present_net_congestion_v1.py'):sha(R/'tools/rational_present_net_congestion_v1.py')};assert all(sha(p)==h for p,h in b.items())
f=O/'normalized_present_factor_diagnostic_v1.json';assert not f.exists();f.write_text(json.dumps({'bindings':b,'rows':rows,'scope':'All-node frozen post-round state normalized cost factor with hypothetical old-owner cases; acc/state held fixed, only present factor changed. Not actual per-net search snapshots, native float arithmetic equivalence, primary paths, controlled trajectory effect, hotspot quality or causal proof.'},indent=2)+'\n')
