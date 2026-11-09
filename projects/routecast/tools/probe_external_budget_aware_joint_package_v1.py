"""One frozen witness-first/root-regeneration atomic package experiment."""
import json,sys,time
from collections import defaultdict,Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from soft_demand_workspace_bridge_v1 import Search
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'prospective_external_family_blocker_release_v1_2026-10-19';G=E/'prospective_external_family_global_mask_probe_v2_2026-10-19';H=E/'prospective_external_family_joint_release_package_v2_2026-10-19';O=E/'prospective_external_family_budget_aware_joint_package_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 O.mkdir(exist_ok=False);matrix=E/'prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';inputs={r['case']:r for r in read(matrix)['rows']};graph,digest,nodes,fields,rc,_=load_endpoints(inputs['w160/episode_01']['endpoint']);caps=fields['capacities'];slots={eid:i for i,eid in enumerate(fields['edge_ids'])};bindings={**closure([Path(__file__)]),str(matrix):sha(matrix)}
 for path in (B/'independent_verification_v1.json',G/'independent_verification_v1.json',H/'failure_ablation_v1.json'):
  receipt=read(path);assert all(sha(p)==h for p,h in receipt['bindings'].items());bindings[str(path)]=sha(path)
 contract=E/'soft_demand_workspace_radix_contract_v3_2026-10-08/verification.json';kernel=read(contract);assert all(sha(p)==h for p,h in kernel['bindings'].items());binary=E/'soft_demand_workspace_radix_build_v3_2026-10-08/search.so';assert kernel['bindings'][str(binary)]==sha(binary);bindings.update(kernel['bindings']);bindings[str(contract)]=sha(contract)
 def owned(candidate):
  ns={r['source'] for r in candidate['records']}
  for r in candidate['records']:ns.update(fields['dest_ranks'][slots[eid]] for eid in r['answer']['physical_edge_ids'])
  return ns
 prior={s['case']:s for s in read(H/'protocol.json')['cases']};ablations={r['case']:r for r in read(H/'failure_ablation_v1.json')['rows']};masks={s['case']:s['actions'][0]['forbidden_nodes'] for s in read(G/'protocol.json')['cases']};cases=[];data={}
 for ep in range(1,4):
  case=f'w160/episode_{ep:02d}';bp=B/case/'candidate_bank.jsonl';gp=G/case/'candidate_bank.jsonl';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};extended={r['net_id']:r['candidates'] for r in map(json.loads,gp.read_text().splitlines())};required=defaultdict(set);invariant={}
  for net,options in bank.items():
   sets=[owned(c) for c in options];common=set.intersection(*sets);invariant[net]=common;assert all(all(n in s for s in sets) for n in {n for s in sets for n in s if caps[n]>1})
   for n in common:required[n].add(net)
  package={2}|{net for n in owned(extended[2][-1]) if caps[n]==1 for net in required[n]-{2}};assert sorted(package)==prior[case]['package_NETs'];witness=ablations[case]['failure']['net_id'];assert witness in package and witness!=2;assert ablations[case]['failure']['fixed_root_order_independent_obstruction'];outside=Counter(n for net,ns in invariant.items() if net not in package for n in ns);assert all(count<=caps[n] for n,count in outside.items());order=[witness,2]+sorted(package-{witness,2});spec=dict(case=case,root_NET=2,reserved_witness_NET=witness,package_NETs=sorted(package),selection_order=order,root_extra_forbidden_nodes=masks[case]);cases.append(spec);data[case]=(bank,outside)
  for p in (bp,gp):bindings[str(p)]=sha(p)
 for p in (H/'protocol.json',G/'protocol.json'):bindings[str(p)]=sha(p)
 policy='Exactly one witness-first package per fixed case. Reuse prior package membership and outside mandatory ownership. Reserve one complete raw-shortest tree for the prior independently proven failed NET under outside-only capacity mask. Regenerate NET2 once avoiding outside mandatory owners, reserved tree, and unchanged original union-mask witness resources. Then generate remaining package NETs ascending ID, avoiding all exhausted outside+selected capacities. Original per-CID budgets unchanged. Fail first, reject whole package; no retries, root/order/quota sweeps, new members or partial commits. Success covers only package and fixed outside mandatory owners, not full outside completion.'
 (O/'protocol.json').write_text(json.dumps(dict(policy=policy,cases=cases,unavailable_cases=[f'w{w:03d}/episode_{ep:02d}' for w in (96,128) for ep in (1,2,3)],bindings=bindings),indent=2)+'\n');rows=[]
 for spec in cases:
  start=time.perf_counter();case=spec['case'];bank,outside=data[case];out=O/case;out.mkdir(parents=True);usage=Counter();selected=[];events=[];failure=None
  with (out/'selected_trees.jsonl').open('x') as stream:
   for step,net in enumerate(spec['selection_order']):
    phase='RESERVE_WITNESS' if step==0 else ('REGENERATE_ROOT' if step==1 else 'COMPLETE_PACKAGE');template={r['connection_id']:r for r in bank[net][0]['records']};source=next(iter(template.values()))['source'];taboo={n for n,cap in enumerate(caps) if outside[n]+usage[n]>=cap}
    if net==2:taboo.update(spec['root_extra_forbidden_nodes'])
    event=dict(step=step,phase=phase,net_id=net,forbidden_nodes=len(taboo),connections=len(template));modified=dict(fields);modified['capacities']=[0 if n in taboo else max(0,cap-outside[n]-usage[n]) for n,cap in enumerate(caps)]
    if source in taboo:failure=dict(event,reason='FORBIDDEN_SOURCE',failed_CIDs=sorted(template));events.append(dict(failure,status='FAILED'));break
    search=Search(modified,rc,binary);search.prepare({},0)
    try:
     dist,parent,settled=search.search(source,{r['sink'] for r in template.values()});bad=sorted(cid for cid,r in template.items() if r['sink'] not in settled or dist[r['sink']]>r['budget_integer'])
     if bad:
      failure=dict(event,reason='UNREACHABLE_OR_BUDGET',failed_CIDs=bad,failed_details=[dict(connection_id=cid,sink=template[cid]['sink'],settled=template[cid]['sink'] in settled,shortest_delay=int(dist[template[cid]['sink']]) if template[cid]['sink'] in settled else None,budget=template[cid]['budget_integer']) for cid in bad]);events.append(dict(failure,status='FAILED'));break
     records=[];parents={}
     for cid,old in sorted(template.items()):
      u=old['sink'];edges=[];seen=set()
      while u!=source:
       assert u not in seen and u not in taboo;seen.add(u);u,slot=parent[u];edges.append(fields['edge_ids'][slot])
      edges.reverse();delay=rc.path(source,old['sink'],edges);assert delay==dist[old['sink']]<=old['budget_integer'];u=source
      for eid in edges:
       v=fields['dest_ranks'][slots[eid]]
       if nodes[v].get('type')!='SINK':assert v not in parents or parents[v]==(u,eid);parents[v]=(u,eid)
       u=v
      records.append(dict(old,answer=dict(status='FOUND',physical_edge_ids=edges,delay=delay)))
     candidate=dict(origin='budget_aware_package_step_'+str(step),records=records);ns=owned(candidate);assert not ns&taboo;usage.update(ns);assert all(usage[n]+outside[n]<=caps[n] for n in ns);selected.append(net);stream.write(json.dumps(dict(net_id=net,candidate=candidate),separators=(',',':'))+'\n');stream.flush();events.append(dict(event,status='SELECTED_CONDITIONALLY'))
    finally:search.close()
  status='PACKAGE_SEARCH_FAILED_NO_COMMIT' if failure else 'PACKAGE_SEARCH_SUCCEEDED_PENDING_INDEPENDENT_AUDIT';assert failure or set(selected)==set(spec['package_NETs']);result=dict(case=case,status=status,selected_NETs=selected,package_NETs=len(spec['package_NETs']),failure=failure,events=events,committed=False,component_seconds=time.perf_counter()-start);(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');rows.append({k:result[k] for k in ('case','status','selected_NETs','package_NETs','failure','committed','component_seconds')});print('BUDGET_AWARE_PACKAGE_TERMINAL',case,status,'selected',len(selected),'failed_phase',failure['phase'] if failure else None,'failed_NET',failure['net_id'] if failure else None,flush=True)
  for p in (out/'result.json',out/'selected_trees.jsonl'):bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items())
 (O/'verification.json').write_text(json.dumps(dict(status='ALL3_FIXED_BUDGET_AWARE_ATOMIC_PACKAGE_SEARCHES_TERMINAL',rows=rows,bindings={str(O/'protocol.json'):sha(O/'protocol.json'),**bindings},labels_opened=False,budgets_changed=False,scope='No package or partial trees committed. Failure is specific to the frozen witness tree, original union mask, outside mandatory ownership and order, not general routing or alternative-root infeasibility.'),indent=2)+'\n')
if __name__=='__main__':main()
