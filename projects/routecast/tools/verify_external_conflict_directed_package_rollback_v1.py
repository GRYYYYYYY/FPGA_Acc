"""Independent XML tree, transaction replay and exact failure shortest-path audit."""
import json,heapq,xml.etree.ElementTree as ET
from array import array
from fractions import Fraction
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'prospective_external_family_blocker_release_v1_2026-10-19';H=E/'prospective_external_family_budget_aware_joint_package_v1_2026-10-19';D=E/'prospective_external_family_conflict_directed_package_rollback_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 protocol=read(D/'protocol.json');summary=read(D/'verification.json');priorproof=read(H/'independent_verification_v1.json');assert summary['status']=='ALL3_FIXED_CONFLICT_DIRECTED_ROLLBACK_SEARCHES_TERMINAL'
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
 rows=[];bindings={str(p):sha(p) for p in (D/'protocol.json',D/'verification.json',H/'independent_verification_v1.json',H/'protocol.json',H/'failure_ablation_v1.json',graph,Path(__file__).resolve())}
 for spec in protocol['cases']:
  case=spec['case'];prior=prior_specs[case];bp=B/case/'candidate_bank.jsonl';pp=H/case/'selected_trees.jsonl';rp=H/case/'result.json';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};initial_rows=list(map(json.loads,pp.read_text().splitlines()));initial={r['net_id']:r['candidate'] for r in initial_rows};package=set(prior['package_NETs']);target=read(rp)['failure']['net_id'];pinned={prior['reserved_witness_NET']}
  if not ablations[case]['failure']['fixed_pair_order_independent_obstruction']:pinned.add(2)
  assert spec['package_NETs']==sorted(package) and spec['initial_selected_NETs']==sorted(initial) and spec['challenger_NET']==target and spec['pinned_NETs']==sorted(pinned);assert spec['root_extra_forbidden_nodes']==prior['root_extra_forbidden_nodes'];outside=Counter()
  for net,options in bank.items():
   sets=[owned(c) for c in options];common=set.intersection(*sets);assert all(all(n in ns for ns in sets) for n in {n for ns in sets for n in ns if caps[n]>1})
   if net not in package:outside.update(common)
  assert all(n<=caps[node] for node,n in outside.items());state={};initial_paths=0
  for row in initial_rows:
   net=row['net_id'];initial_paths+=audit_tree(net,row['candidate'],mask(outside,count(state),spec['root_extra_forbidden_nodes'] if net==2 else ()),bank);state[net]=row['candidate'];initial_usage=count(state);assert all(outside[n]+initial_usage[n]<=caps[n] for n in initial_usage)
  out=D/case;result=read(out/'result.json');generated_rows=list(map(json.loads,(out/'generated_trees.jsonl').read_text().splitlines()));generated={r['step']:r for r in generated_rows};assert len(generated)==len(generated_rows);events=result['events'];assert events and events[0]['phase']=='CHALLENGER' and events[0]['net_id']==target;rollback=[];schedule=[];new_paths=0;failure=None
  for step,event in enumerate(events):
   assert event['step']==step
   if step==0:net=target;taboo=mask(outside,count({n:state[n] for n in pinned}));assert event['phase']=='CHALLENGER'
   else:
    phase,net=schedule[step-1];assert event['phase']==phase and event['net_id']==net and net not in state;taboo=mask(outside,count(state),spec['root_extra_forbidden_nodes'] if net==2 else ())
   template={r['connection_id']:r for r in bank[net][0]['records']};assert event['forbidden_nodes']==len(taboo) and event['connections']==len(template)
   if event['status']=='FAILED':
    assert step==len(events)-1 and step not in generated;source=next(iter(template.values()))['source'];answers=shortest(source,{r['sink'] for r in template.values()},taboo);bad=sorted(cid for cid,r in template.items() if r['sink'] not in answers or answers[r['sink']]>r['budget_integer']);assert bad==event['failed_CIDs']
    for detail in event.get('failed_details',[]):assert detail['settled']==(detail['sink'] in answers) and detail['shortest_delay']==answers.get(detail['sink']) and detail['budget']==template[detail['connection_id']]['budget_integer']
    assert result['failure']=={k:v for k,v in event.items() if k!='status'};failure=dict(net_id=net,phase=event['phase'],failed_CIDs=bad,unreachable=sum(template[cid]['sink'] not in answers for cid in bad),independent_XML_shortest_path_match=True);break
   assert step in generated and generated[step]['net_id']==net;candidate=generated[step]['candidate'];new_paths+=audit_tree(net,candidate,taboo,bank)
   if step==0:
    ns=owned(candidate);usage=count(state);blocked={n for n in ns if outside[n]+usage[n]+1>caps[n]};rollback=sorted(n for n,c in state.items() if n not in pinned and owned(c)&blocked);assert rollback and rollback==event['rollback_NETs'] and event['status']=='CHALLENGER_INSTALLED_WITH_ROLLBACK'
    for n in rollback:del state[n]
    usage=count(state);assert all(outside[n]+usage[n]+1<=caps[n] for n in ns);state[net]=candidate;schedule=[('REROUTE_PREDECESSOR',n) for n in rollback]+[('COMPLETE_PACKAGE',n) for n in sorted(package-set(state)-set(rollback))]
   else:assert event['status']=='SELECTED_CONDITIONALLY';state[net]=candidate
   usage=count(state);assert all(outside[n]+usage[n]<=caps[n] for n in usage)
  assert set(generated)=={e['step'] for e in events if e['status']!='FAILED'};assert result['rollback_NETs']==rollback and result['selected_NETs']==sorted(state) and not result['committed'];final={r['net_id']:r['candidate'] for r in map(json.loads,(out/'final_conditional_trees.jsonl').read_text().splitlines())};assert final==state
  if failure:assert result['status']=='PACKAGE_REPAIR_FAILED_NO_COMMIT'
  else:assert result['status']=='PACKAGE_REPAIR_SUCCEEDED_PENDING_INDEPENDENT_AUDIT' and set(state)==package and len(events)==len(schedule)+1
  row=dict(case=case,package_NETs=len(package),pinned_NETs=sorted(pinned),rollback_NETs=rollback,root_rolled_back=2 in rollback,initial_NETs=len(initial),initial_connection_paths_verified=initial_paths,new_connection_paths_verified=new_paths,final_conditional_NETs=len(state),challenger_installed=target in state,package_accepted=failure is None,committed=False,failure=failure);rows.append(row)
  for p in (bp,pp,rp,out/'result.json',out/'generated_trees.jsonl',out/'final_conditional_trees.jsonl'):bindings[str(p)]=sha(p)
  print('CONFLICT_ROLLBACK_INDEPENDENT_AUDIT',json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
 (D/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL3_CONFLICT_DIRECTED_ROLLBACK_TRANSACTIONS_XML_PATHS_AND_FAILURES_VERIFIED',rows=rows,bindings=bindings,scope='Exact private-state rollback set, budgets and conditional capacity replay. Accepted package is only compatible with fixed outside mandatory owners. Rejected package is not general infeasibility. No bank, native route, quality or utility promotion.'),indent=2)+'\n')
if __name__=='__main__':main()
