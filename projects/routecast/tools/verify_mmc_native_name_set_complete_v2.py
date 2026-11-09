"""Authenticate both full rerun audits, exact original bytes and native gates."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
D=R/'experiments/mmc_native_name_set_complete_v2_2026-10-08'
W=R/'experiments/ultraembedded_mmc_continuous_workflow_v4_2026-10-08'
def auth(data):
 for section in ['bindings','files']:
  for p,h in data.get(section,{}).items():assert sha(p)==h,p
r=json.loads((D/'receipt.json').read_text());p=json.loads((D/'protocol.json').read_text());auth(r);auth(p)
assert r['bindings']==p['bindings'] and [x['arm'] for x in r['rows']]==['cold','seed']
bindings={**r['bindings'],str(D/'receipt.json'):sha(D/'receipt.json'),str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__)):sha(Path(__file__))}
for row in r['rows']:
 arm=row['arm'];new=D/arm/'mmc';old=W/arm/'native/mmc'
 assert row['complete_physical_audit_bytes_equal'] and row['seconds']>0
 assert (new/'physical_audit.json').read_bytes()==(old/'physical_audit.json').read_bytes()
 for folder in [old,new]:
  v=json.loads((folder/'verification.json').read_text());auth(v)
  assert v['physical_connections']==115572 and v['overflow_units']==0
  assert v['all_physical_endpoints_original_XML_arcs_and_node_NET_capacity_pass'] and v['original_native_FULL_check_pass']
  for f in ['verification.json','physical_audit.json']:bindings[str(folder/f)]=sha(folder/f)
 assert row['proof_sha256']==sha(new/'verification.json')
assert all(sha(q)==h for q,h in bindings.items())
(D/'independent_verification_v2.json').write_text(json.dumps(dict(bindings=bindings,all_both_arms_full_original_physical_audit_bytes_and_native_gates_pass=True,rows=r['rows'],scope='Fresh complete XML audit of archived routes; native routing itself not rerun. Candidate-only single clocks, no paired audit/workflow speedup or original HDL/hardware proof.'),indent=2)+'\n')
print(json.dumps(r['rows'],indent=2))
