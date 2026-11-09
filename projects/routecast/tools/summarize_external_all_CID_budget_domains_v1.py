"""Archive all-CID exact terminal proofs, accumulated owner models and preflight gaps."""
import json,hashlib,os
from pathlib import Path
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[1];E=R/'experiments';T=E/'prospective_external_family_all_CID_terminal_budget_domains_v1_2026-10-19';S=E/'prospective_external_family_all_CID_accumulated_ownership_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
cache={}
def sha(p):
 p=Path(p)
 if p not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
  cache[p]=h.hexdigest()
 return cache[p]
def main():
 pending=[T/n for n in ('protocol.json','verification.json','independent_verification_v1.json','learned_conditional_budget_constraints_v1.json')]+[S/n for n in ('protocol.json','verification.json','physical_proposal_preflight_v1.json')]+[E/'conditional_budget_cut_admission_contract_v2_2026-10-19/verification.json',E/'irredundant_cut_owner_witness_contract_v1_2026-10-19/verification.json',E/'cut_owner_actor_requirements_contract_v1_2026-10-19/verification.json'];seen=set();bindings={str(p):sha(p) for p in (Path(__file__).resolve(),T/'proof_scope_v1.md')}
 while pending:
  p=pending.pop()
  if p in seen:continue
  seen.add(p);r=read(p);bindings[str(p)]=sha(p)
  if not isinstance(r,dict):continue
  for q,h in r.get('bindings',{}).items():
   assert sha(q)==h,(str(p),q);bindings[q]=h
   if Path(q).suffix=='.json':pending.append(Path(q))
 terminal=read(T/'independent_verification_v1.json');solves=read(S/'verification.json')['rows'];preflight=read(S/'physical_proposal_preflight_v1.json')['rows'];admission=read(E/'conditional_budget_cut_admission_contract_v2_2026-10-19/verification.json');cleanup=read(E/'irredundant_cut_owner_witness_contract_v1_2026-10-19/verification.json');actors=read(E/'cut_owner_actor_requirements_contract_v1_2026-10-19/verification.json')
 assert terminal['NETs']==7 and terminal['connections']==22 and terminal['physical_ingress_witnesses_verified']==122 and terminal['forward_potential_edge_inequalities_verified']==4758293;assert all(r['all_original_CIDs_covered'] for r in terminal['rows']);assert [r['cuts'] for r in solves]==[11,6,11] and all(r['status']=='SAT' and r['certificate_or_model_verified'] and not r['route_feasibility_proved'] for r in solves)
 assert admission['valid_contexts']==28 and admission['budget_mismatch_rejections']==28 and admission['same_NET_sibling_CID_rejections']==24 and admission['unbound_artifact_rejections']==3;assert [r['requirements']['required_actor_NETs'] for r in preflight]==[[2,84,566,567],[764],[2,84,566,567]];assert all(not r['ready_for_new_physical_trial'] for r in preflight);assert [r['known_failed_physical_search_would_be_unchanged'] for r in preflight]==[False,True,False]
 reductions=[]
 for row in solves:
  p=S/row['case']/'irredundant_owner_model.json';reduction=read(p)['reduction'];assert len(reduction['active'])==len(row['one_logical_owner_allocation']);reductions.append(dict(case=row['case'],retained_owners=len(reduction['active']),removed_surplus_owners=len(reduction['removed']),each_retained_owner_has_unique_cut_witness=all(w['unique_owner_cut_indices'] for w in reduction['irreducibility_witnesses'])))
 decision=dict(status='ALL_RELEVANT_CID_TERMINAL_DOMAINS_CERTIFIED_ACCUMULATED_MODELS_SAT_ACTOR_GAPS_IDENTIFIED',updated_utc=datetime.now(timezone.utc).isoformat(),bindings=bindings,terminal_domain_results=terminal['rows'],case_NETs=7,all_original_CIDs=22,certified_physical_ingress_paths=122,forward_edge_inequalities_verified=4758293,accumulated_owner_necessary_relaxations=solves,irredundant_owner_reductions=reductions,proposal_preflight=preflight,admission_contract={k:v for k,v in admission.items() if k!='bindings'},owner_reduction_contract={k:v for k,v in cleanup.items() if k!='bindings'},actor_requirements_contract={k:v for k,v in actors.items() if k!='bindings'},new_physical_tree_searches=0,committed_packages=0,new_bank_candidates=0,unavailable_cases=[f'w{w:03d}/episode_{ep:02d}' for w in (96,128) for ep in (1,2,3)],labels_opened=False,budgets_changed=False,promoted=False,quality_and_utility_gates_pass=False,interpretation='All original CID obligations for the seven currently relevant case/NET pairs now contribute exact budget-admissible terminal cuts. One source potential per NET and positive witnesses prove completeness, not just one failure-CID budget check. Old internal cuts plus terminal cuts give11/6/11 necessary ownership clauses and SAT models. Inclusion-minimal owner deletion preserves every cut; it is not minimum-cost or individually mandatory assignment. Actor detection includes existing NETs missing assigned points as well as conflicting current owners. Cases1/3 therefore need actors2/84/566/567, with NET2(427 CIDs) and84(266 CIDs) still missing full-CID domains. Case2 asks only for absent NET764 with no predecessor release, against exactly the already independently failed physical state; repeating that search with extra reservations cannot improve it. No new physical trial is executed on these incomplete/no-change proposals.',next_step='Expand the proof relevance closure to all original CIDs of newly required actors NET2/84 in cases1/3, under unchanged outside assumptions. Derive an internal resource cut for NET764/CID3779 from its actual failed prefix in case2, because free terminal points do not encode upstream channel blockage. Then re-solve all necessary constraints with explicit progress/selection and validate any physical realization; do not treat SAT terminal domains as full NET-tree feasibility or silently repeat failed masks. Original forecast quality/native utility/family/full-runtime/hardware gates remain open or failed.')
 out=S/'research_decision_v1.json';assert not out.exists();out.write_text(json.dumps(decision,indent=2)+'\n');p=T/'research_decision_v1.json';assert not p.exists();p.write_text(json.dumps(dict(status='ALL7_CASE_NET22_CID_TERMINAL_BUDGET_DOMAINS_EXACTLY_CERTIFIED',primary_decision=str(out),primary_decision_sha256=sha(out),promoted=False),indent=2)+'\n');cp=E/'mmc_multiplicative_feedback_trial_v1_2026-10-10/supervision_checkpoint.json';state=read(cp)
 for key in ('prospective_external_family_all_CID_terminal_budget_domains_v1','prospective_external_family_all_CID_accumulated_ownership_v1'):state[key]=dict(status=decision['status'],decision=str(out),decision_sha256=sha(out),updated_utc=decision['updated_utc'],promoted=False)
 tmp=cp.with_name(cp.name+'.all_CID_domains.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');os.replace(tmp,cp);print(json.dumps(dict(status=decision['status'],verified_binding_files=len(bindings),NETs=7,CIDs=22,physical_path_certificates=122,owner_models_SAT=3,new_physical_trials=0)),flush=True)
if __name__=='__main__':main()
