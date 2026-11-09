"""Count-neutral proof-family admission and corrupted receipt rejection."""
import json
from pathlib import Path
from conditional_budget_cut_admission_v3 import verified_store
from conditional_budget_cut_admission_v2 import verified_store as old_store
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'conditional_budget_cut_admission_contract_v3_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);new=E/'prospective_external_family_frontier_continuation_budget_cuts_v1_2026-10-19';artifact=new/'learned_conditional_budget_constraints_v1.json';proof=new/'independent_verification_v1.json';clauses=verified_store(artifact,proof);assert len(clauses)==2 and {r['case'] for r in clauses}=={'w160/episode_01','w160/episode_03'};checks=['two_case_generic_family_admitted'];bindings={str(p):sha(p) for p in [Path(__file__).resolve(),R/'tools/conditional_budget_cut_admission_v3.py',R/'tools/conditional_budget_cut_admission_v2.py',R/'tools/conditional_budget_cut_admission_v1.py',artifact,proof]}
 def reject(a,p,name,loader=verified_store):
  try:loader(a,p)
  except ValueError:checks.append(name)
  else:raise AssertionError(name)
 reject(artifact,proof,'old_loader_explicitly_rejects_unknown_new_family',old_store)
 for name in ['reservation_failure_budget_cuts','reservation_frontier_CID_domains']:
  directory=E/f'prospective_external_family_{name}_v1_2026-10-19';a=directory/'learned_conditional_budget_constraints_v1.json';p=directory/'independent_verification_v1.json';assert verified_store(a,p)==old_store(a,p);checks.append('legacy_family_unchanged_'+name)
  for q in [a,p]:bindings[str(q)]=sha(q)
 clone=D/'unbound_clauses.json';clone.write_bytes(artifact.read_bytes());reject(clone,proof,'identical_unbound_artifact_rejected')
 for kind in ['wrong_family','wrong_artifact_hash','wrong_dependency_hash']:
  d=read(proof)
  if kind=='wrong_family':d['status']='UNVERIFIED'
  elif kind=='wrong_artifact_hash':d['bindings'][str(artifact)]='0'*64
  else:
   key=next(p for p in d['bindings'] if p!=str(artifact));d['bindings'][key]='0'*64
  p=D/(kind+'.json');p.write_text(json.dumps(d,indent=2)+'\n');reject(artifact,p,kind+'_rejected');bindings[str(p)]=sha(p)
 bindings[str(clone)]=sha(clone);assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='COUNT_NEUTRAL_PROOF_FAMILY_ADMISSION_AND_BINDING_REJECTIONS_VERIFIED',checks=checks,bindings=bindings,scope='Generic family admits exactly its two proved cases; legacy families unchanged. Underlying exact premise admission/evaluation functions remain shared unchanged v1. No claim of third-case proof or routing success.'),indent=2)+'\n');print('PASS',len(checks),'checks')
if __name__=='__main__':main()
