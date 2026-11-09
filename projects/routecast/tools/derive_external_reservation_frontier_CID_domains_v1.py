"""Proactive exact budget-admissible terminal ingress sets for all relevant CIDs."""
import json,sys,heapq,hashlib
from array import array
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from zero_rc_budget_certificate_graph_v1 import load_graph,candidate_nodes
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'prospective_external_family_blocker_release_v1_2026-10-19';H=E/'prospective_external_family_joint_cut_owner_replacement_v1_2026-10-19';CUTS=[E/'prospective_external_family_budget_resource_cuts_v1_2026-10-19',E/'prospective_external_family_additional_budget_resource_cuts_v1_2026-10-19'];P=E/'prospective_external_family_reservation_frontier_CID_request_v1_2026-10-19/request.json';O=E/'prospective_external_family_reservation_frontier_CID_domains_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 O.mkdir(exist_ok=False);bindings=closure([Path(__file__)]);clauses=[]
 for directory in CUTS:
  p=directory/'independent_verification_v1.json';v=read(p);assert all(sha(q)==h for q,h in v['bindings'].items());clauses.extend(read(directory/'learned_conditional_budget_constraints_v1.json')['clauses']);bindings[str(p)]=sha(p)
 for p in (H/'independent_verification_v1.json',H/'failed_search_contexts_verification_v1.json'):
  v=read(p);assert all(sha(q)==h for q,h in v['bindings'].items());bindings[str(p)]=sha(p)
 preflight=read(P);assert all(sha(q)==h for q,h in preflight['bindings'].items());bindings[str(P)]=sha(P);missing={r['case']:r['requirements']['NETs_missing_all_CID_domain_proofs'] for r in preflight['rows']}
 contexts={r['case']:r for r in read(H/'failed_search_contexts_verification_v1.json')['rows']};matrix=E/'prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';inputs={r['case']:r for r in read(matrix)['rows']};graph=Path(read(inputs['w160/episode_01']['endpoint'])['inputs']['graph']['path']);g=load_graph(graph);caps,types,us,vs,sw,w=g['caps'],g['types'],g['us'],g['vs'],g['switches'],g['weights'];bindings[str(graph)]=sha(graph);bindings[str(matrix)]=sha(matrix);cases=[];data={}
 for prior in read(H/'protocol.json')['cases']:
  case=prior['case'];bp=B/case/'candidate_bank.jsonl';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};package=set(prior['package_NETs']);outside=Counter()
  for net,options in bank.items():
   sets=[candidate_nodes(c,vs) for c in options];common=set.intersection(*sets)
   if net not in package:outside.update(common)
  assert all(count<=caps[node] for node,count in outside.items());nets=sorted(missing[case]);spec=dict(case=case,queried_NETs=nets,connections={net:sorted(r['connection_id'] for r in bank[net][0]['records']) for net in nets},outside_unique_NET_occupancy_sha256=hashlib.sha256(json.dumps(sorted(outside.items()),separators=(',',':')).encode()).hexdigest());cases.append(spec);data[case]=(bank,outside);bindings[str(bp)]=sha(bp)
 bindings[str(H/'protocol.json')]=sha(H/'protocol.json');policy='All CIDs, not just one failure per NET: fixed expanded NET set is exactly the new proved-cut target NETs missing complete CID coverage in the bound request; this is not actual actor selection. Cases with no missing actor remain explicit with empty query lists; prior domains are retained separately. Each case uses original per-CID budgets and outside-only mandatory occupancy; neither restored nor staged package trees are imposed. One capped full-source Dijkstra per NET with cap max(original CID budgets)+1. SINKs are terminal, other SOURCE nodes forbidden. A CID cut is every unit IPIN predecessor u of its original SINK for which d(source,u)+switch_delay<=its original budget. Every included node gets a complete original path witness; every excluded incoming edge gets a lower-bound exclusion from the capped forward Bellman potential. Independent replay must prove exact terminal-domain completeness. No new tree/route trial, budget tuning or dropped CIDs.'
 (O/'protocol.json').write_text(json.dumps(dict(policy=policy,cases=cases,bindings=bindings,unavailable_cases_preserved=6),indent=2)+'\n');bindings[str(O/'protocol.json')]=sha(O/'protocol.json');rows=[]
 for spec in cases:
  case=spec['case'];bank,outside=data[case];caseout=O/case;caseout.mkdir(parents=True)
  for net in spec['queried_NETs']:
   records=sorted(bank[net][0]['records'],key=lambda r:r['connection_id']);source=records[0]['source'];assert all(r['source']==source for r in records);maxbudget=max(r['budget_integer'] for r in records);limit=maxbudget+1;assert limit<2**64;blocked=bytearray(len(caps))
   for node,cap in enumerate(caps):blocked[node]=int(outside[node]>=cap or (types[node]=='SOURCE' and node!=source))
   assert not blocked[source] and types[source]=='SOURCE';dist=array('Q',[limit])*len(caps);dist[source]=0;parent=array('I',[2**32-1])*len(caps);queue=[(0,source)]
   while queue:
    value,u=heapq.heappop(queue)
    if value!=dist[u]:continue
    if types[u]=='SINK':continue
    for pos in range(g['offsets'][u],g['offsets'][u+1]):
     eid=g['order'][pos];v=vs[eid]
     if blocked[v]:continue
     candidate=value+w[sw[eid]]
     if candidate<dist[v]:dist[v]=candidate;parent[v]=eid;heapq.heappush(queue,(candidate,v))
   directory=caseout/f'NET_{net}';directory.mkdir();potential=directory/'forward_lower_bound_u64.bin'
   with potential.open('wb') as f:dist.tofile(f)
   bindings[str(potential)]=sha(potential);connection_results=[]
   for q in records:
    sink,budget=q['sink'],q['budget_integer'];assert types[sink]=='SINK' and not blocked[sink];eligible={};all_incoming=[]
    for pos in range(g['reverse_offsets'][sink],g['reverse_offsets'][sink+1]):
     eid=g['reverse_order'][pos];u=us[eid];assert types[u]=='IPIN' and caps[u]==1;all_incoming.append(eid)
     if not blocked[u] and dist[u]+w[sw[eid]]<=budget:
      key=(dist[u]+w[sw[eid]],eid)
      if u not in eligible or key<eligible[u]:eligible[u]=key
    assert eligible;witnesses=[]
    for u,(value,last) in sorted(eligible.items()):
     current=u;edges=[];seen=set()
     while current!=source:
      assert current not in seen and parent[current]!=2**32-1;seen.add(current);eid=parent[current];assert vs[eid]==current;edges.append(eid);current=us[eid]
     edges.reverse();edges.append(last);assert sum(w[sw[e]] for e in edges)==value<=budget;witnesses.append(dict(ingress_node=u,terminal_edge_id=last,physical_edge_ids=edges,delay=value))
    certificate=dict(case=case,NET=net,CID=q['connection_id'],source=source,sink=sink,budget_integer=budget,admissible_terminal_predecessors=sorted(eligible),all_incoming_edge_ids=sorted(all_incoming),witnesses=witnesses,forward_potential_file=str(potential),forward_potential_sha256=sha(potential),potential_cap=limit,byteorder=sys.byteorder,itemsize=8,scope='Every admissible budget path must terminate through one listed ingress; this is a necessary per-CID ownership cut, not a chosen complete NET tree.')
    p=directory/f'CID_{q["connection_id"]}.json';p.write_text(json.dumps(certificate,indent=2)+'\n');bindings[str(p)]=sha(p);connection_results.append(dict(CID=q['connection_id'],sink=sink,budget=budget,ingress_nodes=sorted(eligible),certificate=str(p)))
   row=dict(case=case,NET=net,source=source,connections=len(records),potential_cap=limit,potential_file=str(potential),terminal_domains=connection_results);rows.append(row);print('ALL_CID_TERMINAL_DOMAINS',json.dumps(dict(case=case,NET=net,connections=len(records),min_domain_size=min(len(q['ingress_nodes']) for q in connection_results),max_domain_size=max(len(q['ingress_nodes']) for q in connection_results))),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(O/'verification.json').write_text(json.dumps(dict(status='ALL_RELEVANT_NET_CID_TERMINAL_BUDGET_DOMAINS_PREPARED_PENDING_INDEPENDENT_REPLAY',rows=rows,bindings={str(O/'protocol.json'):sha(O/'protocol.json'),**bindings},labels_opened=False,budgets_changed=False,unavailable_cases_preserved=6,scope='Graph-derived full budget-admissible terminal ingress domains under fixed outside occupancy. No package tree or native state changed; certificates pending independent graph replay.'),indent=2)+'\n')
if __name__=='__main__':main()
