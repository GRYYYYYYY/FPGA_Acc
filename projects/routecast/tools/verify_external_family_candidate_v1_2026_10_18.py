"""Independent leaf Git hashes, hierarchy receipt and closed metadata size gaps."""
import hashlib,json,re,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 source=R/'experiments/prospective_external_family_source_v2_2026-10-18';vp=source/'source_verification.json';v=json.loads(vp.read_text());runtime=R/'experiments/prospective_external_family_runtime_v1_2026-10-18/verification.json';rt=json.loads(runtime.read_text());assert rt['status']=='source_closure_hierarchy_pass_strict_family_pending' and rt['hierarchy_exit_status']==0
 for proof in [v,rt]:
  for p,h in proof['bindings'].items():assert sha(p)==h
 out=R/'experiments/prospective_external_family_admission_review_v1_2026-10-18';out.mkdir(exist_ok=False);tree=json.loads((source/'upstream_tree.json').read_text());entries={e['path']:e for e in tree['tree']};assert tree['sha']==v['pinned_tree_sha1'];commit=json.loads((source/'upstream_commit.json').read_text());assert commit['sha']==v['pinned_commit'] and commit['commit']['tree']['sha']==tree['sha']
 assets={a['relative']:a for a in v['assets']};rtl=sorted(p for p,e in entries.items() if p.startswith('src/rtl/') and e['type']=='blob');assert rtl==sorted(v['RTL_compilation_units']) and len(rtl)==3
 for name,asset in assets.items():
  path=Path(asset['path']);assert sha(path)==asset['sha256'] and path.stat().st_size==entries[name]['size'];actual=subprocess.check_output(['git','hash-object','--',str(path)],text=True).strip();assert actual==entries[name]['sha']==asset['upstream_git_blob_sha1']
 core=(source/'upstream/chacha.core').read_text();rtl_section=core.split('\nrtl:\n',1)[1].split('\ntb:\n',1)[0] if '\nrtl:\n' in core else None
 if rtl_section is None:
  match=re.search(r'(?ms)^  rtl:\n(.*?)(?=^  \w+:|\Z)',core);assert match;rtl_section=match.group(1)
 declared=sorted(re.findall(r'src/rtl/[A-Za-z0-9_.-]+\.v',rtl_section));assert declared==rtl
 log=(runtime.parent/'closure_check.log').read_text();assert 'ERROR:' not in log and all('\\'+name in log for name in ['chacha','chacha_core','chacha_qr'])
 snapshot=json.loads((source/'pre_acquisition_exposure_snapshot.json').read_text());patterns=[x.encode() for x in ['chacha','xchacha','salsa','salsa20','poly1305','blabla']];digests={a['relative']:a['sha256'].encode() for a in v['assets'] if a['relative'] in rtl};closed=[]
 for gap in snapshot['unresolved']:
  assert gap['reason']=='above2MiB_text_scan_bound';path=REPO/gap['path'];expected=snapshot['metadata_sha256'][gap['path']];h=hashlib.sha256();tail=b'';aliases=set();matched=set()
  with path.open('rb') as f:
   for chunk in iter(lambda:f.read(2**20),b''):
    h.update(chunk);data=tail+chunk;lower=data.lower()
    for p in patterns:
     if p in lower:aliases.add(p.decode())
    for name,digest in digests.items():
     if digest in data:matched.add(name)
    tail=data[-128:]
  assert h.hexdigest()==expected==sha(path);closed.append(dict(path=gap['path'],sha256=expected,aliases=sorted(aliases),exact_candidate_RTL_hash_matches=sorted(matched)))
 assert len(closed)==13
 # Do not silently convert a bounded local negative finding into a global claim.
 result=dict(status='candidate_source_and_closure_verified_family_history_pending',pinned_commit=v['pinned_commit'],pinned_tree_sha1=v['pinned_tree_sha1'],upstream_repository=v['repository'],compilation_units=rtl,all8_selected_upstream_assets_git_hash_equal=len(assets)==8,all3_declared_RTL_units_equal_complete_upstream_RTL_subtree=True,read_only_hierarchy_pass=True,prior_metadata_files=len(snapshot['metadata_sha256']),prior_filename_count=snapshot['filename_count'],prior_filename_alias_hits=snapshot['filename_alias_hits'],prior_metadata_alias_hits=snapshot['metadata_alias_hits'],small_metadata_exact_RTL_hash_matches=v['prior_exact_RTL_hash_references'],closed_metadata_size_gaps=closed,remaining_bound_size_gaps=0,scope_gaps=['Other metadata naming patterns, compressed/unindexed archives and root/outside-workspace history are not covered.','Renamed or modified lineage can escape exact hashes/names; conservative aliases are not a full ancestry certificate.','External user/collaborator exposure clarification remains pending.','No synthesis-to-architecture compatibility, fresh family native labels or predictive validation exists yet.'],strict_unseen_families_certified=0,new_native_labels_read=False,new_placement_route_jobs=False,source_qualification='PROSPECTIVE_CANDIDATE_PENDING_LINEAGE_AND_EXPOSURE',bindings={str(p):sha(p) for p in [Path(__file__),vp,runtime,source/'upstream_commit.json',source/'upstream_tree.json',source/'upstream/chacha.core',source/'pre_acquisition_exposure_snapshot.json',runtime.parent/'closure_check.log']})
 for asset in assets.values():result['bindings'][asset['path']]=asset['sha256']
 with (out/'verification.json').open('x') as f:json.dump(result,f,indent=2)
 print('INDEPENDENT CANDIDATE SOURCE CHECK PASS; size gaps closed',len(closed),'strict unseen remains',0,flush=True)
if __name__=='__main__':main()
