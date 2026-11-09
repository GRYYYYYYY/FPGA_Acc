"""Every-round complete nonignored manifest pin/source/sink identity audit.
Extra pins explicitly reported; ignored-pin semantics and budget comparison remain separate.
"""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];O=R/'experiments/mmc_native_iteration_state_observer_v2_2026-10-10'
v=json.loads((O/'verification.json').read_text());assert v['exit_status']==0 and v['route_bytes_equal_fully_audited_cold'];assert all(sha(p)==h for p,h in v['bindings'].items())
manifest=R/'experiments/native_manifest_scope_preflight_v1_2026-10-10/mmc.queries';assert sha(manifest)==v['bindings'][str(manifest)]
queries={}
for line in manifest.read_text().splitlines():
 f=line.split()
 if f[0]=='Q':
  cid,net,pin,source,sink=map(int,f[1:]);assert (net,pin) not in queries;queries[net,pin]=(source,sink)
assert len(queries)==115572
rows=[]
for iteration in range(1,22):
 p=O/'states'/f'round_{iteration}.tsv';assert sha(p)==v['bindings'][str(p)];roots={};pins={}
 with p.open() as s:
  for line in s:
   f=line.split()
   if f[0]!='T':continue
   assert len(f)==7;net,n,parent,switch=int(f[1]),int(f[2]),int(f[3]),int(f[4]);index=int(f[6])
   if parent==-1:assert net not in roots;roots[net]=n
   if index>=1:assert (net,index) not in pins; pins[net,index]=n
 for (net,index),(source,sink) in queries.items():assert roots[net]==source and pins[net,index]==sink,(iteration,net,index,'manifest mismatch')
 extra=sorted(set(pins)-set(queries));rows.append({'iteration':iteration,'manifest_pins_checked':len(queries),'observed_pin_count':len(pins),'extra_pin_count':len(extra),'extra_pin_examples':[list(x) for x in extra[:12]]})
 print('PIN IDENTITY',iteration,len(queries),len(extra),flush=True)
assert all(sha(p)==h for p,h in v['bindings'].items())
f=O/'pin_identity_audit_v1.json';assert not f.exists();f.write_text(json.dumps({'bindings':{**v['bindings'],str(O/'verification.json'):sha(O/'verification.json'),str(Path(__file__).resolve()):sha(Path(__file__))},'all21rounds_all115572_manifest_NET_local_pin_source_sink_identity_pass':True,'rows':rows,'scope':'Complete nonignored manifest pin identity and root/sink RR mapping only; extra pins reported, not independently classified here. Does not certify path RC/budgets or whole-net semantic equivalence.'},indent=2)+'\n')
