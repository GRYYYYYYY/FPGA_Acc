"""One physical joint-NET realization of a verified necessary-owner SAT witness."""
import json,sys,time
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from conditional_package_tree_search_v1 import attempt,owned
from conditional_budget_cut_admission_v2 import verified_store,admit,evaluate
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'prospective_external_family_blocker_release_v1_2026-10-19';H=E/'prospective_external_family_joint_cut_owner_replacement_v1_2026-10-19';S=E/'prospective_external_family_state_preserving_accumulated_ownership_v1_2026-10-19';CUTS=[E/'prospective_external_family_budget_resource_cuts_v1_2026-10-19',E/'prospective_external_family_additional_budget_resource_cuts_v1_2026-10-19'];O=E/'prospective_external_family_reservation_only_owner_transaction_v1_2026-10-19'

CUTS=[E/f'prospective_external_family_{name}_v1_2026-10-19' for name in ['budget_resource_cuts','additional_budget_resource_cuts','all_CID_terminal_budget_domains','actor_CID_domain_expansion','staged_failure_budget_cuts','batched_actor_CID_domain_expansion','budget_closure_frontier_CID_domains']]
def read(p):return json.loads(Path(p).read_text())
def main():
 O.mkdir(exist_ok=False);bindings=closure([Path(__file__)]);clauses=[]
 for directory in CUTS:
  p=directory/'learned_conditional_budget_constraints_v1.json';v=directory/'independent_verification_v1.json';clauses.extend(verified_store(p,v));bindings[str(p)]=sha(p);bindings[str(v)]=sha(v)
 for p in (E/'prospective_external_family_owner_failure_mask_diagnosis_v3_2026-10-19/independent_verification_v1.json',H/'independent_verification_v1.json',S/'verification.json'):
  proof=read(p);assert all(sha(q)==h for q,h in proof['bindings'].items());bindings[str(p)]=sha(p)
 preflight=read(S/'physical_proposal_preflight_v1.json');assert all(sha(q)==h for q,h in preflight['bindings'].items());bindings[str(S/'physical_proposal_preflight_v1.json')]=sha(S/'physical_proposal_preflight_v1.json');ready={r['case']:r for r in preflight['rows'] if r['ready_for_new_physical_trial']};assert ready;models={r['case']:r for r in read(S/'verification.json')['rows']};matrix=E/'prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';inputs={r['case']:r for r in read(matrix)['rows']};_,digest,nodes,fields,rc,_=load_endpoints(inputs['w160/episode_01']['endpoint']);slots={eid:i for i,eid in enumerate(fields['edge_ids'])};caps=fields['capacities'];bindings[str(matrix)]=sha(matrix);contract=E/'soft_demand_workspace_radix_contract_v3_2026-10-08/verification.json';kernel=read(contract);assert all(sha(q)==h for q,h in kernel['bindings'].items());binary=E/'soft_demand_workspace_radix_build_v3_2026-10-08/search.so';assert sha(binary)==kernel['bindings'][str(binary)];bindings.update(kernel['bindings']);bindings[str(contract)]=sha(contract);data={};cases=[];ledger=lambda state:Counter(n for c in state.values() for n in owned(c,fields,slots))
 for prior in read(H/'protocol.json')['cases']:
  case=prior['case']
  if case not in ready:continue
  assert models[case]['status']=='SAT' and models[case]['certificate_or_model_verified'];bp=B/case/'candidate_bank.jsonl';fp=H/case/'final_conditional_trees.jsonl';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};initial={r['net_id']:r['candidate'] for r in map(json.loads,fp.read_text().splitlines())};ownership={n:owned(c,fields,slots) for n,c in initial.items()};package=set(prior['package_NETs']);outside=Counter()
  for net,options in bank.items():
   if net not in package:outside.update(set.intersection(*(owned(c,fields,slots) for c in options)))
  admitted=[]
  for clause in clauses:
   if clause['case']!=case:continue
   q=next(r for r in bank[clause['NET']][0]['records'] if r['connection_id']==clause['connection_id']);admitted.append(admit(clause,case,digest,q,outside))
  allocation={r['node']:r['required_owner_NET'] for r in models[case]['one_logical_owner_allocation']};assert len(allocation)==len(models[case]['one_logical_owner_allocation'])
  for c in admitted:assert any(allocation.get(n)==c['NET'] for n in c['conditional_budget_cut'])
  targets=sorted({owner for owner in allocation.values() if owner not in initial});moving=sorted({net for n,owner in allocation.items() for net,ns in ownership.items() if net!=owner and n in ns});missing=sorted({owner for n,owner in allocation.items() if n not in ownership.get(owner,set())});actors=sorted(set(missing)|set(moving));assert actors==ready[case]['requirements']['required_actor_NETs'];assert targets and actors and set(actors)<=package
  spec=dict(case=case,package_NETs=sorted(package),initial_selected_NETs=sorted(initial),allocated_resource_owners=allocation,new_target_NETs=targets,moving_old_NETs=moving,transaction_NETs=actors,transaction_order=targets+sorted(set(actors)-set(targets)),original_root_forbidden_nodes=prior['original_root_forbidden_nodes']);cases.append(spec);data[case]=(bank,initial,outside,admitted,allocation)
  for p in (bp,fp):bindings[str(p)]=sha(p)
 p=H/'protocol.json';bindings[str(p)]=sha(p);policy='One fixed reservation-only transaction per preflight-ready case with prior SAT allocation used only to protect resources reserved for other NETs, not force exact own resource selection. All original cuts, complete NET CIDs, budgets, capacities, common-parent tree and nonactor immutability remain mandatory. Own unselected terminal alternatives stay available; validate actual tree ownership intersects every own cut. Preserve original root policy. Same actor set and order as prior fixed trial, no search over assignments/orders. Full atomic rollback on any failure; save true staged failure snapshot. All actors succeed before private install, then one ascending-ID package continuation. No bank/native commits. This is a new physical construction contract, not exact realization of the archived owner model.'
 (O/'protocol.json').write_text(json.dumps(dict(policy=policy,cases=cases,excluded_preflight_cases=[r for r in preflight['rows'] if not r['ready_for_new_physical_trial']],bindings=bindings,unavailable_cases_preserved=6),indent=2)+'\n');rows=[]
 for spec in cases:
  tick=time.perf_counter();case=spec['case'];bank,initial,outside,admitted,allocation=data[case];out=O/case;out.mkdir(parents=True);state=dict(initial);staged={net:c for net,c in initial.items() if net not in spec['transaction_NETs']};failure=None;installed=False;events=[];calls=0
  with (out/'generated_trees.jsonl').open('x') as stream:
   for net in spec['transaction_order']:
    extra={n for n,owner in allocation.items() if owner!=net}
    if net==2:extra.update(spec['original_root_forbidden_nodes'])
    template={r['connection_id']:r for r in bank[net][0]['records']};candidate,info=attempt(template,fields,nodes,rc,binary,slots,outside,ledger(staged),extra);calls+=1;event=dict(call=calls,phase='TRANSACTION_NET',net_id=net,extra_forbidden_nodes=sorted(extra),**info)
    if candidate is None:
     failure=event;events.append(dict(event,status='FAILED_TRANSACTION_ABORTED'))
     snapshot=out/'failed_search_trees_v1.jsonl'
     with snapshot.open('x') as handle:
      for owner,tree in sorted(staged.items()):handle.write(json.dumps(dict(net_id=owner,candidate=tree),separators=(',',':'))+'\n')
     bindings[str(snapshot)]=sha(snapshot);break
    candidate['origin']='joint_cut_owner_actor_'+str(calls);ns=owned(candidate,fields,slots);assert all(ns.intersection(c['conditional_budget_cut']) for c in admitted if c['NET']==net);staged[net]=candidate;assert all(outside[n]+count<=caps[n] for n,count in ledger(staged).items());stream.write(json.dumps(dict(call=calls,net_id=net,candidate=candidate),separators=(',',':'))+'\n');stream.flush();events.append(dict(event,status='TREE_STAGED'))
   if failure is None:
    assert all(owned(staged[c['NET']],fields,slots).intersection(c['conditional_budget_cut']) for c in admitted); assert all(evaluate(c,{net:owned(v,fields,slots) for net,v in staged.items()},outside)['satisfied'] for c in admitted);state=staged;installed=True
    for net in sorted(set(spec['package_NETs'])-set(state)):
     template={r['connection_id']:r for r in bank[net][0]['records']};candidate,info=attempt(template,fields,nodes,rc,binary,slots,outside,ledger(state));calls+=1;event=dict(call=calls,phase='COMPLETE_PACKAGE',net_id=net,**info)
     if candidate is None:
      failure=event;events.append(dict(event,status='FAILED'))
      snapshot=out/'failed_search_trees_v1.jsonl'
      with snapshot.open('x') as handle:
       for owner,tree in sorted(state.items()):handle.write(json.dumps(dict(net_id=owner,candidate=tree),separators=(',',':'))+'\n')
      bindings[str(snapshot)]=sha(snapshot);break
     candidate['origin']='joint_cut_owner_continuation_'+str(calls);state[net]=candidate;assert all(evaluate(c,{owner:owned(v,fields,slots) for owner,v in state.items()},outside)['satisfied'] for c in admitted);stream.write(json.dumps(dict(call=calls,net_id=net,candidate=candidate),separators=(',',':'))+'\n');stream.flush();events.append(dict(event,status='SELECTED_CONDITIONALLY'))
  if not installed:assert state==initial
  status='JOINT_OWNER_TRANSACTION_FAILED_NO_COMMIT' if failure else 'CONDITIONAL_PACKAGE_COMPLETE_PENDING_AUDIT';result=dict(case=case,status=status,package_NETs=len(spec['package_NETs']),transaction_installed_privately=installed,transaction_NETs=spec['transaction_NETs'],final_selected_NETs=sorted(state),search_calls=calls,events=events,failure=failure,final_clause_evaluations=[evaluate(c,{net:owned(v,fields,slots) for net,v in state.items()},outside) for c in admitted],committed=False,component_seconds=time.perf_counter()-tick);(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
  with (out/'final_conditional_trees.jsonl').open('x') as stream:
   for net,c in sorted(state.items()):stream.write(json.dumps(dict(net_id=net,candidate=c),separators=(',',':'))+'\n')
  rows.append({k:result[k] for k in ('case','status','transaction_installed_privately','transaction_NETs','final_selected_NETs','search_calls','failure','committed','component_seconds')});print('JOINT_CUT_OWNER_TERMINAL',case,status,'installed',installed,'selected',len(state),'failed_NET',failure['net_id'] if failure else None,flush=True)
  for p in (out/'generated_trees.jsonl',out/'result.json',out/'final_conditional_trees.jsonl'):bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items());(O/'verification.json').write_text(json.dumps(dict(status='ALL_PREFLIGHT_READY_RESERVATION_ONLY_TRANSACTIONS_TERMINAL',rows=rows,bindings={str(O/'protocol.json'):sha(O/'protocol.json'),**bindings},labels_opened=False,budgets_changed=False,unavailable_cases_preserved=6,committed_packages=0,scope='One physical attempt to realize one necessary-owner SAT model; failure is not ownership-CNF UNSAT or general infeasibility. No candidate bank/native state mutated. Archived prefix, proof and solver production time excluded from component clocks.'),indent=2)+'\n')
if __name__=='__main__':main()
