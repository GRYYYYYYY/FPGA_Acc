"""Preflight fixed logical ownership proposals before any new physical search."""
import json
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from cut_owner_actor_requirements_v1 import required_actors
from zero_rc_budget_certificate_graph_v1 import load_graph,candidate_nodes
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prospective_external_family_continuation_complete_ownership_v1_2026-10-19';T=E/'prospective_external_family_all_CID_terminal_budget_domains_v1_2026-10-19';U=E/'prospective_external_family_actor_CID_domain_expansion_v1_2026-10-19';W=E/'prospective_external_family_batched_actor_CID_domain_expansion_v1_2026-10-19';Z=E/'prospective_external_family_budget_closure_frontier_CID_domains_v1_2026-10-19';K=E/'prospective_external_family_reservation_frontier_CID_domains_v1_2026-10-19';L=E/'prospective_external_family_reservation_root_CID_domains_v1_2026-10-19';M=E/'prospective_external_family_reservation_case02_owner_CID_domains_v1_2026-10-19';J=E/'prospective_external_family_frontier_continuation_CID_domains_v1_2026-10-19';H=E/'prospective_external_family_joint_cut_owner_replacement_v1_2026-10-19';B=E/'prospective_external_family_blocker_release_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 paths=[S/'verification.json',T/'independent_verification_v1.json',U/'independent_verification_v1.json',W/'independent_verification_v1.json',Z/'independent_verification_v1.json',K/'independent_verification_v1.json',L/'independent_verification_v1.json',M/'independent_verification_v1.json',J/'independent_verification_v1.json',H/'failed_search_contexts_verification_v1.json',E/'cut_owner_actor_requirements_contract_v1_2026-10-19/verification.json'];bindings={str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
 for p in paths:
  proof=read(p);assert all(sha(q)==h for q,h in proof['bindings'].items());bindings[str(p)]=sha(p)
 graph=next(Path(p) for p in read(T/'independent_verification_v1.json')['bindings'] if p.endswith('/rr_graph.xml'));g=load_graph(graph);coverage={};domain_rows=read(T/'independent_verification_v1.json')['rows']+read(U/'independent_verification_v1.json')['rows']+read(W/'independent_verification_v1.json')['rows']+read(Z/'independent_verification_v1.json')['rows']+read(K/'independent_verification_v1.json')['rows']+read(L/'independent_verification_v1.json')['rows']+read(M/'independent_verification_v1.json')['rows']+read(J/'independent_verification_v1.json')['rows']
 for r in domain_rows:assert r['all_original_CIDs_covered'];coverage.setdefault(r['case'],set()).add(r['NET'])
 contexts={r['case']:r for r in read(H/'failed_search_contexts_verification_v1.json')['rows']};rows=[]
 for model in read(S/'verification.json')['rows']:
  case=model['case']
  if model['status']!='SAT':
   rows.append(dict(case=case,logical_status=model['status'],ready_for_new_physical_trial=False,scope='No SAT ownership model available. UNKNOWN is no feasibility conclusion; certified UNSAT is limited to admitted outside/budget constraints. No retry or work-bound increase.'));continue
  fp=H/case/'final_conditional_trees.jsonl';bankfile=B/case/'candidate_bank.jsonl';state={r['net_id']:r['candidate'] for r in map(json.loads,fp.read_text().splitlines())};bank={r['net_id']:r['candidates'] for r in map(json.loads,bankfile.read_text().splitlines())};ownership={net:candidate_nodes(c,g['vs']) for net,c in state.items()};allocation={r['node']:r['required_owner_NET'] for r in model['one_logical_owner_allocation']};requirements=required_actors(allocation,ownership,coverage[case]);actors=set(requirements['required_actor_NETs']);context=contexts[case];actual_path=Path(context['snapshot']);actual={r['net_id']:r['candidate'] for r in map(json.loads,actual_path.read_text().splitlines())};fixed={net:c for net,c in state.items() if net not in actors};known_failed_search_unchanged=context['has_only_physical_capacity_mask'] and context['failed_NET'] in actors and context['failed_NET'] not in fixed and fixed==actual;missing={net:len(bank[net][0]['records']) for net in requirements['actors_missing_all_CID_domain_proofs']}
  for r in domain_rows:
   if r['case']==case:assert [d['CID'] for d in r['terminal_domains']]==sorted(q['connection_id'] for q in bank[r['NET']][0]['records'])
  row=dict(case=case,requirements=requirements,missing_actor_CID_counts=missing,known_failed_physical_search_would_be_unchanged=bool(known_failed_search_unchanged),known_failed_NET=context['failed_NET'],known_failed_CIDs=context['failed_CIDs'],ready_for_new_physical_trial=not missing and not known_failed_search_unchanged,scope='Necessary preflight only. Existing NETs missing their own assigned resources must move even when they displace nobody. Complete-CID terminal coverage is still not flow/tree sufficiency. Repeating a known physical failure with unchanged fixed trees and only extra reservations cannot help.');rows.append(row)
  for p in (fp,bankfile,actual_path):bindings[str(p)]=sha(p)
  print('ALL_CID_OWNER_PROPOSAL_PREFLIGHT',json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());p=S/'physical_proposal_preflight_v1.json';assert not p.exists();p.write_text(json.dumps(dict(status='ALL3_FIXED_OWNER_PROPOSALS_ACTOR_AND_BUDGET_COVERAGE_PREFLIGHT_COMPLETE',rows=rows,bindings=bindings,new_physical_searches=0,scope='Gap detection before new execution, no user-approval or research-goal blocker. Missing domains and new failure constraints remain actionable research work.'),indent=2)+'\n')
if __name__=='__main__':main()
