"""Independent XML tree, transaction replay and exact failure shortest-path audit."""
import json,heapq,hashlib,xml.etree.ElementTree as ET
from array import array
from fractions import Fraction
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'prospective_external_family_blocker_release_v1_2026-10-19';H=E/'prospective_external_family_monotone_witness_package_v1_2026-10-19';D=E/'prospective_external_family_clause_guided_root_replacement_v1_2026-10-19';C=E/'prospective_external_family_budget_resource_cuts_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 protocol=read(D/'protocol.json');summary=read(D/'verification.json');priorproof=read(H/'independent_verification_v1.json');assert summary['status']=='ALL3_FIXED_CLAUSE_GUIDED_ROOT_REPLACEMENT_SEARCHES_TERMINAL'
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
 rows=[];bindings={str(p):sha(p) for p in (D/'protocol.json',D/'verification.json',H/'protocol.json',H/'independent_verification_v1.json',artifact,cutproof,graph,Path(__file__).resolve())}
 for spec in protocol['cases']:
  case=spec['case'];prior=prior_specs[case];bp=B/case/'candidate_bank.jsonl';pp=H/case/'final_conditional_trees.jsonl';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};initial_rows=list(map(json.loads,pp.read_text().splitlines()));initial={r['net_id']:r['candidate'] for r in initial_rows};package=set(prior['package_NETs']);assert len(initial)==len(initial_rows) and spec['initial_selected_NETs']==sorted(initial) and spec['package_NETs']==sorted(package);assert spec['original_root_forbidden_nodes']==prior['root_extra_forbidden_nodes'];outside=Counter()
  for net,options in bank.items():
   sets=[owned(c) for c in options];common=set.intersection(*sets);assert all(all(n in ns for ns in sets) for n in {n for ns in sets for n in ns if caps[n]>1})
   if net not in package:outside.update(common)
  clauses=[c for c in allclauses if c['case']==case];assert clauses;targets=set();chosen=[]
  for clause in clauses:
   q=next(r for r in bank[clause['NET']][0]['records'] if r['connection_id']==clause['connection_id']);assert clause['graph_sha256']==graph_hash and clause['outside_unique_NET_occupancy_sha256']==outside_digest(outside);assert (clause['connection_id'],clause['NET'],clause['source'],clause['sink'],clause['budget_integer'])==(q['connection_id'],q['net_id'],q['source'],q['sink'],q['budget_integer']);assert all(caps[n]==1 for n in clause['conditional_budget_cut']);eligible=sorted(set(clause['conditional_budget_cut'])&owned(initial[2]));assert eligible;chosen.append(eligible[0]);targets.add(clause['NET'])
  assert len(targets)==1 and spec['target_NET']==next(iter(targets)) and spec['chosen_root_avoid_nodes']==sorted(set(chosen));assert spec['admitted_constraint_CIDs']==[c['connection_id'] for c in clauses];assert spec['initial_clause_evaluations']==evaluations(clauses,initial,outside) and not any(a['satisfied'] for a in spec['initial_clause_evaluations']);target=spec['target_NET'];assert target not in initial and target in package;initial_paths=0;checked={}
  for row in initial_rows:
   net=row['net_id'];initial_paths+=audit_tree(net,row['candidate'],mask(outside,count(checked),spec['original_root_forbidden_nodes'] if net==2 else ()),bank);checked[net]=row['candidate'];usage=count(checked);assert all(outside[n]+usage[n]<=caps[n] for n in usage)
  out=D/case;result=read(out/'result.json');events=result['events'];generated_rows=list(map(json.loads,(out/'generated_trees.jsonl').read_text().splitlines()));generated={r['call']:r for r in generated_rows};assert len(generated)==len(generated_rows);state=dict(initial);tentative=None;pair=False;failure=None;newpaths=0;normal_order=[];success_calls=set();root_changes=0
  for call,event in enumerate(events,1):
   assert event['call']==call;net=event['net_id']
   if call==1:
    assert event['phase']=='ROOT_PROPOSAL' and net==2;others={n:c for n,c in initial.items() if n!=2};taboo=mask(outside,count(others),set(spec['original_root_forbidden_nodes'])|set(spec['chosen_root_avoid_nodes']))
   elif call==2:
    assert event['phase']=='TARGET_PROPOSAL' and net==target and tentative is not None and not pair;taboo=mask(outside,count(tentative))
   else:
    assert pair and event['phase']=='COMPLETE_PACKAGE' and net==normal_order[call-3] and net not in state;taboo=mask(outside,count(state))
   template={r['connection_id']:r for r in bank[net][0]['records']};assert event['forbidden_nodes']==len(taboo) and event['connections']==len(template)
   if event['status'] in ('FAILED','FAILED_ROOT_STAGE_ABORTED'):
    assert call==len(events) and call not in generated;failure=failure_check(event,template,taboo);assert result['failure']=={k:v for k,v in event.items() if k!='status'}
    if call==2:assert event['status']=='FAILED_ROOT_STAGE_ABORTED' and state==initial
    break
   assert call in generated and generated[call]['net_id']==net;success_calls.add(call);candidate=generated[call]['candidate'];newpaths+=audit_tree(net,candidate,taboo,bank)
   if call==1:
    assert event['status']=='ROOT_STAGED';tentative=dict(others);tentative[2]=candidate;answers=evaluations(clauses,tentative,outside);assert event['clause_evaluations']==answers and all(a['satisfied'] for a in answers);old_records={r['connection_id']:r for r in initial[2]['records']};root_changes=sum(r['answer']['physical_edge_ids']!=old_records[r['connection_id']]['answer']['physical_edge_ids'] for r in candidate['records']);assert root_changes>0
   elif call==2:
    assert event['status']=='ROOT_AND_TARGET_INSTALLED_PRIVATELY';tentative[target]=candidate;state=tentative;pair=True;normal_order=sorted(package-set(state));assert all(state[n]==initial[n] for n in initial if n!=2)
   else:assert event['status']=='SELECTED_CONDITIONALLY';state[net]=candidate
   current=tentative if call==1 else state;usage=count(current);assert all(outside[n]+usage[n]<=caps[n] for n in usage) and all(a['satisfied'] for a in evaluations(clauses,current,outside))
  assert set(generated)==success_calls;assert result['search_calls']==len(events) and result['pair_installed_privately']==pair and result['final_selected_NETs']==sorted(state) and not result['committed'];final_rows=list(map(json.loads,(out/'final_conditional_trees.jsonl').read_text().splitlines()));final={r['net_id']:r['candidate'] for r in final_rows};assert len(final)==len(final_rows) and final==state;assert result['final_clause_evaluations']==evaluations(clauses,state,outside)
  if not pair:assert state==initial
  if failure:assert result['status']=='PACKAGE_REPLACEMENT_FAILED_NO_COMMIT'
  else:assert result['status']=='CONDITIONAL_PACKAGE_COMPLETE_PENDING_AUDIT' and set(state)==package
  row=dict(case=case,package_NETs=len(package),initial_selected_NETs=len(initial),final_selected_NETs=len(state),chosen_root_avoid_nodes=spec['chosen_root_avoid_nodes'],changed_root_connection_paths=root_changes,root_proposal_generated=1 in generated,target_proposal_generated=2 in generated,pair_installed_privately=pair,all_other_old_NET_trees_unchanged=all(state[n]==initial[n] for n in initial if n!=2),all_admitted_clauses_hold_in_final_private_state=all(a['satisfied'] for a in evaluations(clauses,state,outside)),initial_connection_paths_reverified=initial_paths,new_connection_paths_verified=newpaths,search_calls=len(events),conditional_package_complete=failure is None,committed=False,failure=failure);rows.append(row)
  for p in (bp,pp,out/'generated_trees.jsonl',out/'final_conditional_trees.jsonl',out/'result.json'):bindings[str(p)]=sha(p)
  print('CLAUSE_ROOT_REPLACEMENT_INDEPENDENT_AUDIT',json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
 (D/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL3_CLAUSE_GUIDED_ROOT_AND_TARGET_TRANSACTIONS_XML_AND_FAILURES_VERIFIED',rows=rows,bindings=bindings,scope='Exact assumption admission, root literal choice, original budgets, paths, capacity ledger, unchanged old nonroot trees, learned clauses and atomic staged pair replay. Package failures are specific to this one root proposal and continuation. No original/native routing, forecast quality, utility or full-time success.'),indent=2)+'\n')
if __name__=='__main__':main()
