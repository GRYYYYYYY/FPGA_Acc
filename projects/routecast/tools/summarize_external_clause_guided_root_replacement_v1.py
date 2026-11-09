"""Archive premise-safe cut-guided replacement and tested demand-bound diagnosis."""
import json,hashlib,os
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_clause_guided_root_replacement_v1_2026-10-19';Q=E/'prospective_external_family_budget_cut_demand_collision_v1_2026-10-19'
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
 pending=[D/n for n in ('protocol.json','verification.json','independent_verification_v1.json')]+[Q/n for n in ('protocol.json','verification.json','independent_verification_v1.json')]+[E/'conditional_budget_cut_admission_contract_v1_2026-10-19/verification.json'];seen=set();bindings={str(Path(__file__).resolve()):sha(Path(__file__))}
 while pending:
  p=pending.pop()
  if p in seen:continue
  seen.add(p);receipt=read(p);bindings[str(p)]=sha(p)
  if not isinstance(receipt,dict):continue
  for q,h in receipt.get('bindings',{}).items():
   assert sha(q)==h,(str(p),q);bindings[q]=h
   if Path(q).suffix=='.json':pending.append(Path(q))
 contract=read(E/'conditional_budget_cut_admission_contract_v1_2026-10-19/verification.json');audits=read(D/'independent_verification_v1.json')['rows'];demands=read(Q/'independent_verification_v1.json');assert contract['rejections']==28 and contract['ownership_truth_cases']==15;assert len(audits)==3 and all(r['pair_installed_privately'] and r['all_other_old_NET_trees_unchanged'] and r['all_admitted_clauses_hold_in_final_private_state'] and not r['conditional_package_complete'] and not r['committed'] for r in audits);assert [r['changed_root_connection_paths'] for r in audits]==[1,1,1];assert [r['final_selected_NETs'] for r in audits]==[36,45,37];assert demands['positive_paths_verified']==20 and demands['negative_certificates_verified']==0 and not any(r['fixed_outside_budget_capacity_contradiction'] for r in demands['collisions'])
 generated=sum(sum(1 for _ in (D/r['case']/'generated_trees.jsonl').open()) for r in audits);newpaths=sum(r['new_connection_paths_verified'] for r in audits);assert generated==6 and newpaths==1292
 decision=dict(status='ALL3_ASSUMPTION_ADMITTED_CUT_GUIDED_ROOT_TARGET_PAIRS_VERIFIED_PACKAGES_STILL_REJECTED',updated_utc=datetime.now(timezone.utc).isoformat(),bindings=bindings,admission_contract={k:v for k,v in contract.items() if k!='bindings'},package_audits=audits,tested_cut_demand_capacity=demands['collisions'],tested_cut_escape_paths=demands['rows'],new_complete_NET_tree_generations=generated,new_connection_paths_verified=newpaths,reused_prefix_connection_paths_reverified=sum(r['initial_connection_paths_reverified'] for r in audits),new_root_connection_paths_changed=3,committed_packages=0,new_bank_candidates=0,unavailable_cases_preserved=6,labels_opened=False,budgets_changed=False,promoted=False,quality_and_utility_gates_pass=False,interpretation='Verified cut artifacts admitted only under exact graph/case/CID/NET/endpoints/budget/outside occupancy premises. Each one-shot root proposal changes exactly one of NET2s427 connection paths while every other old complete NET tree remains identical. All three prior failed target NETs566/734/566 install successfully and learned conditional resource clauses hold. Packages nevertheless fail at next NET567/741/567, so no routing or predictor promotion. Additional fixed proof-only demand checks retain every next failed CID and every CID of current cut-owner NETs other than the already certified NET. Twenty physical budget witnesses show all tested new demands can avoid the old entire cut under outside-only masks. Therefore the tested old-cut demand bound yields no capacity contradiction; this is not global package feasibility or absence of other cuts.',timing_scope='Three search calls per case plus reused archived state and separate proof work. No matched end-to-end timing, native utility or quality improvement claimed.',next_step='Preserve proof-premise invalidation and accumulated resource clauses while deriving additional constraints for new failures, or design a joint clause-aware replacement mechanism. Validate changed tree paths, all old budget paths, all admitted clauses and a new termination/progress rule before multi-step execution. Do not infer sufficiency from one satisfied cut, global infeasibility from these failures, or silently repeat the completed one-shot protocol. Original quality/native utility/strict-family/full-runtime/hardware gates stay open or failed.')
 out=D/'research_decision_v1.json';assert not out.exists();out.write_text(json.dumps(decision,indent=2)+'\n');side=Q/'research_decision_v1.json';assert not side.exists();side.write_text(json.dumps(dict(status='TESTED_OLD_CUT_DEMAND_BOUND_HAS_NO_CAPACITY_CONTRADICTION',primary_decision=str(out),primary_decision_sha256=sha(out),positive_escape_paths=20,scope='Tested cut/NET domain only, not full package feasibility.'),indent=2)+'\n');cp=E/'mmc_multiplicative_feedback_trial_v1_2026-10-10/supervision_checkpoint.json';state=read(cp);state['prospective_external_family_clause_guided_root_replacement_v1']=dict(status=decision['status'],decision=str(out),decision_sha256=sha(out),updated_utc=decision['updated_utc'],promoted=False);tmp=cp.with_name(cp.name+'.clause_root.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');os.replace(tmp,cp)
 print(json.dumps(dict(status=decision['status'],verified_binding_files=len(bindings),new_trees=generated,new_paths=newpaths,positive_cut_escape_paths=20,committed_packages=0)),flush=True)
if __name__=='__main__':main()
