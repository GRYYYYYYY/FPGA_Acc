"""Independent XML tree, transaction replay and exact failure shortest-path audit."""
import json,heapq,hashlib,xml.etree.ElementTree as ET
from array import array
from fractions import Fraction
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'prospective_external_family_blocker_release_v1_2026-10-19';H=E/'prospective_external_family_joint_cut_owner_replacement_v1_2026-10-19';D=E/'prospective_external_family_state_preserving_owner_transaction_v1_2026-10-19';C=E/'prospective_external_family_budget_resource_cuts_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 protocol=read(D/'protocol.json');summary=read(D/'verification.json');priorproof=read(H/'independent_verification_v1.json');assert summary['status']=='ALL_PREFLIGHT_READY_STATE_PRESERVING_TRANSACTIONS_TERMINAL'
 for proof in (protocol,summary,priorproof):assert all(sha(p)==h for p,h in proof['bindings'].items())
 prior_specs={r['case']:r for r in read(H/'protocol.json')['cases']};matrix=E/'prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';inputs={r['case']:r for r in read(matrix)['rows']};graph=Path(read(inputs['w160/episode_01']['endpoint'])['inputs']['graph']['path']);caps=array('I');types=[];us=array('I');vs=array('I');switches=array('I');weights={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));types.append(e.get('type'));t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0
  elif e.tag=='switch' and parent=='switches':
   t=e.find('timing');assert all(Fraction(t.get(k,'0'))==0 for k in ('R','Cin','Cout','Cinternal'));value=Fraction(t.get('Tdel','0'))*10**18;assert value.denominator==1 and value>=0;weights[int(e.get('id'))]=value.numerator
  elif e.tag=='edge' and parent=='rr_edges':us.append(int(e.get('src_node')));vs.append(int(e.get('sink_node')));switches.append(int(e.get('switch_id')))
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
  stack.pop()
 offsets=array('I',[0])*(len(caps)+1)
 for u in us:offsets[u+1]+=1
 for i in range(len(caps)):offsets[i+1]+=offsets[i]
 cursor=array('I',offsets);edge_order=array('I',[0])*len(us)
 for eid,u in enumerate(us):edge_order[cursor[u]]=eid;cursor[u]+=1
 def owned(c):
  ns={r['source'] for r in c['records']}
  for r in c['records']:ns.update(vs[e] for e in r['answer']['physical_edge_ids'])
  return ns
 def count(state):return Counter(n for c in state.values() for n in owned(c))
 def mask(outside,usage,extra=()):return {n for n,cap in enumerate(caps) if outside[n]+usage[n]>=cap}|set(extra)
 def audit_tree(net,candidate,taboo,bank):
  original={r['connection_id']:r for r in bank[net][0]['records']};records={r['connection_id']:r for r in candidate['records']};assert len(records)==len(candidate['records']) and set(records)==set(original);parents={}
  for cid,r in records.items():
   for k,v in original[cid].items():
    if k!='answer':assert r[k]==v
   u=r['source'];seen={u};assert u not in taboo and caps[u]>0 and types[u]=='SOURCE';delay=0
   for pos,eid in enumerate(r['answer']['physical_edge_ids']):
    assert type(eid) is int and 0<=eid<len(us) and us[eid]==u;v=vs[eid];assert v not in seen and v not in taboo and caps[v]>0
    if pos<len(r['answer']['physical_edge_ids'])-1:assert types[v] not in ('SOURCE','SINK')
    if types[v]!='SINK':assert v not in parents or parents[v]==(u,eid);parents[v]=(u,eid)
    seen.add(v);delay+=weights[switches[eid]];u=v
   assert u==r['sink'] and types[u]=='SINK' and delay==r['answer']['delay']<=r['budget_integer']
  return len(records)
 def shortest(source,targets,taboo):
  if source in taboo:return {}
  dist={source:0};done={};queue=[(0,source)];pending=set(targets)
  while queue and pending:
   value,u=heapq.heappop(queue)
   if u in done or dist[u]!=value:continue
   done[u]=value;pending.discard(u)
   if types[u]=='SINK':continue
   for pos in range(offsets[u],offsets[u+1]):
    eid=edge_order[pos];v=vs[eid]
    if v in taboo or types[v]=='SOURCE':continue
    d=value+weights[switches[eid]]
    if d<dist.get(v,10**100):dist[v]=d;heapq.heappush(queue,(d,v))
  return {sink:done[sink] for sink in targets if sink in done}
 artifact=C/'learned_conditional_budget_constraints_v1.json';cutproof=C/'independent_verification_v1.json';cp=read(cutproof);assert cp['bindings'][str(artifact)]==sha(artifact) and all(sha(p)==h for p,h in cp['bindings'].items());allclauses=read(artifact)['clauses'];graph_hash=sha(graph)
 def outside_digest(outside):return hashlib.sha256(json.dumps(sorted((node,count) for node,count in outside.items() if count),separators=(',',':')).encode()).hexdigest()
 def evaluations(clauses,state,outside):
  ownership={net:owned(c) for net,c in state.items()};answers=[]
  for clause in clauses:
   available=[];blocked={}
   for node in clause['conditional_budget_cut']:
    owners=sorted(net for net,ns in ownership.items() if net!=clause['NET'] and node in ns)
    if outside[node]==0 and not owners:available.append(node)
    else:blocked[str(node)]=dict(outside_owners=outside[node],package_other_NETs=owners)
   answers.append(dict(satisfied=bool(available),available_nodes=available,blocked_nodes=blocked))
  return answers
 def failure_check(event,template,taboo):
  source=next(iter(template.values()))['source'];answers=shortest(source,{r['sink'] for r in template.values()},taboo);bad=sorted(cid for cid,r in template.items() if r['sink'] not in answers or answers[r['sink']]>r['budget_integer']);assert bad and bad==event['failed_CIDs']
  for detail in event.get('failed_details',[]):assert detail['settled']==(detail['sink'] in answers) and detail['shortest_delay']==answers.get(detail['sink']) and detail['budget']==template[detail['connection_id']]['budget_integer']
  return dict(net_id=event['net_id'],phase=event['phase'],failed_CIDs=bad,unreachable=sum(template[cid]['sink'] not in answers for cid in bad),details=[dict(connection_id=cid,shortest_delay=answers.get(template[cid]['sink']),budget=template[cid]['budget_integer']) for cid in bad],independent_XML_shortest_paths_match=True)
 N=E/'prospective_external_family_additional_budget_resource_cuts_v1_2026-10-19';newproof=N/'independent_verification_v1.json';np=read(newproof);assert all(sha(p)==h for p,h in np['bindings'].items());allclauses.extend(read(N/'learned_conditional_budget_constraints_v1.json')['clauses']);S=E/'prospective_external_family_state_preserving_accumulated_ownership_v1_2026-10-19';sp=S/'verification.json';models=read(sp);assert all(sha(p)==h for p,h in models['bindings'].items());models={r['case']:r for r in models['rows']};rows=[];bindings={str(p):sha(p) for p in (D/'protocol.json',D/'verification.json',H/'protocol.json',H/'independent_verification_v1.json',artifact,cutproof,newproof,N/'learned_conditional_budget_constraints_v1.json',sp,graph,Path(__file__).resolve())}
 from conditional_budget_cut_admission_v2 import verified_store
 for name in ['all_CID_terminal_budget_domains','actor_CID_domain_expansion','staged_failure_budget_cuts','batched_actor_CID_domain_expansion','budget_closure_frontier_CID_domains']:
  directory=E/f'prospective_external_family_{name}_v1_2026-10-19';ap=directory/'learned_conditional_budget_constraints_v1.json';vp=directory/'independent_verification_v1.json';allclauses.extend(verified_store(ap,vp));bindings[str(ap)]=sha(ap);bindings[str(vp)]=sha(vp)
 preflight_path=S/'physical_proposal_preflight_v1.json';preflight=read(preflight_path);assert all(sha(q)==h for q,h in preflight['bindings'].items());ready={r['case']:r for r in preflight['rows'] if r['ready_for_new_physical_trial']};assert {r['case'] for r in protocol['cases']}==set(ready);bindings[str(preflight_path)]=sha(preflight_path)
 for spec in protocol['cases']:
  case=spec['case'];prior=prior_specs[case];bp=B/case/'candidate_bank.jsonl';pp=H/case/'final_conditional_trees.jsonl';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};initial_rows=list(map(json.loads,pp.read_text().splitlines()));initial={r['net_id']:r['candidate'] for r in initial_rows};assert len(initial)==len(initial_rows);package=set(prior['package_NETs']);assert spec['package_NETs']==sorted(package) and spec['initial_selected_NETs']==sorted(initial) and spec['original_root_forbidden_nodes']==prior['original_root_forbidden_nodes'];outside=Counter()
  for net,options in bank.items():
   sets=[owned(c) for c in options];common=set.intersection(*sets)
   if net not in package:outside.update(common)
  clauses=[c for c in allclauses if c['case']==case]
  for c in clauses:
   q=next(r for r in bank[c['NET']][0]['records'] if r['connection_id']==c['connection_id']);assert c['graph_sha256']==graph_hash and c['outside_unique_NET_occupancy_sha256']==outside_digest(outside);assert (c['connection_id'],c['NET'],c['source'],c['sink'],c['budget_integer'])==(q['connection_id'],q['net_id'],q['source'],q['sink'],q['budget_integer']);assert all(caps[n]==1 for n in c['conditional_budget_cut'])
  allocation={r['node']:r['required_owner_NET'] for r in models[case]['one_logical_owner_allocation']};assert {int(n):net for n,net in spec['allocated_resource_owners'].items()}==allocation
  for c in clauses:assert any(allocation.get(n)==c['NET'] for n in c['conditional_budget_cut'])
  ownership={net:owned(c) for net,c in initial.items()};targets=sorted(set(allocation.values())-set(initial));moving=sorted({net for n,owner in allocation.items() for net,ns in ownership.items() if net!=owner and n in ns});missing={owner for n,owner in allocation.items() if n not in ownership.get(owner,set())};actors=sorted(missing|set(moving));assert actors==ready[case]['requirements']['required_actor_NETs'];order=targets+sorted(set(actors)-set(targets));assert spec['new_target_NETs']==targets and spec['moving_old_NETs']==moving and spec['transaction_NETs']==actors and spec['transaction_order']==order;checked={};initial_paths=0
  for row in initial_rows:
   net=row['net_id'];initial_paths+=audit_tree(net,row['candidate'],mask(outside,count(checked),spec['original_root_forbidden_nodes'] if net==2 else ()),bank);checked[net]=row['candidate'];usage=count(checked);assert all(outside[n]+usage[n]<=caps[n] for n in usage)
  out=D/case;result=read(out/'result.json');events=result['events'];generated_rows=list(map(json.loads,(out/'generated_trees.jsonl').read_text().splitlines()));generated={r['call']:r for r in generated_rows};assert len(generated)==len(generated_rows);state=dict(initial);staged={net:c for net,c in initial.items() if net not in actors};installed=False;failure=None;newpaths=0;success_calls=set();continuation=[]
  for call,event in enumerate(events,1):
   assert event['call']==call
   if call<=len(order):
    net=order[call-1];assert event['phase']=='TRANSACTION_NET' and event['net_id']==net;extra={n for n,owner in allocation.items() if owner!=net}
    for c in clauses:
     if c['NET']==net:extra.update(n for n in c['conditional_budget_cut'] if allocation.get(n)!=net)
    if net==2:extra.update(spec['original_root_forbidden_nodes'])
    assert event['extra_forbidden_nodes']==sorted(extra);taboo=mask(outside,count(staged),extra)
   else:
    assert installed;net=continuation[call-len(order)-1];assert event['phase']=='COMPLETE_PACKAGE' and event['net_id']==net;taboo=mask(outside,count(state))
   assert net not in (staged if call<=len(order) else state);template={r['connection_id']:r for r in bank[net][0]['records']};assert event['forbidden_nodes']==len(taboo) and event['connections']==len(template)
   if event['status'] in ('FAILED_TRANSACTION_ABORTED','FAILED'):
    assert call==len(events) and call not in generated;failure=failure_check(event,template,taboo);assert result['failure']=={k:v for k,v in event.items() if k!='status'}
    if call<=len(order):assert event['status']=='FAILED_TRANSACTION_ABORTED' and not installed and state==initial
    snapshot_path=out/'failed_search_trees_v1.jsonl';snapshot_rows=list(map(json.loads,snapshot_path.read_text().splitlines()));snapshot={r['net_id']:r['candidate'] for r in snapshot_rows};assert len(snapshot)==len(snapshot_rows) and snapshot==(staged if call<=len(order) else state);bindings[str(snapshot_path)]=sha(snapshot_path)
    break
   assert call in generated and generated[call]['net_id']==net;candidate=generated[call]['candidate'];success_calls.add(call);newpaths+=audit_tree(net,candidate,taboo,bank)
   if call<=len(order):
    assert event['status']=='TREE_STAGED';assert {n for n,owner in allocation.items() if owner==net}<=owned(candidate);staged[net]=candidate;usage=count(staged);assert all(outside[n]+usage[n]<=caps[n] for n in usage)
    if call==len(order):
     assert all(n in owned(staged[owner]) for n,owner in allocation.items()) and all(a['satisfied'] for a in evaluations(clauses,staged,outside));state=staged;installed=True;continuation=sorted(package-set(state))
   else:
    assert event['status']=='SELECTED_CONDITIONALLY';state[net]=candidate;usage=count(state);assert all(outside[n]+usage[n]<=caps[n] for n in usage) and all(a['satisfied'] for a in evaluations(clauses,state,outside))
  assert set(generated)==success_calls;assert result['search_calls']==len(events) and result['transaction_installed_privately']==installed and result['transaction_NETs']==actors and result['final_selected_NETs']==sorted(state);assert not result['committed'];final_rows=list(map(json.loads,(out/'final_conditional_trees.jsonl').read_text().splitlines()));final={r['net_id']:r['candidate'] for r in final_rows};assert len(final)==len(final_rows) and final==state;assert result['final_clause_evaluations']==evaluations(clauses,state,outside);assert all(state[n]==initial[n] for n in initial if n not in actors)
  if not installed:assert state==initial
  if failure:assert result['status']=='JOINT_OWNER_TRANSACTION_FAILED_NO_COMMIT'
  else:assert result['status']=='CONDITIONAL_PACKAGE_COMPLETE_PENDING_AUDIT' and set(state)==package
  row=dict(case=case,transaction_NETs=actors,transaction_order=order,transaction_installed_privately=installed,initial_selected_NETs=len(initial),final_selected_NETs=len(state),all_nonactor_old_trees_unchanged=True,original_state_restored_if_transaction_failed=installed or state==initial,all_admitted_clauses_hold_in_final_state=all(a['satisfied'] for a in evaluations(clauses,state,outside)),initial_connection_paths_reverified=initial_paths,new_connection_paths_verified=newpaths,search_calls=len(events),conditional_package_complete=failure is None,committed=False,failure=failure);rows.append(row)
  for p in (bp,pp,out/'generated_trees.jsonl',out/'final_conditional_trees.jsonl',out/'result.json'):bindings[str(p)]=sha(p)
  print('JOINT_CUT_OWNER_INDEPENDENT_AUDIT',json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL_PREFLIGHT_READY_OWNER_TRANSACTIONS_AND_ABORTS_INDEPENDENT_XML_VERIFIED',rows=rows,bindings=bindings,scope='One fixed necessary-owner SAT witness realized or rejected by full original NET path/budget/capacity checks, exact extra masks, old nonactor immutability and atomic restore. SAT relaxation does not guarantee physical realization; physical failure does not refute other ownership assignments or general routing. No native, ranking or utility success.'),indent=2)+'\n')
if __name__=='__main__':main()
