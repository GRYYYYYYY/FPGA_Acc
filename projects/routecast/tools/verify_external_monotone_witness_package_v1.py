"""Independent XML tree, transaction replay and exact failure shortest-path audit."""
import json,heapq,xml.etree.ElementTree as ET
from array import array
from fractions import Fraction
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'prospective_external_family_blocker_release_v1_2026-10-19';H=E/'prospective_external_family_conflict_directed_package_rollback_v1_2026-10-19';D=E/'prospective_external_family_monotone_witness_package_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 protocol=read(D/'protocol.json');summary=read(D/'verification.json');priorproof=read(H/'independent_verification_v1.json');assert summary['status']=='ALL3_MONOTONE_WITNESS_PACKAGE_SEARCHES_TERMINAL'
 for proof in (protocol,summary,priorproof):assert all(sha(p)==h for p,h in proof['bindings'].items())
 prior_specs={r['case']:r for r in read(H/'protocol.json')['cases']};ablations={r['case']:r for r in read(H/'failure_ablation_v1.json')['rows']};matrix=E/'prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';inputs={r['case']:r for r in read(matrix)['rows']};graph=Path(read(inputs['w160/episode_01']['endpoint'])['inputs']['graph']['path']);caps=array('I');types=[];us=array('I');vs=array('I');switches=array('I');weights={};stack=[]
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
 def potential(package,state,protected):
  assert protected<=set(state)<=package
  return (len(package)-len(protected))*(len(package)+1)+len(package)-len(state)
 def ledger(ownership):return Counter(n for ns in ownership.values() for n in ns)
 def audit_failure(event,template,taboo):
  source=next(iter(template.values()))['source'];answers=shortest(source,{r['sink'] for r in template.values()},taboo);bad=sorted(cid for cid,r in template.items() if r['sink'] not in answers or answers[r['sink']]>r['budget_integer']);assert bad and bad==event['failed_CIDs']
  for detail in event.get('failed_details',[]):assert detail['settled']==(detail['sink'] in answers) and detail['shortest_delay']==answers.get(detail['sink']) and detail['budget']==template[detail['connection_id']]['budget_integer']
  return dict(net_id=event['net_id'],failed_CIDs=bad,details=[dict(connection_id=cid,shortest_delay=answers.get(template[cid]['sink']),budget=template[cid]['budget_integer']) for cid in bad],unreachable=sum(template[cid]['sink'] not in answers for cid in bad),independent_original_XML_shortest_paths_match=True)
 rows=[];bindings={str(p):sha(p) for p in (D/'protocol.json',D/'verification.json',H/'independent_verification_v1.json',H/'protocol.json',H/'failure_ablation_v1.json',graph,Path(__file__).resolve())}
 for spec in protocol['cases']:
  case=spec['case'];prior=prior_specs[case];bp=B/case/'candidate_bank.jsonl';pp=H/case/'final_conditional_trees.jsonl';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};initial_rows=list(map(json.loads,pp.read_text().splitlines()));package=set(prior['package_NETs']);initial_protected=set(ablations[case]['failure']['core_NETs']);assert spec['package_NETs']==sorted(package) and spec['initial_protected_NETs']==sorted(initial_protected) and 2 in initial_protected and spec['root_extra_forbidden_nodes']==prior['root_extra_forbidden_nodes'];outside=Counter()
  for net,options in bank.items():
   sets=[owned(c) for c in options];common=set.intersection(*sets);assert all(all(n in ns for ns in sets) for n in {n for ns in sets for n in ns if caps[n]>1})
   if net not in package:outside.update(common)
  assert all(count<=caps[n] for n,count in outside.items());state={};ownership={};initial_paths=0;usage=Counter()
  for row in initial_rows:
   net=row['net_id'];assert net not in state;initial_paths+=audit_tree(net,row['candidate'],mask(outside,usage,spec['root_extra_forbidden_nodes'] if net==2 else ()),bank);state[net]=row['candidate'];ownership[net]=owned(row['candidate']);usage.update(ownership[net]);assert all(outside[n]+usage[n]<=caps[n] for n in usage)
  assert spec['initial_selected_NETs']==sorted(state);protected=set(initial_protected);frozen={n:state[n] for n in protected};initial_rank=potential(package,state,protected);assert initial_rank==spec['initial_rank'] and spec['max_distinct_repairs']==len(package)-len(protected) and spec['structural_search_call_bound']==2*(initial_rank+1)
  out=D/case;result=read(out/'result.json');events=list(map(json.loads,(out/'events.jsonl').read_text().splitlines()));generated_rows=list(map(json.loads,(out/'generated_trees.jsonl').read_text().splitlines()));generated={r['call']:r for r in generated_rows};assert len(generated)==len(generated_rows);iterations=repairs=normals=0;pending=None;failure=None;newpaths=0;transitions=[];normal_failures=0
  for call,event in enumerate(events,1):
   assert event['call']==call;before=potential(package,state,protected);assert event['rank_before']==before and event['selected_before']==len(state) and event['protected_before']==len(protected);net=event['net_id'];template={r['connection_id']:r for r in bank[net][0]['records']};extra=spec['root_extra_forbidden_nodes'] if net==2 else ()
   if event['mode']=='ALL_SELECTED':
    assert pending is None and net==min(package-set(state));iterations+=1;assert event['iteration']==iterations;taboo=mask(outside,usage,extra)
   else:
    assert event['mode']=='PROTECTED_CORE' and pending==(net,iterations) and event['iteration']==iterations;taboo=mask(outside,Counter(n for owner in protected for n in ownership[owner]),extra)
   assert event['forbidden_nodes']==len(taboo) and event['connections']==len(template)
   if event['status'] in ('NEEDS_PROTECTED_CORE_SEARCH','PROTECTED_CORE_OBSTRUCTION'):
    assert call not in generated and event['rank_after']==before;observed=audit_failure(event,template,taboo)
    if event['status']=='NEEDS_PROTECTED_CORE_SEARCH':assert event['mode']=='ALL_SELECTED';pending=(net,iterations);normal_failures+=1;continue
    assert event['mode']=='PROTECTED_CORE' and call==len(events);assert result['failure']=={k:v for k,v in event.items() if k not in ('status','rank_after')};failure=observed;pending=None;break
   assert call in generated and generated[call]['net_id']==net;candidate=generated[call]['candidate'];newpaths+=audit_tree(net,candidate,taboo,bank);ns=owned(candidate);assert net not in state
   if event['status']=='INSERTED':
    assert event['mode']=='ALL_SELECTED' and pending is None;state[net]=candidate;ownership[net]=ns;usage.update(ns);normals+=1;after=potential(package,state,protected);assert after==before-1
   else:
    assert event['status']=='REPAIRED_AND_PROTECTED' and event['mode']=='PROTECTED_CORE' and pending==(net,iterations);blocked={n for n in ns if outside[n]+usage[n]+1>caps[n]};removed=sorted(owner for owner,nodeset in ownership.items() if owner not in protected and nodeset&blocked);assert removed and removed==event['rollback_NETs'] and not set(removed)&protected
    for owner in removed:del state[owner];del ownership[owner]
    remaining=ledger(ownership);assert all(outside[n]+remaining[n]+1<=caps[n] for n in ns);state[net]=candidate;ownership[net]=ns;protected.add(net);frozen[net]=candidate;usage=ledger(ownership);repairs+=1;after=potential(package,state,protected);assert after==before+len(removed)-len(package)-2<before;pending=None;transitions.append(dict(call=call,protected_NET=net,rollback_NETs=removed,rank_before=before,rank_after=after))
   assert event['rank_after']==after;assert all(state[n]==candidate for n,candidate in frozen.items());assert all(outside[n]+usage[n]<=caps[n] for n in usage)
  assert pending is None;assert set(generated)=={e['call'] for e in events if e['status'] in ('INSERTED','REPAIRED_AND_PROTECTED')};final_rows=list(map(json.loads,(out/'final_conditional_trees.jsonl').read_text().splitlines()));final={r['net_id']:r['candidate'] for r in final_rows};assert len(final)==len(final_rows) and final==state;assert result['final_selected_NETs']==sorted(state) and result['initial_protected_NETs']==sorted(initial_protected) and result['final_protected_NETs']==sorted(protected);assert result['iterations']==iterations and result['search_calls']==len(events) and result['repairs']==repairs and result['normal_insertions']==normals;assert result['initial_rank']==initial_rank and result['final_rank']==potential(package,state,protected);assert len(events)<=spec['structural_search_call_bound'] and repairs<=spec['max_distinct_repairs'];assert not result['committed']
  if failure:assert result['status']=='PROTECTED_CORE_OBSTRUCTION_NO_COMMIT'
  else:assert set(state)==package and result['status']=='CONDITIONAL_PACKAGE_COMPLETE_PENDING_AUDIT'
  row=dict(case=case,package_NETs=len(package),initial_selected_NETs=len(initial_rows),final_selected_NETs=len(state),initial_protected_NETs=sorted(initial_protected),final_protected_NETs=sorted(protected),search_calls=len(events),normal_failures=normal_failures,repairs=repairs,normal_insertions=normals,initial_rank=initial_rank,final_rank=potential(package,state,protected),all_progress_and_immutable_protected_tree_invariants_pass=True,initial_connection_paths_reverified=initial_paths,new_connection_paths_verified=newpaths,repair_transitions=transitions,conditional_package_complete=failure is None,committed=False,failure=failure);rows.append(row)
  for p in (bp,pp,out/'events.jsonl',out/'generated_trees.jsonl',out/'result.json',out/'final_conditional_trees.jsonl'):bindings[str(p)]=sha(p)
  print('MONOTONE_PACKAGE_INDEPENDENT_AUDIT',json.dumps({k:v for k,v in row.items() if k!='repair_transitions'}),flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
 (D/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL3_MONOTONE_PACKAGE_XML_TRANSACTIONS_PROGRESS_BOUNDS_AND_CORE_FAILURES_VERIFIED',rows=rows,bindings=bindings,scope='Algebraic progress proof plus exact observed transaction replay, original XML paths and independent heap failure checks. Fixed-core obstruction does not imply full graph, other core choices or ranking infeasibility. No native or full runtime gain.'),indent=2)+'\n')
if __name__=='__main__':main()
