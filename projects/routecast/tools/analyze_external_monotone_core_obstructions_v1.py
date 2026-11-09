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
 audited=read(D/'independent_verification_v1.json');assert all(sha(p)==h for p,h in audited['bindings'].items())
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
 contexts={};plans=[];bindings={str(p):sha(p) for p in (D/'protocol.json',D/'verification.json',D/'independent_verification_v1.json',graph,Path(__file__).resolve())}
 for spec in protocol['cases']:
  case=spec['case'];bp=B/case/'candidate_bank.jsonl';out=D/case;fp=out/'final_conditional_trees.jsonl';rp=out/'result.json';result=read(rp);assert result['status']=='PROTECTED_CORE_OBSTRUCTION_NO_COMMIT';final={r['net_id']:r['candidate'] for r in map(json.loads,fp.read_text().splitlines())};core=set(result['final_protected_NETs']);net=result['failure']['net_id'];assert core<=set(final) and net not in final;bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};outside=Counter();package=set(spec['package_NETs'])
  for owner,options in bank.items():
   sets=[owned(c) for c in options];common=set.intersection(*sets)
   if owner not in package:outside.update(common)
  core_ownership={owner:owned(final[owner]) for owner in core};template={r['connection_id']:r for r in bank[net][0]['records']};plans.append(dict(case=case,failed_NET=net,full_protected_NETs=sorted(core)));contexts[case]=(outside,core_ownership,template)
  for p in (bp,fp,rp):bindings[str(p)]=sha(p)
 plan_path=D/'core_analysis_protocol_v1.json';assert not plan_path.exists();plan_path.write_text(json.dumps(dict(policy='Certificate minimization only, no generation, routing trials, label reads or budget changes. For each observed core failure, verify outside-only is not a budget obstruction. Start with all frozen protected trees, then once per owner ascending NET ID delete it iff at least one failed-NET connection still exceeds budget or is unreachable. Finally verify current core obstructs and every single-owner deletion removes all individual shortest-path budget obstructions. This is inclusion minimal for fixed trees, not minimum cardinality or general infeasibility.',cases=plans,bindings=bindings),indent=2)+'\n');bindings[str(plan_path)]=sha(plan_path);rows=[]
 for plan in plans:
  case=plan['case'];outside,core_ownership,template=contexts[case];source=next(iter(template.values()))['source'];targets={r['sink'] for r in template.values()};queries={}
  def query(owners):
   key=tuple(sorted(owners))
   if key not in queries:
    counts=Counter(n for owner in key for n in core_ownership[owner]);taboo=mask(outside,counts);answers=shortest(source,targets,taboo);bad=sorted(cid for cid,r in template.items() if r['sink'] not in answers or answers[r['sink']]>r['budget_integer']);queries[key]=dict(protected_NETs=list(key),forbidden_nodes=len(taboo),failed_CIDs=bad,details=[dict(connection_id=cid,shortest_delay=answers.get(template[cid]['sink']),budget=template[cid]['budget_integer']) for cid in bad])
   return queries[key]
  assert not query(set())['failed_CIDs'];remaining=set(plan['full_protected_NETs']);assert query(remaining)['failed_CIDs'];deletions=[]
  for owner in plan['full_protected_NETs']:
   trial=remaining-{owner};still_blocked=bool(query(trial)['failed_CIDs']);deletions.append(dict(removed_NET=owner,deleted=still_blocked,trial_protected_NETs=sorted(trial)))
   if still_blocked:remaining=trial
  assert remaining and query(remaining)['failed_CIDs']
  for owner in remaining:assert not query(remaining-{owner})['failed_CIDs']
  row=dict(case=case,failed_NET=plan['failed_NET'],original_core_size=len(plan['full_protected_NETs']),inclusion_minimal_protected_NETs=sorted(remaining),minimal_core_obstruction=query(remaining),outside_only_has_no_shortest_path_budget_obstruction=True,every_single_deletion_removes_all_shortest_path_budget_obstructions=True,unique_exact_heap_queries=len(queries));rows.append(row);p=D/case/'core_analysis_v1.json';assert not p.exists();p.write_text(json.dumps(dict(result=row,deletion_trace=deletions,all_queries=list(queries.values())),indent=2)+'\n');bindings[str(p)]=sha(p);print('MONOTONE_MINIMAL_FROZEN_CORE',json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
 (D/'core_obstruction_analysis_v1.json').write_text(json.dumps(dict(status='ALL3_FIXED_TREE_CORE_BUDGET_OBSTRUCTIONS_INCLUSION_MINIMIZED',rows=rows,bindings=bindings,scope='Inclusion minimal at NET/tree granularity for these exact frozen paths and outside mandatory owners. Independent original XML shortest-path checks, not minimum cardinality, graph-wide budget impossibility, or route ranking failure. A passing shortest-path mask is not a completed outside routing.'),indent=2)+'\n')
if __name__=='__main__':main()
