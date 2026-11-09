"""Refresh local declared-source exposure, without opening new route labels."""
import json,sys,subprocess,datetime
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from archive_design_exposure_v3 import declarations
from source_binding_v2 import closure

def main():
 oldpath=R/'experiments/design_exposure_inventory_v3_2026-10-15/receipt.json';old=json.loads(oldpath.read_text())
 familypath=R/'experiments/cross_project_koios_source_declarations_v1_2026-10-15/family_admission_status_v1.json';families=json.loads(familypath.read_text())
 catalogpath=R/'experiments/koios_pinned_source_inventory_v4_2026-10-15/verification.json';catalog=json.loads(catalogpath.read_text())
 bindings={str(p):sha(p) for p in [oldpath,familypath,catalogpath]};bindings.update(closure([Path(__file__),R/'tools/archive_design_exposure_v3.py']))
 indexed=defaultdict(list)
 for record in old['declared_source_records']:indexed[record['protocol']].append(record)
 paths=sorted(subprocess.run(['rg','--files','--hidden','-g','protocol.json','experiments'],cwd=R,text=True,capture_output=True,check=True).stdout.splitlines())
 hashes={};records=[];unresolved=[];counts=Counter();changed=[];added=[]
 for name in paths:
  path=R/name;before=path.stat();digest=sha(path);hashes[name]=digest
  if digest==old['stable_protocol_hashes'].get(name):
   records.extend(indexed[name]);counts['unchanged_protocols']+=1
   if not indexed[name]:unresolved.append(dict(protocol=name,reason='prior_no_direct_source_declaration_or_prior_decode_bound'))
   continue
  if name in old['stable_protocol_hashes']:changed.append(name)
  else:added.append(name)
  if before.st_size>2**21:
   unresolved.append(dict(protocol=name,reason='above2MiB_decode_bound',bytes=before.st_size));continue
  try:
   data=json.loads(path.read_text());rows=list(declarations(data))
  except (ValueError,UnicodeError,RecursionError) as error:
   unresolved.append(dict(protocol=name,reason=type(error).__name__));continue
  if sha(path)!=digest:
   unresolved.append(dict(protocol=name,reason='changed_during_read'));continue
  if not rows:unresolved.append(dict(protocol=name,reason='no_direct_source_identity'))
  for row in rows:
   row.update(protocol=name,protocol_sha256=digest,identity_hash_valid=isinstance(row['declared_sha256'],str) and len(row['declared_sha256'])==64,filename_stem=Path(row['path']).stem)
   records.append(row)
  counts['new_or_changed_decoded_protocols']+=1
 removed=sorted(set(old['stable_protocol_hashes'])-set(paths))
 members=catalog['all_benchmark_members'];official={r['relative_to_official_VTR']:r['sha256'] for r in catalog['authenticated_files']}
 references=defaultdict(set)
 for row in records:
  for member in members:
   source=member['source'];digest=official.get(source)
   if row['path']==source or row['path'].endswith('/'+source) or digest and row['declared_sha256']==digest:
    references[member['provisional_group']].add(row['protocol'])
 prior_dev=set(families['development_only_conservative_groups']);unknown=set(families['remaining_unknown_groups'])
 additionally_referenced=unknown&set(references)
 result_groups={g:dict(prior_status='DEVELOPMENT_REFERENCE' if g in prior_dev else 'UNKNOWN',current_local_declared_reference_count=len(references[g]),new_or_changed_protocol_references=sorted(references[g]&(set(added)|set(changed))),strict_unseen_admitted=False,status='DEVELOPMENT_REFERENCE' if g in prior_dev or references[g] else 'UNKNOWN') for g in catalog['provisional_groups']}
 drift=[name for name,h in hashes.items() if not (R/name).exists() or sha(R/name)!=h]
 out=R/'experiments/routecast_exposure_delta_v1_2026-10-18';out.mkdir()
 result=dict(status='complete' if not drift else 'protocol_snapshot_changed',bindings=bindings,checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),current_protocol_count=len(paths),prior_protocol_count=old['protocol_count'],counts=dict(counts),new_protocols=added,changed_prior_protocols=changed,missing_prior_protocols=removed,unstable_protocols=drift,current_protocol_hashes=hashes,declared_source_records=records,unresolved_protocols=unresolved,koios_group_status=result_groups,prior_unknown_groups_now_with_local_declarations=sorted(additionally_referenced),strict_unseen_families_certified=0,new_native_labels_read=False,scope='RouteCast protocol metadata declarations only, bounded2MiB JSON decode. Reuses old declared identities only if current protocol bytes match. Not successful model/label exposure, full ancestry, cross-project refresh or global history proof. Prior unknown groups never upgraded to unseen; absent declarations remain UNKNOWN. No source/label/job files modified.')
 with (out/'receipt.json').open('x') as stream:json.dump(result,stream,indent=2)
 print(json.dumps(dict(status=result['status'],protocols=len(paths),added=len(added),changed=len(changed),missing=len(removed),declared_sources=len(records),unresolved=len(unresolved),group_status_counts=dict(Counter(x['status'] for x in result_groups.values())),strict_unseen_families=0)),flush=True)

if __name__=='__main__':main()
