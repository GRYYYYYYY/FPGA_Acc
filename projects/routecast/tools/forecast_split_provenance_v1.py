"""Declared-provenance preflight; does not discover hidden reads or certify lineage."""
import re
HEX=re.compile(r'[0-9a-f]{64}')
def check(manifest):
 samples=manifest['samples'];ids=[r['sample_id'] for r in samples]
 if not samples or len(ids)!=len(set(ids)):raise ValueError('empty or duplicate samples')
 rows={r['sample_id']:r for r in samples};splits={'train','validation','test'}
 for r in samples:
  if not isinstance(r['family_id'],str) or not r['family_id'] or not HEX.fullmatch(r['source_sha256']) or r['split'] not in splits or type(r['lineage_reviewed']) is not bool:raise ValueError('invalid identity declaration')
 if not any(r['split']=='train' for r in samples) or not any(r['split']=='test' for r in samples):raise ValueError('train and test required')
 for role in ['model_fit_samples','feature_normalizer_fit_samples','label_transform_fit_samples']:
  used=manifest[role]
  if len(set(used))!=len(used) or any(s not in rows or rows[s]['split']!='train' for s in used):raise ValueError('nontraining fit dependency: '+role)
 allowed={'netlist','placement','rr_graph','prior_route'}
 if manifest['input_policy']=='prefix_assisted':allowed.add('prefix_state')
 elif manifest['input_policy']!='placement_and_prior_route':raise ValueError('unknown input policy')
 for dependency in manifest['feature_dependencies']:
  sample=dependency['sample_id'];role=dependency['role']
  if sample not in rows or role not in allowed:raise ValueError('invalid or target-derived feature dependency')
  if role=='prior_route' and dependency.get('epoch_relation')!='strictly_before_target':raise ValueError('prior route epoch unproven')
  if role=='prefix_state' and dependency.get('prefix_cost_accounted') is not True:raise ValueError('prefix acquisition cost unaccounted')
 family_groups={};content_groups={}
 for r in samples:
  family_groups.setdefault(r['family_id'],set()).add(r['split']);content_groups.setdefault(r['source_sha256'],set()).add(r['split'])
 shared_families=sorted(k for k,v in family_groups.items() if len(v)>1);shared_contents=sorted(k for k,v in content_groups.items() if len(v)>1)
 if type(manifest['claim_strict_unseen_family']) is not bool:raise ValueError('explicit claim required')
 if manifest['claim_strict_unseen_family']:
  if shared_families or shared_contents or not all(r['lineage_reviewed'] for r in samples):raise ValueError('strict family separation not established')
 return {'status':'DECLARED_PROVENANCE_PREFLIGHT_PASS','samples':len(samples),'shared_families':shared_families,'shared_source_hashes':shared_contents,'strict_claim_consistent_with_declarations':manifest['claim_strict_unseen_family'],'strict_family_independence_certified':False,'scope':'Validates supplied metadata only; actual feature reads, complete family lineage, immutable prospective exposure registry and full experimental gates need separate evidence.'}
