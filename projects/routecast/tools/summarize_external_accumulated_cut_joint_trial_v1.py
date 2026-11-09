"""Archive extra graph cuts, necessary ownership solves, and one physical trial."""
import json,hashlib,os
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';C=E/'prospective_external_family_additional_budget_resource_cuts_v1_2026-10-19';S=E/'prospective_external_family_accumulated_budget_cut_ownership_v1_2026-10-19';D=E/'prospective_external_family_joint_cut_owner_replacement_v1_2026-10-19'
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
 pending=[C/'independent_verification_v1.json',C/'verification.json',S/'verification.json',S/'protocol.json',D/'protocol.json',D/'verification.json',D/'independent_verification_v1.json',D/'failed_search_contexts_verification_v1.json',E/'budget_cut_ownership_relaxation_contract_v1_2026-10-19/verification.json'];seen=set();bindings={str(Path(__file__).resolve()):sha(Path(__file__))}
 while pending:
  p=pending.pop()
  if p in seen:continue
  seen.add(p);receipt=read(p);bindings[str(p)]=sha(p)
  if not isinstance(receipt,dict):continue
  for q,h in receipt.get('bindings',{}).items():
   assert sha(q)==h,(str(p),q);bindings[q]=h
   if Path(q).suffix=='.json':pending.append(Path(q))
 cuts=read(C/'independent_verification_v1.json');solves=read(S/'verification.json')['rows'];audits=read(D/'independent_verification_v1.json')['rows'];contexts=read(D/'failed_search_contexts_verification_v1.json')['rows'];contract=read(E/'budget_cut_ownership_relaxation_contract_v1_2026-10-19/verification.json');assert cuts['positive_paths_verified']==218 and cuts['negative_certificates_verified']==86 and cuts['original_edge_Bellman_inequalities_verified']==55351962
 assert all(r['status']=='SAT' and r['independent_structure_exact'] and r['certificate_or_model_verified'] and r['owner_function_assignments_checked']==32 and not r['route_feasibility_proved'] for r in solves)
 assert [r['transaction_installed_privately'] for r in audits]==[False,True,False] and [r['final_selected_NETs'] for r in audits]==[36,48,37];assert all(not r['conditional_package_complete'] and not r['committed'] and r['all_nonactor_old_trees_unchanged'] for r in audits);assert all(r['has_only_physical_capacity_mask'] and r['failed_NET_absent'] for r in contexts)
 generated=sum(sum(1 for _ in (D/r['case']/'generated_trees.jsonl').open()) for r in audits);paths=sum(r['new_connection_paths_verified'] for r in audits);assert generated==6 and paths==443
 decision=dict(status='ADDITIONAL_GRAPH_CUTS_CERTIFIED_ALL3_OWNERSHIP_RELAXATIONS_SAT_ALL_PHYSICAL_PACKAGES_INCOMPLETE',updated_utc=datetime.now(timezone.utc).isoformat(),bindings=bindings,additional_budget_cuts=cuts['rows'],new_positive_path_certificates=218,new_negative_certificates=86,new_original_edge_Bellman_inequalities_verified=55351962,ownership_contract={k:v for k,v in contract.items() if k!='bindings'},ownership_necessary_relaxations=solves,physical_transaction_audits=audits,actual_failed_search_contexts=contexts,new_complete_NET_tree_generations=generated,new_connection_paths_verified=paths,reused_prefix_connection_paths_reverified=sum(r['initial_connection_paths_reverified'] for r in audits),committed_packages=0,new_bank_candidates=0,unavailable_cases=[f'w{w:03d}/episode_{ep:02d}' for w in (96,128) for ep in (1,2,3)],labels_opened=False,budgets_changed=False,promoted=False,quality_and_utility_gates_pass=False,interpretation='New next-failure graph cuts contain4/3/4 resources; singleton nodes individually avoidable. Exact same outside premises admit old and new cuts together. Three ownership relaxations SAT, with96 actual owner functions exhaustively checked, but this is only necessary budget/capacity consistency. One fixed SAT allocation per case is physically attempted. Cases1/3 give NET567 IPIN41181 while preserving NET566 CHANX91658; rebuilding full NET566 fails another CID3255, and all private changes restore original state. Case2 gives NET741 CHANX92582 while preserving NET734 IPIN27263; both transaction trees install, then continuation fails at NET764/CID3779. All nonactor trees unchanged. No other allocation or order tried.',failure_context_scope='Actual failed-search states are materialized separately from rollback-restored final states. Cases1/3 snapshots contain staged NET567 but exclude failed NET566; their restored final states contain NET566 instead. All three current extra masks are already physically exhausted by the active states, so future graph-cut derivation can use capacity-only snapshots without silently importing extra algorithmic bans.',timing_scope='Proof, SAT and physical search are separate components; archived prefix production and complete native route evaluation excluded. No full-runtime, quality, native utility, family or hardware success claim.',next_step='Derive new constraints for NET566/CID3255 from actual staged failure contexts, not post-abort restored trees, and for NET764/CID3779 from its actual prefix. Accumulate multiple CID cuts for the same NET with shared owner variables, then define a new finite progress/selection policy before further model realization. A SAT necessary relaxation and one failed physical realization neither proves full routing feasibility nor refutes other allocations; do not relax original budgets or silently repeat completed trial.')
 out=D/'research_decision_v1.json';assert not out.exists();out.write_text(json.dumps(decision,indent=2)+'\n')
 for directory,status in ((C,'ALL3_ADDITIONAL_BUDGET_CUTS_INDEPENDENTLY_CERTIFIED'),(S,'ALL3_ACCUMULATED_OWNERSHIP_RELAXATIONS_SAT_NOT_ROUTING_PROOFS')):
  p=directory/'research_decision_v1.json';assert not p.exists();p.write_text(json.dumps(dict(status=status,primary_decision=str(out),primary_decision_sha256=sha(out),promoted=False),indent=2)+'\n')
 cp=E/'mmc_multiplicative_feedback_trial_v1_2026-10-10/supervision_checkpoint.json';state=read(cp)
 for key in ('prospective_external_family_additional_budget_resource_cuts_v1','prospective_external_family_accumulated_budget_cut_ownership_v1','prospective_external_family_joint_cut_owner_replacement_v1'):state[key]=dict(status=decision['status'],decision=str(out),decision_sha256=sha(out),updated_utc=decision['updated_utc'],promoted=False)
 tmp=cp.with_name(cp.name+'.accumulated_cuts.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');os.replace(tmp,cp);print(json.dumps(dict(status=decision['status'],verified_binding_files=len(bindings),negative_certificates=86,logical_SAT_cases=3,physical_complete_packages=0,new_tree_paths=paths)),flush=True)
if __name__=='__main__':main()
