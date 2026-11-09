"""Independently reconstruct all archived delta states and bind actual files."""
import json,sys,copy,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
out=R/'experiments/branch_delta_roundtrip_v1_2026-10-07';parent=R/'experiments/mcnc_prefix_wire04_v11_2026-10-07';receipt=json.loads((out/'receipt.json').read_text());bindings={**receipt['bindings'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json')};files=[f for n in ('bigkey','dsip','misex3') for f in (out/n).glob('*.json')];bindings.update({str(f):sha(f) for f in files});assert all(sha(k)==v for k,v in bindings.items());(out/'verification_protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Independent delta decoder against authenticated original full branch states. All seed/delta files SHA bound, physical checks inherited from identical original states.'))+'\n')
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
rows=[]
for row in receipt['rows']:
 name=row['name'];count=0
 for file in sorted((out/name).glob('repair*.json')):
  dirname,filename=file.name.rsplit('_',1);batch=int(dirname.split('_')[1][5:]);seed=json.loads((out/name/f'seed{batch}.json').read_text());delta=json.loads(file.read_text());assert delta['version']==1 and digest(seed)==delta['seed_sha256'];records={r['connection_id']:r for r in seed['records']};assert len(records)==len(seed['records'])
  for r in delta['new_records']:assert r['connection_id'] not in records;records[r['connection_id']]=r
  order=delta['record_order'];assert len(order)==len(set(order)) and set(order)==set(records);ledger=dict(seed['ledger'])
  for n in delta['ledger_removed']:assert n in ledger;del ledger[n]
  ledger.update(delta['ledger_updates']);state=copy.deepcopy(delta['metadata']);assert 'records' not in state and 'ledger' not in state;state.update(records=[records[cid] for cid in order],ledger=ledger);assert digest(state)==delta['state_sha256'];original=parent/name/dirname/filename;assert str(original) in bindings and json.loads(original.read_text())==state;count+=1
 assert count==row['states'];rows.append(dict(name=name,all_seed_delta_hashes_bound=True,independent_exact_reconstructions=count));print('PASS independent archive',name,count,flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Full JSON equality inherits authenticated old XML/RC/parent/capacity/constraint checks, not new physical solver, live timing or native gain.'),indent=2)+'\n')
