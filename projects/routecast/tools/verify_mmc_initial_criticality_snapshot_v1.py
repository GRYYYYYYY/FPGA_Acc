"""Admit initial capture by explicit routed-pin subset; preserve failed count assertion."""
import json,sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pre_route_endpoints import sha
R=Path.cwd();O=R/'experiments/mmc_native_initial_criticality_snapshot_v1_2026-10-10';P=R/'experiments/mmc_native_criticality_observer_v1_2026-10-10/verification.json'
b=json.loads((O/'startup.json').read_text())['bindings'];prior=json.loads(P.read_text());b.update(prior['bindings']);b[str(P)]=sha(P)
assert all(sha(p)==h for p,h in b.items())
assert not (O/'output.route').exists()
assert 'ROUTECAST INITIAL CRITICALITY SNAPSHOT 119473' in (O/'native.log').read_text()
def read(path,first_only):
 d={};count=0
 for line in path.read_text().splitlines():
  x=line.split();count+=1;assert x[0]=='C' and int(x[1])==count
  k=int(x[2]),int(x[4]);v=float(x[5]);assert math.isfinite(v) and 0<=v<=float(x[6])+1e-7
  if not first_only:assert k not in d
  d.setdefault(k,(int(x[3]),v,x[6],x[7]))
 return d,count
initial,count=read(O/'criticality.tsv',False);first,_=read(P.parent/'criticality.tsv',True)
assert count==119473 and len(first)==115572 and set(first)<=set(initial)
changed=[dict(net=k[0],local_pin=k[1],snapshot=initial[k],first_observed=first[k]) for k in first if first[k]!=initial[k]]
extra=sorted(set(initial)-set(first));assert len(extra)==3901
for p in [O/'startup.json',O/'criticality.tsv',O/'native.log',Path(__file__).resolve()]:b[str(p)]=sha(p)
source=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src/route/route_net.tpp';b[str(source)]=sha(source)
result=dict(bindings=b,all_clustered_sink_pins=count,routed_manifest_connections=len(first),extra_nonobserved_pins=len(extra),extra_pin_examples=extra[:20],changed_routed_connections=len(changed),changed_examples=changed[:20],initial_equals_first_observed_on_routed_manifest=not changed,no_output_route=True,scope='First getter snapshot before its caller connection search. Enumerates entire clustered netlist including pins absent from original actual-routing manifest. Extra pin ignored/global classification not independently proved. Original driver expected 115572 and failed after native normal snapshot exit; this verifier admits explicit subset instead. No performance or final route evidence.')
(O/'snapshot_verification.json').write_text(json.dumps(result,indent=2)+'\n');print('SNAPSHOT SUBSET PASS',count,len(first),'changed',len(changed))
