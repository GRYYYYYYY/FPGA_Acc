"""Account for two observed scan exceptions without changing archived evidence."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
O=R/'work/reproducibility_dependency_closure_20261021'
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 audit=O/'audit.json';before=digest(audit);data=json.loads(audit.read_text());assert len(data['errors'])==2
 errors={Path(e['path']).relative_to(R).as_posix():e for e in data['errors']}
 plan=errors['experiments/research_plan.json'];readme=errors['README.md']
 archived=R/'work/current_research_claim_matrix_v2_20261017/inputs/experiments/research_plan.json'
 assert digest(archived)==plan['expected']
 old=Path(plan['source']);old_before=digest(old);old_data=json.loads(old.read_text())
 assert old_data['archived_inputs_sha256'][str(archived.relative_to(R))]==plan['expected']
 payload=Path(readme['source']);payload_before=digest(payload);pd=json.loads(payload.read_text());root=payload.parent
 assert pd['files_sha256']['README.md']==readme['expected'];assert digest(root/'README.md')==readme['expected']
 reproducer=root/'reproduce.py';s=reproducer.read_text();assert 'path = ROOT / relative' in s
 checked={}
 for relative,expected in pd['files_sha256'].items():
  path=root/relative;actual=digest(path);assert actual==expected,relative;checked[relative]=actual
 assert len(data['unresolved_hash_field_forms'])==1
 ambiguity=data['unresolved_hash_field_forms'][0];assert ambiguity['source']==str(payload) and ambiguity['key']=='README.md'
 assert not data['json_parse_errors']
 assert digest(audit)==before and digest(old)==old_before and digest(payload)==payload_before
 report={'status':'original_two_exceptions_retained_and_explained_by_archived_plan_and_package_relative_paths','original_scan_unique_files':data['unique_files'],'original_scan_bytes_hashed':data['bytes_hashed'],'original_reference_edges':data['reference_edges'],'original_exceptions_retained':2,'unexplained_recorded_exceptions':0,'resolutions':[{'path':plan['path'],'classification':'mutable_root_plan_historical_digest_has_hash_bound_archive','historical_source':str(old),'archive':str(archived),'verified_sha256':plan['expected'],'original_mutable_reference_not_rewritten':True},{'path':readme['path'],'classification':'scanner_wrong_base_for_package_relative_file_map','manifest':str(payload),'correct_file':str(root/'README.md'),'verified_sha256':readme['expected'],'package_manifest_members_reverified':len(checked),'relative_base_evidence':str(reproducer),'original_scan_path_ambiguity_retained':True}],'source_sha256':{str(p):digest(p) for p in [audit,O/'exception_classification.json',old,archived,payload,reproducer,root/'README.md',Path(__file__).resolve() ]},'scope':'Only recorded hash dependencies and these two scoped exceptions. Original scan and historical manifests unchanged. No source repair, portable complete-pipeline rebuild, new routing verification, physical evidence or G8 closure. Unhashed and unrecognized dependencies remain outside scan coverage.','research_complete':False}
 with (O/'exception_resolution.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','resolutions']}))
if __name__=='__main__':main()
