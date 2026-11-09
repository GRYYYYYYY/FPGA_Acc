"""One assumption-admitted resource-clause root replacement per fixed case."""
import json,sys,time
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from conditional_package_tree_search_v1 import attempt,owned
from conditional_budget_cut_admission_v1 import verified_store,admit,evaluate
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'prospective_external_family_blocker_release_v1_2026-10-19';H=E/'prospective_external_family_monotone_witness_package_v1_2026-10-19';C=E/'prospective_external_family_budget_resource_cuts_v1_2026-10-19';O=E/'prospective_external_family_clause_guided_root_replacement_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 O.mkdir(exist_ok=False);matrix=E/'prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';inputs={r['case']:r for r in read(matrix)['rows']};_,digest,nodes,fields,rc,_=load_endpoints(inputs['w160/episode_01']['endpoint']);caps=fields['capacities'];slots={eid:i for i,eid in enumerate(fields['edge_ids'])};bindings={**closure([Path(__file__)]),str(matrix):sha(matrix)};artifact=C/'learned_conditional_budget_constraints_v1.json';clauses=verified_store(artifact,C/'independent_verification_v1.json')
 for p in (H/'independent_verification_v1.json',C/'independent_verification_v1.json',E/'conditional_budget_cut_admission_contract_v1_2026-10-19/verification.json'):
  proof=read(p);assert all(sha(q)==h for q,h in proof['bindings'].items());bindings[str(p)]=sha(p)
 bindings[str(artifact)]=sha(artifact);contract=E/'soft_demand_workspace_radix_contract_v3_2026-10-08/verification.json';kernel=read(contract);assert all(sha(q)==h for q,h in kernel['bindings'].items());binary=E/'soft_demand_workspace_radix_build_v3_2026-10-08/search.so';assert sha(binary)==kernel['bindings'][str(binary)];bindings.update(kernel['bindings']);bindings[str(contract)]=sha(contract)
 cases=[];data={};ledger=lambda state:Counter(n for c in state.values() for n in owned(c,fields,slots))
 for prior in read(H/'protocol.json')['cases']:
  case=prior['case'];assert inputs[case]['graph_sha256']==digest;bp=B/case/'candidate_bank.jsonl';pp=H/case/'final_conditional_trees.jsonl';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};initial={r['net_id']:r['candidate'] for r in map(json.loads,pp.read_text().splitlines())};ownership={net:owned(c,fields,slots) for net,c in initial.items()};package=set(prior['package_NETs']);outside=Counter()
  for net,options in bank.items():
   sets=[owned(c,fields,slots) for c in options];common=set.intersection(*sets);assert all(all(n in ns for ns in sets) for n in {n for ns in sets for n in ns if caps[n]>1})
   if net not in package:outside.update(common)
  admitted=[];chosen=[];targets=set();before=[]
  for clause in clauses:
   if clause['case']!=case:continue
   q=next(r for r in bank[clause['NET']][0]['records'] if r['connection_id']==clause['connection_id']);admitted.append(admit(clause,case,digest,q,outside));answer=evaluate(clause,ownership,outside);assert not answer['satisfied'];before.append(answer);eligible=sorted(set(clause['conditional_budget_cut'])&ownership[2]);assert eligible;chosen.append(eligible[0]);targets.add(clause['NET'])
  assert admitted and len(targets)==1;target=next(iter(targets));assert target not in initial and target in package;spec=dict(case=case,package_NETs=sorted(package),initial_selected_NETs=sorted(initial),root_NET=2,target_NET=target,chosen_root_avoid_nodes=sorted(set(chosen)),original_root_forbidden_nodes=prior['root_extra_forbidden_nodes'],admitted_constraint_CIDs=[c['connection_id'] for c in admitted],initial_clause_evaluations=before);cases.append(spec);data[case]=(bank,initial,outside,admitted)
  for p in (bp,pp):bindings[str(p)]=sha(p)
 p=H/'protocol.json';bindings[str(p)]=sha(p)
 policy='One staged root replacement per case, all cases fixed before searches. Admit every case clause only after verified-artifact, graph, CID/NET/endpoints, original budget and outside occupancy checks. For each currently violated clause choose the smallest cut node occupied by NET2; root search avoids these nodes plus original root union mask, against outside and every currently selected other NET tree. No other old tree changes. If root fails reject. If root succeeds, require all admitted clauses satisfied and stage one complete target-NET search against tentative root+old others. Only if both succeed atomically install root and target in private state; on target failure restore original state. Then generate remaining package NETs ascending ID once, checking all clauses and original budgets/capacities. First failure rejects whole package; no alternative literals/root attempts, backtracking, order/quota sweeps or partial external commits.'
 (O/'protocol.json').write_text(json.dumps(dict(policy=policy,cases=cases,unavailable_cases=[f'w{w:03d}/episode_{ep:02d}' for w in (96,128) for ep in (1,2,3)],bindings=bindings),indent=2)+'\n');rows=[]
 for spec in cases:
  tick=time.perf_counter();case=spec['case'];bank,initial,outside,admitted=data[case];state=dict(initial);out=O/case;out.mkdir(parents=True);events=[];failure=None;pair_installed=False;calls=0;target=spec['target_NET'];root_extra=set(spec['original_root_forbidden_nodes'])|set(spec['chosen_root_avoid_nodes'])
  with (out/'generated_trees.jsonl').open('x') as stream:
   others={net:c for net,c in state.items() if net!=2};template={r['connection_id']:r for r in bank[2][0]['records']};root,info=attempt(template,fields,nodes,rc,binary,slots,outside,ledger(others),root_extra);calls+=1;event=dict(call=calls,phase='ROOT_PROPOSAL',net_id=2,**info)
   if root is None:failure=event;events.append(dict(event,status='FAILED'))
   else:
    root['origin']='clause_guided_root';stream.write(json.dumps(dict(call=calls,net_id=2,candidate=root),separators=(',',':'))+'\n');stream.flush();tentative=dict(others);tentative[2]=root;answers=[evaluate(c,{net:owned(v,fields,slots) for net,v in tentative.items()},outside) for c in admitted];assert all(a['satisfied'] for a in answers);events.append(dict(event,status='ROOT_STAGED',clause_evaluations=answers));template={r['connection_id']:r for r in bank[target][0]['records']};candidate,info=attempt(template,fields,nodes,rc,binary,slots,outside,ledger(tentative));calls+=1;event=dict(call=calls,phase='TARGET_PROPOSAL',net_id=target,**info)
    if candidate is None:failure=event;events.append(dict(event,status='FAILED_ROOT_STAGE_ABORTED'))
    else:
     candidate['origin']='clause_guided_target';tentative[target]=candidate;assert all(outside[n]+count<=caps[n] for n,count in ledger(tentative).items());assert all(evaluate(c,{net:owned(v,fields,slots) for net,v in tentative.items()},outside)['satisfied'] for c in admitted);stream.write(json.dumps(dict(call=calls,net_id=target,candidate=candidate),separators=(',',':'))+'\n');stream.flush();state=tentative;pair_installed=True;events.append(dict(event,status='ROOT_AND_TARGET_INSTALLED_PRIVATELY'))
     for net in sorted(set(spec['package_NETs'])-set(state)):
      template={r['connection_id']:r for r in bank[net][0]['records']};candidate,info=attempt(template,fields,nodes,rc,binary,slots,outside,ledger(state));calls+=1;event=dict(call=calls,phase='COMPLETE_PACKAGE',net_id=net,**info)
      if candidate is None:failure=event;events.append(dict(event,status='FAILED'));break
      candidate['origin']='clause_guided_continuation_'+str(calls);state[net]=candidate;assert all(evaluate(c,{owner:owned(v,fields,slots) for owner,v in state.items()},outside)['satisfied'] for c in admitted);stream.write(json.dumps(dict(call=calls,net_id=net,candidate=candidate),separators=(',',':'))+'\n');stream.flush();events.append(dict(event,status='SELECTED_CONDITIONALLY'))
  if not pair_installed:assert state==initial
  status='PACKAGE_REPLACEMENT_FAILED_NO_COMMIT' if failure else 'CONDITIONAL_PACKAGE_COMPLETE_PENDING_AUDIT';assert failure or set(state)==set(spec['package_NETs']);final_evaluations=[evaluate(c,{net:owned(v,fields,slots) for net,v in state.items()},outside) for c in admitted];result=dict(case=case,status=status,package_NETs=len(spec['package_NETs']),initial_selected_NETs=len(initial),final_selected_NETs=sorted(state),pair_installed_privately=pair_installed,search_calls=calls,events=events,failure=failure,final_clause_evaluations=final_evaluations,committed=False,component_seconds=time.perf_counter()-tick);(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
  with (out/'final_conditional_trees.jsonl').open('x') as stream:
   for net,c in sorted(state.items()):stream.write(json.dumps(dict(net_id=net,candidate=c),separators=(',',':'))+'\n')
  rows.append({k:result[k] for k in ('case','status','package_NETs','final_selected_NETs','pair_installed_privately','search_calls','failure','committed','component_seconds')});print('CLAUSE_GUIDED_REPLACEMENT_TERMINAL',case,status,'pair_installed',pair_installed,'selected',len(state),'failed_phase',failure['phase'] if failure else None,flush=True)
  for p in (out/'generated_trees.jsonl',out/'final_conditional_trees.jsonl',out/'result.json'):bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items())
 (O/'verification.json').write_text(json.dumps(dict(status='ALL3_FIXED_CLAUSE_GUIDED_ROOT_REPLACEMENT_SEARCHES_TERMINAL',rows=rows,bindings={str(O/'protocol.json'):sha(O/'protocol.json'),**bindings},labels_opened=False,budgets_changed=False,unavailable_cases_preserved=6,committed_packages=0,scope='New resource-clause conditioned root proposals, not continuation of immutable-tree protected policy. No bank/native routing state changed. Clause satisfaction is necessary, not complete routability or forecast/native utility success. Component clocks exclude archived state production.'),indent=2)+'\n')
if __name__=='__main__':main()
