"""Archive one-round conflict-directed rollback without promoting partial repairs."""
import json,hashlib,os
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_conflict_directed_package_rollback_v1_2026-10-19'
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
 pending=[D/n for n in ('protocol.json','verification.json','independent_verification_v1.json','failure_ablation_v1.json')];seen=set();bindings={str(Path(__file__).resolve()):sha(Path(__file__))}
 while pending:
  p=pending.pop()
  if p in seen:continue
  seen.add(p);d=read(p);bindings[str(p)]=sha(p)
  if not isinstance(d,dict):continue
  for q,h in d.get('bindings',{}).items():
   assert sha(q)==h,(str(p),q);bindings[q]=h
   if Path(q).suffix=='.json':pending.append(Path(q))
 audits=read(D/'independent_verification_v1.json')['rows'];ablations=read(D/'failure_ablation_v1.json')['rows'];provider=read(D/'verification.json')['rows'];assert len(audits)==len(ablations)==len(provider)==3;assert [r['rollback_NETs'] for r in audits]==[[2,80,84],[84],[2]];assert [r['final_conditional_NETs'] for r in audits]==[28,37,28]
 assert all(r['challenger_installed'] and not r['package_accepted'] and not r['committed'] for r in audits)
 assert all(r['status']=='PACKAGE_REPAIR_FAILED_NO_COMMIT' for r in provider)
 assert all(not r['failure']['original_pins_already_block_budget'] and not r['failure']['repaired_core_order_independent_obstruction'] for r in ablations)
 generated=sum(sum(1 for _ in (D/r['case']/'generated_trees.jsonl').open()) for r in audits);newpaths=sum(r['new_connection_paths_verified'] for r in audits);assert generated==31 and newpaths==1820
 decision=dict(status='ONE_CONFLICT_DIRECTED_ROLLBACK_REPAIRS_ALL_PRIOR_FAILURES_ALL3_PACKAGES_STILL_REJECTED',updated_utc=datetime.now(timezone.utc).isoformat(),bindings=bindings,package_audits=audits,failure_ablations=ablations,new_conditional_trees=generated,new_connection_paths_verified=newpaths,reused_prefix_connection_paths_reverified=sum(r['initial_connection_paths_verified'] for r in audits),committed_packages=0,new_bank_candidates=0,unavailable_cases_preserved=6,labels_opened=False,budgets_changed=False,promoted=False,quality_and_utility_gates_pass=False,interpretation='Exact challenger-path capacity conflicts select rollback sets[2,80,84]/[84]/[2], never pinned trees. Prior failed NETs287/388/388 are installed; every rolled-back predecessor is rebuilt successfully with original budgets and conditional capacities. Prefixes reach28/37/28 NETs, then fail at458/567/436. The fixed original pins and repaired core each permit all current failed-NET connection budgets; only the full additional prefix causes current failures. No order-independent impossibility claim for these repaired cores.',timing_scope='Search component clocks exclude archived prefix production and independent audits. This is not a matched end-to-end runtime or native speedup result.',next_step='Design a monotone protected-witness transaction policy with a structural termination bound, instead of simply increasing the previous one-round quota. A successful conflict repair adds a new protected NET; only nonprotected conflicting owners can be released and queued. Stop if exact search under outside+protected core violates an original budget. Derive and verify progress/rollback invariants before executing. Capacity remains a diagnostic distinct from congestion ranking, native utility, strict unseen-family, full runtime and hardware gates.')
 out=D/'research_decision_v1.json';assert not out.exists();out.write_text(json.dumps(decision,indent=2)+'\n');cp=E/'mmc_multiplicative_feedback_trial_v1_2026-10-10/supervision_checkpoint.json';state=read(cp);state['prospective_external_family_conflict_directed_package_rollback_v1']=dict(status=decision['status'],decision=str(out),decision_sha256=sha(out),updated_utc=decision['updated_utc'],promoted=False);tmp=cp.with_name(cp.name+'.conflict_rollback.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');os.replace(tmp,cp)
 print(json.dumps(dict(status=decision['status'],verified_binding_files=len(bindings),new_trees=generated,new_paths=newpaths,committed_packages=0)),flush=True)
if __name__=='__main__':main()
