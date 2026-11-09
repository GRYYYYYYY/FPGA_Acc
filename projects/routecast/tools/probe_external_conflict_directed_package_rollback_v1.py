"""One pre-frozen conflict-directed predecessor rollback per fixed case."""
import json,sys,time
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from conditional_package_tree_search_v1 import attempt,owned
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'prospective_external_family_blocker_release_v1_2026-10-19';H=E/'prospective_external_family_budget_aware_joint_package_v1_2026-10-19';O=E/'prospective_external_family_conflict_directed_package_rollback_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 O.mkdir(exist_ok=False);matrix=E/'prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';inputs={r['case']:r for r in read(matrix)['rows']};_,_,nodes,fields,rc,_=load_endpoints(inputs['w160/episode_01']['endpoint']);caps=fields['capacities'];slots={e:i for i,e in enumerate(fields['edge_ids'])};bindings={**closure([Path(__file__)]),str(matrix):sha(matrix)}
 for p in (B/'independent_verification_v1.json',H/'independent_verification_v1.json',H/'failure_ablation_v1.json'):
  receipt=read(p);assert all(sha(q)==h for q,h in receipt['bindings'].items());bindings[str(p)]=sha(p)
 contract=E/'soft_demand_workspace_radix_contract_v3_2026-10-08/verification.json';kernel=read(contract);assert all(sha(q)==h for q,h in kernel['bindings'].items());binary=E/'soft_demand_workspace_radix_build_v3_2026-10-08/search.so';assert sha(binary)==kernel['bindings'][str(binary)];bindings.update(kernel['bindings']);bindings[str(contract)]=sha(contract)
 ablations={r['case']:r for r in read(H/'failure_ablation_v1.json')['rows']};cases=[];data={}
 for prior in read(H/'protocol.json')['cases']:
  case=prior['case'];bp=B/case/'candidate_bank.jsonl';prefix=H/case/'selected_trees.jsonl';rp=H/case/'result.json';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};selected={r['net_id']:r['candidate'] for r in map(json.loads,prefix.read_text().splitlines())};old=read(rp);assert old['failure']['phase']=='COMPLETE_PACKAGE';target=old['failure']['net_id'];assert target not in selected;package=set(prior['package_NETs']);outside=Counter()
  for net,options in bank.items():
   sets=[owned(c,fields,slots) for c in options];common=set.intersection(*sets);assert all(all(n in ns for ns in sets) for n in {n for ns in sets for n in ns if caps[n]>1})
   if net not in package:outside.update(common)
  pinned={prior['reserved_witness_NET']}
  if not ablations[case]['failure']['fixed_pair_order_independent_obstruction']:pinned.add(2)
  assert pinned<=set(selected);spec=dict(case=case,package_NETs=sorted(package),initial_selected_NETs=sorted(selected),challenger_NET=target,pinned_NETs=sorted(pinned),root_extra_forbidden_nodes=prior['root_extra_forbidden_nodes']);cases.append(spec);data[case]=(bank,selected,outside)
  for p in (bp,prefix,rp):bindings[str(p)]=sha(p)
 p=H/'protocol.json';bindings[str(p)]=sha(p)
 policy='One conflict-directed rollback per case, no retry/depth/order/quota sweep. Start from independently audited prior conditional prefix, with same package and outside mandatory occupancy. Pin prior reserved witness; also pin NET2 only when prior fixed-pair mask admits all failing-NET connections. Search one complete challenger under outside+pinned trees. Derive exact rollback set: all nonpinned selected NET owners at any resource whose capacity would overflow on challenger insertion. Remove precisely those owners and install challenger atomically in private state. Reroute removed NETs ascending ID once, preserving NET2 original union mask; then complete remaining package ascending ID once. Fail first, reject package; no second rollback or partial commits. Success is conditional package feasibility, not outside optional completion or native legality.'
 (O/'protocol.json').write_text(json.dumps(dict(policy=policy,cases=cases,unavailable_cases=[f'w{w:03d}/episode_{ep:02d}' for w in (96,128) for ep in (1,2,3)],bindings=bindings),indent=2)+'\n');rows=[]
 for spec in cases:
  tick=time.perf_counter();case=spec['case'];bank,selected,outside=data[case];selected=dict(selected);out=O/case;out.mkdir(parents=True);events=[];failure=None;rollback=[];target=spec['challenger_NET'];pinned=set(spec['pinned_NETs']);count=lambda state:Counter(n for c in state.values() for n in owned(c,fields,slots));usage=count(selected)
  with (out/'generated_trees.jsonl').open('x') as stream:
   template={r['connection_id']:r for r in bank[target][0]['records']};candidate,info=attempt(template,fields,nodes,rc,binary,slots,outside,count({n:selected[n] for n in pinned}));event=dict(step=0,phase='CHALLENGER',net_id=target,**info)
   if candidate is None:failure=event;events.append(dict(event,status='FAILED'))
   else:
    candidate['origin']='conflict_rollback_challenger';ns=owned(candidate,fields,slots)
    for node in ns:
     if outside[node]+usage[node]+1>caps[node]:rollback.extend(net for net,c in selected.items() if net not in pinned and node in owned(c,fields,slots))
    rollback=sorted(set(rollback));assert rollback and not set(rollback)&pinned
    for net in rollback:del selected[net]
    usage=count(selected);assert all(outside[n]+usage[n]+1<=caps[n] for n in ns);selected[target]=candidate;usage.update(ns);stream.write(json.dumps(dict(step=0,net_id=target,candidate=candidate),separators=(',',':'))+'\n');stream.flush();events.append(dict(event,status='CHALLENGER_INSTALLED_WITH_ROLLBACK',rollback_NETs=rollback));print('ROLLBACK_SET',case,rollback,flush=True)
    schedule=[('REROUTE_PREDECESSOR',net) for net in rollback]+[('COMPLETE_PACKAGE',net) for net in sorted(set(spec['package_NETs'])-set(selected)-set(rollback))]
    for step,(phase,net) in enumerate(schedule,1):
     assert net not in selected;template={r['connection_id']:r for r in bank[net][0]['records']};candidate,info=attempt(template,fields,nodes,rc,binary,slots,outside,usage,spec['root_extra_forbidden_nodes'] if net==2 else ());event=dict(step=step,phase=phase,net_id=net,**info)
     if candidate is None:failure=event;events.append(dict(event,status='FAILED'));break
     candidate['origin']='conflict_rollback_step_'+str(step);ns=owned(candidate,fields,slots);assert all(outside[n]+usage[n]+1<=caps[n] for n in ns);selected[net]=candidate;usage.update(ns);stream.write(json.dumps(dict(step=step,net_id=net,candidate=candidate),separators=(',',':'))+'\n');stream.flush();events.append(dict(event,status='SELECTED_CONDITIONALLY'))
  status='PACKAGE_REPAIR_FAILED_NO_COMMIT' if failure else 'PACKAGE_REPAIR_SUCCEEDED_PENDING_INDEPENDENT_AUDIT';assert failure or set(selected)==set(spec['package_NETs']);result=dict(case=case,status=status,package_NETs=len(spec['package_NETs']),rollback_NETs=rollback,selected_NETs=sorted(selected),failure=failure,events=events,committed=False,component_seconds=time.perf_counter()-tick);(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
  with (out/'final_conditional_trees.jsonl').open('x') as stream:
   for net,c in sorted(selected.items()):stream.write(json.dumps(dict(net_id=net,candidate=c),separators=(',',':'))+'\n')
  rows.append({k:result[k] for k in ('case','status','package_NETs','rollback_NETs','selected_NETs','failure','committed','component_seconds')});print('CONFLICT_ROLLBACK_TERMINAL',case,status,'selected',len(selected),'failed_NET',failure['net_id'] if failure else None,flush=True)
  for p in (out/'result.json',out/'generated_trees.jsonl',out/'final_conditional_trees.jsonl'):bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items())
 (O/'verification.json').write_text(json.dumps(dict(status='ALL3_FIXED_CONFLICT_DIRECTED_ROLLBACK_SEARCHES_TERMINAL',rows=rows,bindings={str(O/'protocol.json'):sha(O/'protocol.json'),**bindings},labels_opened=False,budgets_changed=False,committed_packages=0,scope='Private conditional rollback experiment only. No candidate bank or global routing state changed. No general feasibility, forecast or native utility claim.'),indent=2)+'\n')
if __name__=='__main__':main()
