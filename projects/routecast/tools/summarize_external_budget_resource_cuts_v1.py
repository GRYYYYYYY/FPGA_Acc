"""Archive graph-wide path certificates under explicit conditional occupancy scopes."""
import json,hashlib,os
from pathlib import Path
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_budget_resource_cuts_v1_2026-10-19'
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
 pending=[D/n for n in ('protocol.json','verification.json','independent_verification_v1.json','learned_conditional_budget_constraints_v1.json')];seen=set();bindings={str(p):sha(p) for p in (Path(__file__).resolve(),D/'proof_scope_v1.md')}
 while pending:
  p=pending.pop()
  if p in seen:continue
  seen.add(p);receipt=read(p);bindings[str(p)]=sha(p)
  if not isinstance(receipt,dict):continue
  for q,h in receipt.get('bindings',{}).items():
   assert sha(q)==h,(str(p),q);bindings[q]=h
   if Path(q).suffix=='.json':pending.append(Path(q))
 provider=read(D/'verification.json');proof=read(D/'independent_verification_v1.json');constraints=read(D/'learned_conditional_budget_constraints_v1.json');assert proof['status']=='ALL3_BUDGET_RESOURCE_PATH_AND_BELLMAN_CERTIFICATES_INDEPENDENT_EXPAT_VERIFIED';assert provider['queries']==89 and proof['positive_paths_verified']==50 and proof['negative_certificates_verified']==39 and proof['original_edge_Bellman_inequalities_verified']==25365875
 assert [r['conditional_budget_cut'] for r in proof['rows']]==[[91658],[27263,117111],[91658]];assert all(not r['full_graph_budget_unavoidable_core_unit_nodes'] for r in proof['rows']);assert len(constraints['clauses'])==3
 decision=dict(status='ALL3_CONDITIONAL_BUDGET_RESOURCE_CUTS_CERTIFIED_OVER_ORIGINAL_GRAPH_PATHS',updated_utc=datetime.now(timezone.utc).isoformat(),bindings=bindings,case_results=proof['rows'],positive_path_certificates=50,negative_certificates=39,original_edge_Bellman_inequalities_verified=25365875,learned_constraint_file=str(D/'learned_conditional_budget_constraints_v1.json'),committed_trees=0,new_bank_candidates=0,unavailable_cases_preserved=6,labels_opened=False,budgets_changed=False,promoted=False,quality_and_utility_gates_pass=False,interpretation='The fixed-tree obstructions reduce to conditional resource constraints over all legal graph paths within unchanged budgets. Cases1/3 require CHANX91658 available for NET566 under the fixed outside occupancy; frozen NET2 occupies it. Case2 requires at least one of IPIN27263/CHANY117111 available for NET734; frozen NET2/NET723 occupy them respectively, and each node alone is avoidable. All occupied core unit nodes on certified full-graph baseline paths were tested; there is no unconditional budget-unavoidable frozen-core unit node in these cases. Therefore export conditional availability clauses, never unconditional reservations. A cut is necessary, not sufficient; restoring one node need not remove every obstruction in the original larger mask.',proof_scope='Every negative result has endpoint exclusion or a capped potential with p(source)=B+1,p(sink)=0 and p(u)<=w+p(v) on every allowed original XML edge. Positive results have full physical paths. This avoids reliance on sampled alternatives, finite bank completeness or shortest-parent DAG dominators.',next_step='Use assumption-bound resource-availability clauses to guide replacement of protected tree choices while retaining previously learned budget requirements. First validate clause-cache admission/invalidation against graph, endpoints, budgets and outside occupancy; then pre-freeze proposal generation and check complete NET trees and all accumulated clauses. Do not relax budgets, apply conditional reservations globally, or promote a model before original forecast/native utility/full-runtime/family/hardware gates.')
 out=D/'research_decision_v1.json';assert not out.exists();out.write_text(json.dumps(decision,indent=2)+'\n');cp=E/'mmc_multiplicative_feedback_trial_v1_2026-10-10/supervision_checkpoint.json';state=read(cp);state['prospective_external_family_budget_resource_cuts_v1']=dict(status=decision['status'],decision=str(out),decision_sha256=sha(out),updated_utc=decision['updated_utc'],promoted=False);tmp=cp.with_name(cp.name+'.budget_resource_cuts.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');os.replace(tmp,cp)
 print(json.dumps(dict(status=decision['status'],verified_binding_files=len(bindings),queries=89,positive_paths=50,negative_certificates=39,edge_inequalities=25365875)),flush=True)
if __name__=='__main__':main()
