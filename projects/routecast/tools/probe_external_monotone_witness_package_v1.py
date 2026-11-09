"""Monotone protected witnesses, structural termination bound, no tuned loop quota."""
import json,sys,time
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from conditional_package_tree_search_v1 import attempt,owned
from monotone_package_transaction_v1 import rank,rollback_owners
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'prospective_external_family_blocker_release_v1_2026-10-19';H=E/'prospective_external_family_conflict_directed_package_rollback_v1_2026-10-19';O=E/'prospective_external_family_monotone_witness_package_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 O.mkdir(exist_ok=False);matrix=E/'prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';inputs={r['case']:r for r in read(matrix)['rows']};_,_,nodes,fields,rc,_=load_endpoints(inputs['w160/episode_01']['endpoint']);caps=fields['capacities'];slots={eid:i for i,eid in enumerate(fields['edge_ids'])};bindings={**closure([Path(__file__)]),str(matrix):sha(matrix)}
 for p in (B/'independent_verification_v1.json',H/'independent_verification_v1.json',H/'failure_ablation_v1.json',E/'monotone_package_transaction_contract_v1_2026-10-19/verification.json'):
  proof=read(p);assert all(sha(q)==h for q,h in proof['bindings'].items());bindings[str(p)]=sha(p)
 contract=E/'soft_demand_workspace_radix_contract_v3_2026-10-08/verification.json';kernel=read(contract);assert all(sha(q)==h for q,h in kernel['bindings'].items());binary=E/'soft_demand_workspace_radix_build_v3_2026-10-08/search.so';assert sha(binary)==kernel['bindings'][str(binary)];bindings.update(kernel['bindings']);bindings[str(contract)]=sha(contract)
 ablations={r['case']:r for r in read(H/'failure_ablation_v1.json')['rows']};cases=[];data={}
 for prior in read(H/'protocol.json')['cases']:
  case=prior['case'];bp=B/case/'candidate_bank.jsonl';pp=H/case/'final_conditional_trees.jsonl';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};selected={r['net_id']:r['candidate'] for r in map(json.loads,pp.read_text().splitlines())};package=set(prior['package_NETs']);protected=set(ablations[case]['failure']['core_NETs']);assert 2 in protected and protected<=set(selected);outside=Counter()
  for net,options in bank.items():
   sets=[owned(c,fields,slots) for c in options];common=set.intersection(*sets);assert all(all(n in ns for ns in sets) for n in {n for ns in sets for n in ns if caps[n]>1})
   if net not in package:outside.update(common)
  initial_rank=rank(package,selected,protected);spec=dict(case=case,package_NETs=sorted(package),initial_selected_NETs=sorted(selected),initial_protected_NETs=sorted(protected),root_extra_forbidden_nodes=prior['root_extra_forbidden_nodes'],initial_rank=initial_rank,max_distinct_repairs=len(package)-len(protected),structural_search_call_bound=2*(initial_rank+1));cases.append(spec);data[case]=(bank,selected,protected,outside)
  for p in (bp,pp):bindings[str(p)]=sha(p)
 p=H/'protocol.json';bindings[str(p)]=sha(p)
 policy='One complete deterministic run per fixed case from audited conditional prefix and audited repaired core. Select smallest absent package NET. Try one raw complete tree against outside+all selected owners; on success insert without protection. On failure try once against outside+protected trees only. If that fails stop: fixed protected-core obstruction. Otherwise derive exact conflicting nonprotected owner rollback set, atomically remove it, insert challenger and protect it permanently, then again select smallest absent NET. NET2 retains original union mask. Every successful iteration strictly decreases rank=(N-|P|)(N+1)+(N-|S|), every repair adds a distinct protected NET, no protected tree changes. No tunable iteration/depth quota, order/parameter sweeps, expanded members, retries after core obstruction or partial commits. Natural bound2(R0+1) search calls is an invariant, not a swept budget.'
 (O/'protocol.json').write_text(json.dumps(dict(policy=policy,cases=cases,unavailable_cases=[f'w{w:03d}/episode_{ep:02d}' for w in (96,128) for ep in (1,2,3)],bindings=bindings),indent=2)+'\n');rows=[]
 for spec in cases:
  tick=time.perf_counter();case=spec['case'];bank,initial,initial_protected,outside=data[case];selected=dict(initial);protected=set(initial_protected);package=set(spec['package_NETs']);ownership={n:owned(c,fields,slots) for n,c in selected.items()};usage=Counter(n for ns in ownership.values() for n in ns);core_usage=Counter(n for net in protected for n in ownership[net]);assert all(outside[n]+usage[n]<=caps[n] for n in usage);out=O/case;out.mkdir(parents=True);calls=iterations=repairs=normal_insertions=0;failure=None
  with (out/'generated_trees.jsonl').open('x') as trees,(out/'events.jsonl').open('x') as events:
   while set(selected)!=package:
    iterations+=1;net=min(package-set(selected));template={r['connection_id']:r for r in bank[net][0]['records']};before=rank(package,selected,protected);extra=spec['root_extra_forbidden_nodes'] if net==2 else ();candidate,info=attempt(template,fields,nodes,rc,binary,slots,outside,usage,extra);calls+=1;event=dict(call=calls,iteration=iterations,net_id=net,mode='ALL_SELECTED',rank_before=before,protected_before=len(protected),selected_before=len(selected),**info)
    if candidate is not None:
     candidate['origin']='monotone_normal_call_'+str(calls);ns=owned(candidate,fields,slots);assert all(outside[n]+usage[n]+1<=caps[n] for n in ns);selected[net]=candidate;ownership[net]=ns;usage.update(ns);after=rank(package,selected,protected);assert after==before-1;normal_insertions+=1;trees.write(json.dumps(dict(call=calls,net_id=net,candidate=candidate),separators=(',',':'))+'\n');trees.flush();events.write(json.dumps(dict(event,status='INSERTED',rank_after=after),separators=(',',':'))+'\n');events.flush()
    else:
     events.write(json.dumps(dict(event,status='NEEDS_PROTECTED_CORE_SEARCH',rank_after=before),separators=(',',':'))+'\n');events.flush();candidate,info=attempt(template,fields,nodes,rc,binary,slots,outside,core_usage,extra);calls+=1;event=dict(call=calls,iteration=iterations,net_id=net,mode='PROTECTED_CORE',rank_before=before,protected_before=len(protected),selected_before=len(selected),**info)
     if candidate is None:
      failure=event;events.write(json.dumps(dict(event,status='PROTECTED_CORE_OBSTRUCTION',rank_after=before),separators=(',',':'))+'\n');events.flush();break
     candidate['origin']='monotone_repair_call_'+str(calls);ns=owned(candidate,fields,slots);removed=rollback_owners(caps,outside,ownership,protected,ns);assert removed and not set(removed)&protected
     for owner in removed:del selected[owner];del ownership[owner]
     selected[net]=candidate;ownership[net]=ns;protected.add(net);usage=Counter(n for nodeset in ownership.values() for n in nodeset);core_usage.update(ns);after=rank(package,selected,protected);assert after==before+len(removed)-len(package)-2<before;repairs+=1;assert repairs<=spec['max_distinct_repairs'];trees.write(json.dumps(dict(call=calls,net_id=net,candidate=candidate),separators=(',',':'))+'\n');trees.flush();events.write(json.dumps(dict(event,status='REPAIRED_AND_PROTECTED',rollback_NETs=removed,rank_after=after),separators=(',',':'))+'\n');events.flush();print('MONOTONE_REPAIR',case,'protected',len(protected),'challenger',net,'rollback',removed,'rank',after,flush=True)
    assert calls<=spec['structural_search_call_bound'] and protected<=set(selected)<=package
  assert calls<=spec['structural_search_call_bound'];status='PROTECTED_CORE_OBSTRUCTION_NO_COMMIT' if failure else 'CONDITIONAL_PACKAGE_COMPLETE_PENDING_AUDIT';assert failure or set(selected)==package
  with (out/'final_conditional_trees.jsonl').open('x') as stream:
   for net,c in sorted(selected.items()):stream.write(json.dumps(dict(net_id=net,candidate=c),separators=(',',':'))+'\n')
  result=dict(case=case,status=status,package_NETs=len(package),initial_selected_NETs=len(initial),final_selected_NETs=sorted(selected),initial_protected_NETs=sorted(initial_protected),final_protected_NETs=sorted(protected),initial_rank=spec['initial_rank'],final_rank=rank(package,selected,protected),iterations=iterations,search_calls=calls,repairs=repairs,normal_insertions=normal_insertions,failure=failure,committed=False,component_seconds=time.perf_counter()-tick);(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');rows.append({k:result[k] for k in ('case','status','package_NETs','final_selected_NETs','final_protected_NETs','iterations','search_calls','repairs','failure','committed','component_seconds')});print('MONOTONE_PACKAGE_TERMINAL',case,status,'selected',len(selected),'protected',len(protected),'calls',calls,'failed_NET',failure['net_id'] if failure else None,flush=True)
  for p in (out/'generated_trees.jsonl',out/'events.jsonl',out/'final_conditional_trees.jsonl',out/'result.json'):bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items())
 (O/'verification.json').write_text(json.dumps(dict(status='ALL3_MONOTONE_WITNESS_PACKAGE_SEARCHES_TERMINAL',rows=rows,bindings={str(O/'protocol.json'):sha(O/'protocol.json'),**bindings},unavailable_cases_preserved=6,labels_opened=False,budgets_changed=False,committed_packages=0,scope='Finite conditional-package mechanism only, no candidate-bank or native routing mutation. Core obstruction is specific to frozen protected trees and outside mandatory ownership, not general routing or predictor infeasibility. Component clocks exclude archived prefix generation.'),indent=2)+'\n')
if __name__=='__main__':main()
