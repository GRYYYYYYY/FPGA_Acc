"""Stage input-only prospective MMC episodes; never read target route outcomes."""
import hashlib,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1]
O=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
 return h.hexdigest()
def read(p): return json.loads(Path(p).read_text())
def write(p,j):
 with p.open('x') as f: json.dump(j,f,indent=2); f.write('\n')
proofs=[R/'experiments'/n/'verification.json' for n in ['prospective_layout_swap_native_pin_identity_v1_2026-10-18','prospective_layout_swap_native_deltas_v1_2026-10-18']]
proofs.append(R/'experiments/mmc_prospective_swap_input_exposure_v1_2026-10-19/exception_review_v1.json')
bindings={str(Path(__file__).resolve()):sha(__file__)}
for p in proofs:
 j=read(p); bindings[str(p)]=sha(p)
 for q,h in j.get('bindings',{}).items():
  assert q not in bindings or bindings[q]==h
  bindings[q]=h
for p,h in bindings.items(): assert sha(p)==h,p
source=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json'
old={r['connection_id']:r for r in read(source)['records']};assert len(old)==115572
bindings[str(source)]=sha(source)
O.mkdir(); rows=[]
for i in range(1,4):
 name=f'episode_{i:02d}'; ep=R/'experiments/prospective_layout_swap_native_partition_v1_2026-10-18'/name/'endpoints.json'
 j=read(ep);qs=j['connections'];by={q['connection_id']:q for q in qs};assert len(qs)==len(by)==115572 and set(by)==set(old)
 assert all(q['net_id']==old[c]['net_id'] for c,q in by.items())
 changed=sorted(c for c,q in by.items() if (q['source'],q['sink'])!=(old[c]['source'],old[c]['sink']))
 dirty=sorted({by[c]['net_id'] for c in changed});assert changed
 delta=read(R/'experiments/prospective_layout_swap_native_deltas_v1_2026-10-18/verification.json')['episodes'][i-1]
 assert len(changed)==delta['affected_connections'] and len(dirty)==delta['affected_NETs']
 d=O/name;d.mkdir();(d/'demand').mkdir();(d/'mmc').mkdir()
 shutil.copyfile(ep,d/'demand/endpoints.json')
 native=R/'experiments/prospective_layout_swap_native_placement_v1_2026-10-18'/name
 local={str(ep):sha(ep)}
 for f in ['design.net','design.place','design.blif']:
  p=native/f;shutil.copyfile(p,d/'mmc'/f);local[str(p)]=sha(p);assert sha(d/'mmc'/f)==local[str(p)]
 assert sha(d/'mmc/design.net')==j['inputs']['net']['sha256']
 affected=dict(changed_connection_ids=changed,affected_net_ids=dirty,recompute_connection_ids=sorted(c for c,q in by.items() if q["net_id"] in set(dirty)))
 staged=dict(bindings=local,affected=affected,connections=len(qs),all_native_logical_NET_local_pin_identities_preserved=True,native_route_labels_generated=False,scope='Adapter only; pin identity certified by bound native proof. Known MMC family; no global unseen history claim. No target route read or job launched.')
 write(d/'staged_input_verification_v1.json',staged)
 rows.append(dict(episode=name,changed_connections=len(changed),dirty_NETs=len(dirty),staged_path=str(d)))
 bindings.update(local)
for p in O.rglob('*'):
 if p.is_file():bindings[str(p)]=sha(p)
write(O/'verification.json',dict(status='three_predictor_input_adapters_verified',bindings=bindings,episodes=rows,native_route_jobs_launched=0,strict_unseen_family_admitted=False,predictor_outputs_pending=True,prospective_outcome_protocol_pending=True))
print(json.dumps(rows,indent=2))
