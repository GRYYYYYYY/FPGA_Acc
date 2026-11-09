"""Exact full-sequence JSON comparison to independently audited v11 reference."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
old=R/'experiments/mcnc_prefix_wire04_v11_2026-10-07';out=R/'experiments/mcnc_prefix_edge_v13_2026-10-07';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());op=json.loads((old/'protocol.json').read_text());assert p['policy']==op['policy'] and p['inputs']==op['inputs'] and p['cases']==op['cases'];assert r['protocol_sha256']==sha(out/'protocol.json');bindings={**p['inputs'],**p['sources'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json')}
for proofname in ('verification.json','branch_verification.json'):
 file=old/proofname;proof=json.loads(file.read_text());bindings.update(proof['bindings']);bindings[str(file)]=sha(file)
for row in r['rows']:bindings.update(row['files'])
assert all(sha(k)==v for k,v in bindings.items());(out/'parity_protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Authenticate old deep audits and compare full actual transaction/branch/candidate JSON. Exact parity permits inherited structural evidence only; no fresh native or speed proof.'))+'\n');rows=[]
for row in r['rows']:
 name=row['name'];patterns=('candidate.json','floors.json','batch*.json','repair*/*.json');a={str(f.relative_to(old/name)):f for pattern in patterns for f in (old/name).glob(pattern)};b={str(f.relative_to(out/name)):f for pattern in patterns for f in (out/name).glob(pattern)};missing=sorted(set(a)-set(b));extra=sorted(set(b)-set(a));changed=[];equal=0
 for key in sorted(set(a)&set(b)):
  bindings[str(a[key])]=sha(a[key]);bindings[str(b[key])]=sha(b[key])
  if json.loads(a[key].read_text())==json.loads(b[key].read_text()):equal+=1
  else:changed.append(key)
 rows.append(dict(name=name,json_equal=equal,missing=missing,extra=extra,changed=changed,all_sequence_outputs_equal=not(missing or extra or changed)));print(name,rows[-1],flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'parity_verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Structural proof inherits authenticated reference only for wholly identical cases; differences require fresh audit. Timings not controlled; lower-bound publications independently audited separately.'),indent=2)+'\n')
