"""Adversarial split and feature-provenance contract; no third-party code execution."""
import copy,json
from pathlib import Path
from forecast_split_provenance_v1 import check
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1]
def main():
 base={'samples':[{'sample_id':'a','family_id':'family_A','source_sha256':'a'*64,'lineage_reviewed':True,'split':'train'},{'sample_id':'b','family_id':'family_B','source_sha256':'b'*64,'lineage_reviewed':True,'split':'validation'},{'sample_id':'c','family_id':'family_C','source_sha256':'c'*64,'lineage_reviewed':True,'split':'test'}],'model_fit_samples':['a'],'feature_normalizer_fit_samples':['a'],'label_transform_fit_samples':['a'],'feature_dependencies':[{'sample_id':'c','role':'prior_route','epoch_relation':'strictly_before_target'}],'input_policy':'placement_and_prior_route','claim_strict_unseen_family':True}
 assert check(base)['strict_family_independence_certified'] is False
 cases=[]
 for field in ['model_fit_samples','feature_normalizer_fit_samples','label_transform_fit_samples']:
  for sample in ['b','c','missing']:
   m=copy.deepcopy(base);m[field]=[sample];cases.append(m)
 for role in ['target_route','target_label','prefix_state']:
  m=copy.deepcopy(base);m['feature_dependencies'][0]['role']=role;cases.append(m)
 for field,value in [('family_id','family_A'),('source_sha256','a'*64),('lineage_reviewed',False)]:
  m=copy.deepcopy(base);m['samples'][2][field]=value;cases.append(m)
 m=copy.deepcopy(base);m['feature_dependencies'][0]['epoch_relation']='target';cases.append(m)
 m=copy.deepcopy(base);m['samples'].append(copy.deepcopy(m['samples'][0]));cases.append(m)
 m=copy.deepcopy(base);m['input_policy']='prefix_assisted';m['feature_dependencies']=[{'sample_id':'c','role':'prefix_state','prefix_cost_accounted':False}];cases.append(m)
 for m in cases:
  try:check(m)
  except ValueError:pass
  else:raise AssertionError('contaminated declaration accepted')
 development=copy.deepcopy(base)
 for r in development['samples']:r['family_id']='exposed_development_family';r['lineage_reviewed']=False
 development['claim_strict_unseen_family']=False;result=check(development);assert result['shared_families']==['exposed_development_family'] and not result['strict_claim_consistent_with_declarations']
 prefix=copy.deepcopy(base);prefix['input_policy']='prefix_assisted';prefix['feature_dependencies']=[{'sample_id':'c','role':'prefix_state','prefix_cost_accounted':True}];assert check(prefix)['status']=='DECLARED_PROVENANCE_PREFLIGHT_PASS'
 D=R/'experiments/forecast_split_provenance_contract_v1_2026-10-20';D.mkdir(exist_ok=False);files=[Path(__file__),R/'tools/forecast_split_provenance_v1.py'];(D/'verification.json').write_text(json.dumps({'status':'ALL18_CONTAMINATED_DECLARATIONS_REJECTED_AND3_VALID_SCOPES_PASS','rejections':len(cases),'valid_scopes':3,'bindings':{str(p):sha(p) for p in files},'scope':'Declared metadata checks only. No family independence inferred automatically and no external model executed.'},indent=2)+'\n');assert len(cases)==18;print('FORECAST_PROVENANCE_CONTRACT_PASS',len(cases))
if __name__=='__main__':main()
