"""Require full audit and dependency closure before interpreting label diagnostics."""
import json
from pathlib import Path
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_exact_aggregate_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 proof=D/'independent_verification_v1.json';v=read(proof);assert len(v['rows'])==72 and v['metric_vectors']==216
 docs=[proof,D/'verification.json',D/'manifest.json',E/'wbuart_reduced_L1_factor_profile_v1_2026-10-20/independent_verification_v1.json',E/'wbuart_joint_aggregate_L1_v1_2026-10-20/independent_verification_v1.json']
 docs += [D/c/'verification.json' for c in read(D/'manifest.json')['cases']]
 bindings={}
 for p in docs:
  doc=read(p)
  for name,h in doc['bindings'].items():assert sha(name)==h,name;bindings[name]=h
  bindings[str(p)]=sha(p)
 rows=read(D/'verification.json')['rows'];local=read(E/'wbuart_joint_aggregate_L1_v1_2026-10-20/verification.json')['rows'];comparisons=[]
 for row in rows:
  previous=next(x for x in local if all(x[k]==row[k] for k in ['case','initializer','timing_policy','priority']));changes={}
  for scope in ['resource','spatial']:
   a=row['metrics']['exact_label_diagnostic'][scope];b=previous['metrics']['joint_label_diagnostic'][scope];changes[scope]={'rho_delta':a['rho']-b['rho'],'hits_delta':a['hits']-b['hits']}
  comparisons.append({**{k:row[k] for k in ['case','initializer','timing_policy','priority','minimum_L1','local_L1','both_numeric_comparisons']},'relative_to_oneNET_local':changes})
 primary=[r for r in comparisons if (r['initializer'],r['timing_policy'],r['priority'])==('native_retained','warm_timing_round_updated','MAP')];assert len(primary)==9
 report={'status':'CERTIFIED_FINITE_POOL_LOSS_DIAGNOSTIC_REVIEW','rows':comparisons,'primary':primary,'all_config_numeric_comparisons_pass':sum(r['both_numeric_comparisons'] for r in comparisons),'primary_numeric_comparisons_pass':sum(r['both_numeric_comparisons'] for r in primary),'strict_L1_improvements':sum(r['minimum_L1']<r['local_L1'] for r in comparisons),'interpretation':['Exact optimum is for aggregate CHANNEL-count L1, then minimum switches; not Spearman or topK optimum.','Lower L1 can lower spatial rho or resource topK hits; more L1 search alone cannot guarantee original ranking gate.','Failure of the canonical L1 minimizer is not proof that no other pool selection passes the ranking gate.','All target-dependent diagnostics remain inadmissible as deployable predictors; original actual quality gate remains 0/9.','Next model research must use source/input-only signals and frozen original gates; do not tune on successful diagnostic cases.'],'bindings':{**bindings,str(Path(__file__)):sha(__file__)}}
 out=D/'research_review_v1.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n');print('CERTIFIED_EXACT_REVIEW',report['primary_numeric_comparisons_pass'],report['all_config_numeric_comparisons_pass'])
if __name__=='__main__':main()
