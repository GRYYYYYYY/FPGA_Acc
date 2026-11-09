"""Actual audited archive roundtrip, including low-level failures."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from branch_state_delta_v1 import pack,unpack
from pre_route_endpoints import sha
from source_binding_v2 import closure
parent=R/'experiments/mcnc_prefix_wire04_v11_2026-10-07';out=R/'experiments/branch_delta_roundtrip_v1_2026-10-07';out.mkdir();proof=json.loads((parent/'branch_verification.json').read_text());bindings={**proof['bindings'],**closure([Path(__file__)]),str(parent/'branch_verification.json'):sha(parent/'branch_verification.json')};assert all(sha(k)==v for k,v in bindings.items());(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Offline all saved group states lossless archive roundtrip; no live routing timing or storage savings performance claim.'))+'\n');rows=[]
for name in ('bigkey','dsip','misex3'):
 directory=out/name;directory.mkdir();seeds={};count=original=encoded=0
 for file in sorted((parent/name).glob('repair*/net*.json')):
  batch=int(file.parent.name.split('_')[1][5:]);event=json.loads((parent/name/f'batch{batch}.json').read_text());release=set(event['released_net_ids'])
  if batch not in seeds:
   records=[r for r in event['before_records'] if r['net_id'] not in release]
   # Store full seed records with empty baseline ledger: ledger remains explicit updates.
   seed=dict(records=records,ledger={});seeds[batch]=seed;(directory/f'seed{batch}.json').write_text(json.dumps(seed)+'\n');encoded+=(directory/f'seed{batch}.json').stat().st_size
  seed=seeds[batch];state=json.loads(file.read_text());delta=pack(seed,state);target=directory/(file.parent.name+'_'+file.name);target.write_text(json.dumps(delta)+'\n');assert unpack(json.loads((directory/f'seed{batch}.json').read_text()),json.loads(target.read_text()))==state;count+=1;original+=file.stat().st_size;encoded+=target.stat().st_size
 rows.append(dict(name=name,states=count,original_group_bytes=original,delta_plus_seed_bytes=encoded));print('PASS delta',rows[-1],flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Exact roundtrip of every archived group JSON; original full evidence retained, no live performance/quality proof.'),indent=2)+'\n')
