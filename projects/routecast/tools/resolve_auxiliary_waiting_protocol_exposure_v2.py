"""Resolve the exact unmatched explicit protocol digest via authenticated writer naming."""
import json,hashlib
from pathlib import Path
from resolve_protocol_digest_exposure_v2 import protocol_digests
from resolve_protocol_source_exposure_v1 import references, witnesses as derive_witnesses
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 inventory=R/'experiments/design_exposure_inventory_v3_2026-10-15/receipt.json';previous=R/'experiments/protocol_digest_exposure_resolution_v2_2026-10-17/verification.json'
 inv=json.loads(inventory.read_text());old=json.loads(previous.read_text());assert old['all_pass'] and old['unmatched_explicit_protocol_digest_fields']==1
 frozen=inv['stable_protocol_hashes'];byhash={}
 for name,digest in frozen.items():byhash.setdefault(digest,[]).append(name)
 missing=[]
 for name,expected in frozen.items():
  p=R/name;assert sha(p)==expected
  for digest in protocol_digests(json.loads(p.read_text())):
   if digest not in byhash:missing.append((name,digest))
 assert len(missing)==1
 name,digest=missing[0];origin=R/name;data=json.loads(origin.read_text())
 writer=R/'tools/stereo_global_bypass_impact.py';assert sha(writer)==data['sources']['stereo_global_bypass_impact.py']
 source=writer.read_text();assert "sha(out/'waiting_protocol.json')" in source and "'waiting_protocol_sha256'" in source
 target=origin.parent/'waiting_protocol.json';assert sha(target)==digest==data['waiting_protocol_sha256']
 waiting=json.loads(target.read_text());parents=byhash.get(waiting['parent_protocol_sha256'],[]);assert parents
 assert all(sha(R/p)==waiting['parent_protocol_sha256'] for p in parents)
 # Preserve explicit witnesses only: source links to auxiliary waiting, then to exact snapshot parent.
 parent_witnesses={p:old['witness_by_protocol'][p] for p in parents if p in old['witness_by_protocol']}
 assert parent_witnesses
 witnesses=[]
 for parent,w in parent_witnesses.items():
  record=inv['declared_source_records'][w['declaration_record_index']];assert record['identity_hash_valid']
  witnesses.append(dict(parent_protocol=parent,parent_source_declaration_witness=w,source_declaration_record=record))
 auxiliary_name=str(target.relative_to(R))
 byhash.setdefault(digest,[]).append(auxiliary_name)
 names={**frozen,auxiliary_name:digest};absolute={str(R/n):n for n in names};edges={n:set() for n in names}
 for n,h in names.items():
  obj=json.loads((R/n).read_text());assert sha(R/n)==h
  for path,reference_digest in references(obj):
   dest=absolute.get(path)
   if dest is not None and names[dest]==reference_digest:edges[n].add(dest)
  for reference_digest in protocol_digests(obj):edges[n].update(byhash.get(reference_digest,[]))
 direct={}
 for i,row in enumerate(inv['declared_source_records']):
  if row['identity_hash_valid'] and row['protocol'] in frozen:direct.setdefault(row['protocol'],i)
 found=derive_witnesses(edges,direct);assert set(old['witness_by_protocol'])<=set(found)
 newly=sorted((set(found)&set(frozen))-set(old['witness_by_protocol']))
 assert name in found and auxiliary_name in found and name in newly
 for n,w in found.items():
  if w['distance']:
   nxt=w['next_protocol'];assert nxt in edges[n] and found[nxt]['distance']==w['distance']-1 and found[nxt]['declaration_record_index']==w['declaration_record_index']
 files=[Path(__file__).resolve(),inventory,previous,origin,target,writer,*[R/p for p in parents]]
 out=R/'experiments/auxiliary_waiting_protocol_exposure_resolution_v2_2026-10-17';out.mkdir()
 result=dict(all_pass=True,original_snapshot_protocols=3693,previous_unmatched_explicit_digest_fields=1,remaining_unmatched_explicit_digest_fields=0,new_authenticated_auxiliary_protocols=1,previous_original_snapshot_unresolved_count=len(old['remaining_unresolved_protocols']),original_snapshot_unresolved_count=len(set(frozen)-set(found)),original_snapshot_source_reachability_changed=bool(newly),newly_source_linked_original_protocols=newly,total_reached_original_snapshot_protocols=len(set(frozen)&set(found)),auxiliary_protocol_source_witness=found[auxiliary_name],witness_by_protocol=found,origin_protocol=name,origin_already_had_source_witness=name in old['witness_by_protocol'],explicit_auxiliary_protocol=str(target.relative_to(R)),explicit_auxiliary_digest=digest,witnesses=witnesses,bindings={str(p):sha(p) for p in files},strict_unseen_families_certified=0,new_route_labels_opened=False,new_frontend_or_model_launched=False,scope='One exact historical declaration reference now resolved via authenticated writer and file hash. Auxiliary file lay outside protocol.json-only frozen inventory. No complete history, actual experiment/label exposure or strict-unseen certification inferred.',promoted=False)
 (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['witnesses','bindings','witness_by_protocol']},indent=2))
if __name__=='__main__':main()
