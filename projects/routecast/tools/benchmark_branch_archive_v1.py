"""Alternating real-state serializer/write comparison; all overhead per call paid."""
import sys,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from branch_state_delta_v1 import pack,unpack
from pre_route_endpoints import sha
from source_binding_v2 import closure
parent=R/'experiments/mcnc_prefix_wire04_v11_2026-10-07';out=R/'experiments/branch_archive_cost_v1_2026-10-07';out.mkdir();files=sorted((parent/'bigkey').glob('repair_batch2_attempt1_branch*/net*.json'));assert len(files)==27;eventfile=parent/'bigkey/batch2.json';bindings={str(f):sha(f) for f in files+[eventfile]};bindings.update(closure([Path(__file__)]));(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,files=len(files),order=['full','delta','delta','full','delta','full','full','delta'],policy='All bigkey failed transaction2 group states retained. Input parsing separate; each mode pays serialization/write/close; delta pays pack hashes/copy and seed publication per round. No fsync, original observer same close-only policy. Reconstruction and hash audit outside timer; warmed single-host component, no routing/GPFS durability/end-to-end/statistical claims.'))+'\n');begin=time.perf_counter();event=json.loads(eventfile.read_text());release=set(event['released_net_ids']);seed=dict(records=[r for r in event['before_records'] if r['net_id'] not in release],ledger={});states=[json.loads(f.read_text()) for f in files];preparation=time.perf_counter()-begin;rows=[]
for i,mode in enumerate(['full','delta','delta','full','delta','full','full','delta']):
 directory=out/f'round{i}_{mode}';directory.mkdir();start=time.perf_counter();size=0
 if mode=='delta':
  text=json.dumps(seed)+'\n';(directory/'seed.json').write_text(text);size+=len(text.encode())
 for j,state in enumerate(states):
  value=state if mode=='full' else pack(seed,state);text=json.dumps(value)+'\n';(directory/f'state{j}.json').write_text(text);size+=len(text.encode())
 elapsed=time.perf_counter()-start
 for j,state in enumerate(states):
  value=json.loads((directory/f'state{j}.json').read_text());decoded=value if mode=='full' else unpack(json.loads((directory/'seed.json').read_text()),value);assert decoded==state
 rows.append(dict(round=i,mode=mode,seconds=elapsed,bytes=size,states=len(states),all_roundtrips_exact=True));print(rows[-1],flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,input_prepare_seconds=preparation,rows=rows,files={str(p):sha(p) for p in out.glob('round*/*.json')},scope='Alternating component serialization/write, not routing or physical hardware performance.'),indent=2)+'\n')
