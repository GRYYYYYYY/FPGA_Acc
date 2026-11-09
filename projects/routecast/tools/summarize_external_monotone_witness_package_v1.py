"""Archive structurally terminating monotone-package trial and frozen-core limits."""
import json,hashlib,os
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_monotone_witness_package_v1_2026-10-19'
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
 pending=[D/n for n in ('protocol.json','verification.json','independent_verification_v1.json','core_obstruction_analysis_v1.json')]+[E/'monotone_package_transaction_contract_v1_2026-10-19/verification.json'];seen=set();bindings={str(Path(__file__).resolve()):sha(Path(__file__))}
 while pending:
  p=pending.pop()
  if p in seen:continue
  seen.add(p);receipt=read(p);bindings[str(p)]=sha(p)
  if not isinstance(receipt,dict):continue
  for q,h in receipt.get('bindings',{}).items():
   assert sha(q)==h,(str(p),q);bindings[q]=h
   if Path(q).suffix=='.json':pending.append(Path(q))
 audits=read(D/'independent_verification_v1.json')['rows'];cores=read(D/'core_obstruction_analysis_v1.json')['rows'];provider=read(D/'verification.json')['rows'];contract=read(E/'monotone_package_transaction_contract_v1_2026-10-19/verification.json');assert len(audits)==len(cores)==len(provider)==3
 assert [r['repairs'] for r in audits]==[2,3,1] and [r['search_calls'] for r in audits]==[14,21,12];assert [r['inclusion_minimal_protected_NETs'] for r in cores]==[[2],[2,723],[2]];assert all(r['all_progress_and_immutable_protected_tree_invariants_pass'] and not r['conditional_package_complete'] and not r['committed'] for r in audits);assert all(r['status']=='PROTECTED_CORE_OBSTRUCTION_NO_COMMIT' for r in provider);assert all(r['outside_only_has_no_shortest_path_budget_obstruction'] and r['every_single_deletion_removes_all_shortest_path_budget_obstructions'] for r in cores)
 generated=sum(sum(1 for _ in (D/r['case']/'generated_trees.jsonl').open()) for r in audits);newpaths=sum(r['new_connection_paths_verified'] for r in audits);assert generated==35 and newpaths==3041
 decision=dict(status='MONOTONE_TERMINATION_VERIFIED_ALL3_PACKAGES_STOPPED_ON_FIXED_CORE_BUDGET_OBSTRUCTIONS',updated_utc=datetime.now(timezone.utc).isoformat(),bindings=bindings,rank_contract={k:v for k,v in contract.items() if k!='bindings'},package_audits=audits,inclusion_minimal_frozen_core_obstructions=cores,new_conditional_tree_generations=generated,new_connection_paths_verified=newpaths,reused_prefix_connection_paths_reverified=sum(r['initial_connection_paths_reverified'] for r in audits),committed_packages=0,new_bank_candidates=0,unavailable_cases_preserved=6,labels_opened=False,budgets_changed=False,promoted=False,quality_and_utility_gates_pass=False,interpretation='Termination and transaction safety are verified: ordinary insertions decrease integer rank by1; each repair permanently protects one new NET and strictly decreases rank; exact rollback never changes protected trees. Six repairs succeed across fixed cases. Searches terminate from protected-core budget obstructions at NET566/734/566, not structural limits. Original XML heap minimization gives inclusion-minimal fixed-tree cores[2]/[2,723]/[2]; all have shortest delay1169500012 above unchanged budget1000000000 in units1e-18 seconds. These are conditional fixed-tree counterexamples, not generally infeasible cores or minimal-cardinality proofs. Fixed whole-tree protection can lock in choices that prevent completion, so increasing repair counts does not resolve these recorded fixed-core obstructions.',timing_scope='Component clocks exclude archived prefix construction and independent evidence production. No complete end-to-end speedup, native timing, deployment, quality or utility success.',next_step='Distinguish fixed-path conflicts from graph-level budget-necessary occupancy before changing protection semantics. Audit whether a small set of occupied resources is unavoidable for failed CIDs under the original budget, or whether another path can replace a protected tree while preserving learned budget constraints. Old shortest-parent DAG dominators are not necessity proofs over all allowed-budget paths. Do not merely raise iteration quotas or relax original budgets. Keep full original forecast/native utility/family/full-time/hardware gates open or failed.')
 out=D/'research_decision_v1.json';assert not out.exists();out.write_text(json.dumps(decision,indent=2)+'\n');cp=E/'mmc_multiplicative_feedback_trial_v1_2026-10-10/supervision_checkpoint.json';state=read(cp);state['prospective_external_family_monotone_witness_package_v1']=dict(status=decision['status'],decision=str(out),decision_sha256=sha(out),updated_utc=decision['updated_utc'],promoted=False);tmp=cp.with_name(cp.name+'.monotone_package.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');os.replace(tmp,cp)
 print(json.dumps(dict(status=decision['status'],verified_binding_files=len(bindings),new_trees=generated,new_paths=newpaths,repairs=sum(r['repairs'] for r in audits),committed_packages=0)),flush=True)
if __name__=='__main__':main()
