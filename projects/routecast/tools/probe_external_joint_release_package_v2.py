"""One frozen atomic package per case, with deterministic conditional releases."""
import json,sys,time
from collections import defaultdict,Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from soft_demand_workspace_bridge_v1 import Search
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'prospective_external_family_blocker_release_v1_2026-10-19';G=E/'prospective_external_family_global_mask_probe_v2_2026-10-19';O=E/'prospective_external_family_joint_release_package_v2_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 O.mkdir(exist_ok=False);matrix=E/'prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';inputs={r['case']:r for r in read(matrix)['rows']};graph,digest,nodes,fields,rc,_=load_endpoints(inputs['w160/episode_01']['endpoint']);caps=fields['capacities'];slots={eid:i for i,eid in enumerate(fields['edge_ids'])};bindings={**closure([Path(__file__)]),str(matrix):sha(matrix)}
 for path in (B/'independent_verification_v1.json',G/'independent_verification_v1.json'):
  receipt=read(path);assert all(sha(p)==h for p,h in receipt['bindings'].items());bindings[str(path)]=sha(path)
 contract=E/'soft_demand_workspace_radix_contract_v3_2026-10-08/verification.json';kernel=read(contract);assert all(sha(p)==h for p,h in kernel['bindings'].items());binary=E/'soft_demand_workspace_radix_build_v3_2026-10-08/search.so';assert kernel['bindings'][str(binary)]==sha(binary);bindings.update(kernel['bindings']);bindings[str(contract)]=sha(contract)
 def owned(candidate):
  result={r['source'] for r in candidate['records']}
  for r in candidate['records']:result.update(fields['dest_ranks'][slots[eid]] for eid in r['answer']['physical_edge_ids'])
  return result
 cases=[];data={}
 for ep in range(1,4):
  case=f'w160/episode_{ep:02d}';bp=B/case/'candidate_bank.jsonl';gp=G/case/'candidate_bank.jsonl';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};extended={r['net_id']:r['candidates'] for r in map(json.loads,gp.read_text().splitlines())};required=defaultdict(set);invariant={}
  for net,options in bank.items():
   sets=[owned(c) for c in options];common=set.intersection(*sets);invariant[net]=common
   nonunit={node for s in sets for node in s if caps[node]>1};assert all(all(node in s for s in sets) for node in nonunit)
   for node in common:required[node].add(net)
  assert len(extended[2])==len(bank[2])+1 and extended[2][:-1]==bank[2];root=extended[2][-1];root_owned=owned(root);blockers=defaultdict(set)
  for node in root_owned:
   if caps[node]==1:
    for net in required[node]-{2}:blockers[net].add(node)
  package={2}|set(blockers);outside=Counter(node for net,ns in invariant.items() if net not in package for node in ns);assert all(count<=caps[node] for node,count in outside.items());order=sorted(package-{2});spec=dict(case=case,root_NET=2,root_option=len(bank[2]),package_NETs=sorted(package),replacement_order=order,root_blocking_resources={net:sorted(ns) for net,ns in sorted(blockers.items())});cases.append(spec);data[case]=(bank,root,outside);bindings[str(bp)]=sha(bp);bindings[str(gp)]=sha(gp)
 protocol=dict(policy='One frozen atomic package per fixed case: fixed previously audited NET2 union-mask tree plus all its original-bank mandatory unit owners. Outside-bank mandatory ownership preserved, outside nonunit ownership invariant and counted. Conditional release of every package member before search. Root selected first, remaining NETs ascending ID. Each searches exactly once avoiding all capacity exhausted by outside mandatory owners and already selected package trees. Original budgets. On first failure stop this package and reject whole package; do not append partial trees, alter root/order, refill or retry. A success is only capacity compatibility with outside mandatory ownership, not a completion of outside routes or native legality.',cases=cases,unavailable_cases=[f'w{w:03d}/episode_{ep:02d}' for w in (96,128) for ep in (1,2,3)],bindings=bindings)
 (O/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for spec in cases:
  start=time.perf_counter();case=spec['case'];bank,root,outside=data[case];directory=O/case;directory.mkdir(parents=True);selected={2:root};usage=Counter(owned(root));assert all(usage[node]+outside[node]<=caps[node] for node in usage);events=[];failure=None
  with (directory/'selected_trees.jsonl').open('x') as stream:
   stream.write(json.dumps(dict(net_id=2,candidate=root),separators=(',',':'))+'\n');stream.flush()
   for step,net in enumerate(spec['replacement_order']):
    template={r['connection_id']:r for r in bank[net][0]['records']};source=next(iter(template.values()))['source'];sinks={r['sink'] for r in template.values()};taboo={node for node in range(len(caps)) if outside[node]+usage[node]>=caps[node]};event=dict(step=step,net_id=net,forbidden_nodes=len(taboo),connections=len(template));modified=dict(fields);modified['capacities']=[max(0,cap-outside[n]-usage[n]) for n,cap in enumerate(caps)]
    if source in taboo:failure=dict(event,reason='FORBIDDEN_SOURCE',failed_CIDs=sorted(template));events.append(dict(failure,status='FAILED'));break
    search=Search(modified,rc,binary);search.prepare({},0)
    try:
     dist,parent,settled=search.search(source,sinks);bad=[cid for cid,r in template.items() if r['sink'] not in settled or dist[r['sink']]>r['budget_integer']]
     if bad:
      failure=dict(event,reason='UNREACHABLE_OR_BUDGET',failed_CIDs=sorted(bad),failed_details=[dict(connection_id=cid,sink=template[cid]['sink'],settled=template[cid]['sink'] in settled,shortest_delay=int(dist[template[cid]['sink']]) if template[cid]['sink'] in settled else None,budget=template[cid]['budget_integer']) for cid in sorted(bad)]);events.append(dict(failure,status='FAILED'));break
     records=[];parents={}
     for cid,old in sorted(template.items()):
      node=old['sink'];edges=[];seen=set()
      while node!=source:
       assert node not in seen and node not in taboo;seen.add(node);node,slot=parent[node];edges.append(fields['edge_ids'][slot])
      edges.reverse();delay=rc.path(source,old['sink'],edges);assert delay==dist[old['sink']]<=old['budget_integer'];node=source
      for eid in edges:
       slot=slots[eid];dest=fields['dest_ranks'][slot]
       if nodes[dest].get('type')!='SINK':assert dest not in parents or parents[dest]==(node,eid);parents[dest]=(node,eid)
       node=dest
      records.append(dict(old,answer=dict(status='FOUND',physical_edge_ids=edges,delay=delay)))
     candidate=dict(origin='joint_package_step_'+str(step),records=records);ns=owned(candidate);assert not ns&taboo;usage.update(ns);assert all(usage[n]+outside[n]<=caps[n] for n in ns);selected[net]=candidate;stream.write(json.dumps(dict(net_id=net,candidate=candidate),separators=(',',':'))+'\n');stream.flush();events.append(dict(event,status='SELECTED_CONDITIONALLY'))
    finally:search.close()
  status='PACKAGE_SEARCH_FAILED_NO_COMMIT' if failure else 'PACKAGE_SEARCH_SUCCEEDED_PENDING_INDEPENDENT_AUDIT';assert bool(failure) or set(selected)==set(spec['package_NETs']);result=dict(case=case,status=status,selected_NETs=sorted(selected),package_NETs=len(spec['package_NETs']),failure=failure,events=events,committed=False,component_seconds=time.perf_counter()-start);(directory/'result.json').write_text(json.dumps(result,indent=2)+'\n');rows.append({k:result[k] for k in ('case','status','package_NETs','selected_NETs','failure','committed','component_seconds')});print('JOINT_PACKAGE_TERMINAL',case,status,'selected',len(selected),'planned',len(spec['package_NETs']),'failed_NET',failure['net_id'] if failure else None,flush=True)
  for path in (directory/'selected_trees.jsonl',directory/'result.json'):bindings[str(path)]=sha(path)
 assert all(sha(p)==h for p,h in bindings.items())
 (O/'verification.json').write_text(json.dumps(dict(status='ALL3_FIXED_ATOMIC_JOINT_PACKAGE_SEARCHES_TERMINAL',rows=rows,bindings={str(O/'protocol.json'):sha(O/'protocol.json'),**bindings},labels_opened=False,budgets_changed=False,scope='No package committed or candidate bank changed. Partial search trees are diagnostic only. Failures are fixed root/order/outside-mask failures, not general routing or budget infeasibility.'),indent=2)+'\n')
if __name__=='__main__':main()
