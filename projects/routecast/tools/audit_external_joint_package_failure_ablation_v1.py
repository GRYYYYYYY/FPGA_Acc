"""Fixed causal mask ablation for actual atomic-package failures; no new generation."""
import json,heapq,xml.etree.ElementTree as ET
from array import array
from fractions import Fraction
from collections import Counter,defaultdict
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'prospective_external_family_blocker_release_v1_2026-10-19';G=E/'prospective_external_family_global_mask_probe_v2_2026-10-19';D=E/'prospective_external_family_joint_release_package_v2_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 protocol=read(D/'protocol.json');receipt=read(D/'verification.json');assert receipt['status']=='ALL3_FIXED_ATOMIC_JOINT_PACKAGE_SEARCHES_TERMINAL'
 prior=read(D/'independent_verification_v1.json');assert all(sha(p)==h for p,h in prior['bindings'].items())
 for proof in (protocol,receipt):assert all(sha(p)==h for p,h in proof['bindings'].items())
 matrix=E/'prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';inputs={r['case']:r for r in read(matrix)['rows']};graph=Path(read(inputs['w160/episode_01']['endpoint'])['inputs']['graph']['path']);caps=array('I');types=[];us=array('I');vs=array('I');switches=array('I');weights={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));types.append(e.get('type'));t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0
  elif e.tag=='switch' and parent=='switches':
   t=e.find('timing');assert all(Fraction(t.get(k,'0'))==0 for k in ('R','Cin','Cout','Cinternal'));w=Fraction(t.get('Tdel','0'))*10**18;assert w.denominator==1;weights[int(e.get('id'))]=w.numerator
  elif e.tag=='edge' and parent=='rr_edges':us.append(int(e.get('src_node')));vs.append(int(e.get('sink_node')));switches.append(int(e.get('switch_id')))
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
  stack.pop()
 offsets=array('I',[0])*(len(caps)+1)
 for u in us:offsets[u+1]+=1
 for i in range(len(caps)):offsets[i+1]+=offsets[i]
 cursor=array('I',offsets);edge_order=array('I',[0])*len(us)
 for eid,u in enumerate(us):edge_order[cursor[u]]=eid;cursor[u]+=1
 def owned(candidate):
  ns={r['source'] for r in candidate['records']}
  for r in candidate['records']:ns.update(vs[eid] for eid in r['answer']['physical_edge_ids'])
  return ns
 def shortest(source,targets,taboo):
  if source in taboo:return {}
  dist={source:0};settled={};queue=[(0,source)];pending=set(targets)
  while queue and pending:
   value,u=heapq.heappop(queue)
   if u in settled or dist[u]!=value:continue
   settled[u]=value;pending.discard(u)
   if types[u]=='SINK':continue
   for pos in range(offsets[u],offsets[u+1]):
    eid=edge_order[pos];v=vs[eid]
    if v in taboo or types[v]=='SOURCE':continue
    candidate=value+weights[switches[eid]]
    if candidate<dist.get(v,10**100):dist[v]=candidate;heapq.heappush(queue,(candidate,v))
  return {sink:settled[sink] for sink in targets if sink in settled}
 bindings={str(p):sha(p) for p in (D/'protocol.json',D/'verification.json',D/'independent_verification_v1.json',graph,Path(__file__).resolve())};rows=[]
 for spec in protocol['cases']:
  case=spec['case'];bp=B/case/'candidate_bank.jsonl';gp=G/case/'candidate_bank.jsonl';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};extended={r['net_id']:r['candidates'] for r in map(json.loads,gp.read_text().splitlines())};required=defaultdict(set);invariant={}
  for net,options in bank.items():
   sets=[owned(c) for c in options];common=set.intersection(*sets);invariant[net]=common
   for node in {n for ns in sets for n in ns if caps[n]>1}:assert all(node in ns for ns in sets)
   for node in common:required[node].add(net)
  root=extended[2][-1];assert extended[2][:-1]==bank[2];blockers=defaultdict(set)
  for node in owned(root):
   if caps[node]==1:
    for net in required[node]-{2}:blockers[net].add(node)
  package={2}|set(blockers);assert sorted(package)==spec['package_NETs'] and spec['replacement_order']==sorted(package-{2});assert {int(n):ns for n,ns in spec['root_blocking_resources'].items()}=={n:sorted(ns) for n,ns in blockers.items()};outside=Counter(node for net,ns in invariant.items() if net not in package for node in ns);assert all(count<=caps[node] for node,count in outside.items())
  directory=D/case;result=read(directory/'result.json');trees=list(map(json.loads,(directory/'selected_trees.jsonl').read_text().splitlines()));assert trees and trees[0]==dict(net_id=2,candidate=root);selected=[r['net_id'] for r in trees];assert selected==[2]+spec['replacement_order'][:len(trees)-1] and sorted(selected)==result['selected_NETs'];usage=Counter();paths=0
  for index,row in enumerate(trees):
   net=row['net_id'];template={r['connection_id']:r for r in bank[net][0]['records']};candidate=row['candidate'];records={r['connection_id']:r for r in candidate['records']};assert len(records)==len(candidate['records']) and set(records)==set(template);taboo={n for n,cap in enumerate(caps) if outside[n]+usage[n]>=cap};parents={}
   for cid,r in records.items():
    old=template[cid]
    for k,v in old.items():
     if k!='answer':assert r[k]==v
    u=r['source'];assert u not in taboo and types[u]=='SOURCE';seen={u};delay=0
    for pos,eid in enumerate(r['answer']['physical_edge_ids']):
     assert type(eid) is int and 0<=eid<len(us) and us[eid]==u;v=vs[eid];assert v not in seen and v not in taboo and caps[v]>0
     if pos<len(r['answer']['physical_edge_ids'])-1:assert types[v] not in ('SOURCE','SINK')
     if types[v]!='SINK':assert v not in parents or parents[v]==(u,eid);parents[v]=(u,eid)
     seen.add(v);delay+=weights[switches[eid]];u=v
    assert u==r['sink'] and types[u]=='SINK' and delay==r['answer']['delay']<=r['budget_integer'];paths+=1
   usage.update(owned(candidate));assert all(usage[n]+outside[n]<=caps[n] for n in usage)
   if index:assert result['events'][index-1]['net_id']==net and result['events'][index-1]['status']=='SELECTED_CONDITIONALLY'
  failed=result['failure'];failure_audit=None
  if failed:
   assert result['status']=='PACKAGE_SEARCH_FAILED_NO_COMMIT' and not result['committed'];step=len(trees)-1;assert failed['step']==step and failed['net_id']==spec['replacement_order'][step] and len(result['events'])==step+1;net=failed['net_id'];template={r['connection_id']:r for r in bank[net][0]['records']};source=next(iter(template.values()))['source'];taboo={n for n,cap in enumerate(caps) if outside[n]+usage[n]>=cap};assert len(taboo)==failed['forbidden_nodes']
   values=shortest(source,{r['sink'] for r in template.values()},taboo);bad=sorted(cid for cid,r in template.items() if r['sink'] not in values or values[r['sink']]>r['budget_integer']);assert bad==failed['failed_CIDs']
   for detail in failed.get('failed_details',[]):
    assert detail['settled']==(detail['sink'] in values);assert detail['shortest_delay']==values.get(detail['sink']);assert detail['budget']==template[detail['connection_id']]['budget_integer']
   root_owned=owned(root);variants={}
   for name,mask in [('outside_only',{n for n,cap in enumerate(caps) if outside[n]>=cap}),('outside_plus_fixed_root',{n for n,cap in enumerate(caps) if outside[n]+int(n in root_owned)>=cap}),('outside_plus_full_selected_prefix',taboo)]:
    answers=values if name=='outside_plus_full_selected_prefix' else shortest(source,{r['sink'] for r in template.values()},mask)
    bad_cids=sorted(cid for cid,r in template.items() if r['sink'] not in answers or answers[r['sink']]>r['budget_integer'])
    variants[name]=dict(forbidden_nodes=len(mask),failed_CIDs=bad_cids,unreachable_CIDs=[cid for cid in bad_cids if template[cid]['sink'] not in answers],budget_exceeded_CIDs=[cid for cid in bad_cids if template[cid]['sink'] in answers],details=[dict(connection_id=cid,shortest_delay=answers.get(template[cid]['sink']),budget=template[cid]['budget_integer']) for cid in bad_cids])
   assert variants['outside_plus_full_selected_prefix']['failed_CIDs']==bad
   failure_audit=dict(net_id=net,masks=variants,outside_alone_obstruction=bool(variants['outside_only']['failed_CIDs']),fixed_root_order_independent_obstruction=bool(variants['outside_plus_fixed_root']['failed_CIDs']),independent_original_XML_heap_shortest_paths_match=True)
  else:assert set(selected)==package and result['status']=='PACKAGE_SEARCH_SUCCEEDED_PENDING_INDEPENDENT_AUDIT'
  row=dict(case=case,package_NETs=len(package),selected_NETs_verified=len(trees),connection_paths_verified=paths,all_conditional_capacities_and_budgets_pass=True,package_accepted=False if failed else True,failure=failure_audit);rows.append(row)
  for p in (bp,gp,directory/'result.json',directory/'selected_trees.jsonl'):bindings[str(p)]=sha(p)
  print('JOINT_PACKAGE_INDEPENDENT_AUDIT',json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
 (D/'failure_ablation_v1.json').write_text(json.dumps(dict(status='ALL3_ACTUAL_JOINT_PACKAGE_FAILURE_MASK_ABLATIONS_XML_VERIFIED',rows=rows,bindings=bindings,scope='Success only covers package and fixed outside mandatory owners, not outside optional route completion. Failure confirms this fixed root, package, greedy order and outside mask; not general joint feasibility, route ranking, timing or native legality. No partial package committed.'),indent=2)+'\n')
if __name__=='__main__':main()
