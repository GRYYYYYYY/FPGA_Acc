"""Independent XML tree, transaction replay and exact failure shortest-path audit."""
import json,heapq,sys,xml.etree.ElementTree as ET
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
 J=E/'prospective_external_family_clause_guided_root_replacement_v1_2026-10-19';C=E/'prospective_external_family_budget_resource_cuts_v1_2026-10-19';O=E/'prospective_external_family_budget_cut_demand_collision_v1_2026-10-19';O.mkdir(exist_ok=False)
 for p in (J/'independent_verification_v1.json',C/'independent_verification_v1.json'):
  receipt=read(p);assert all(sha(q)==h for q,h in receipt['bindings'].items())
 clauses=read(C/'learned_conditional_budget_constraints_v1.json')['clauses'];packages={r['case']:set(r['package_NETs']) for r in read(J/'protocol.json')['cases']};bindings={str(p):sha(p) for p in (J/'independent_verification_v1.json',J/'protocol.json',C/'independent_verification_v1.json',C/'learned_conditional_budget_constraints_v1.json',graph,Path(__file__).resolve())};contexts={};plans=[];groups=[]
 reverse_offsets=array('I',[0])*(len(caps)+1)
 for v in vs:reverse_offsets[v+1]+=1
 for i in range(len(caps)):reverse_offsets[i+1]+=reverse_offsets[i]
 cursor=array('I',reverse_offsets);reverse_edges=array('I',[0])*len(us)
 for eid,v in enumerate(vs):reverse_edges[cursor[v]]=eid;cursor[v]+=1
 for clause in clauses:
  case=clause['case'];bp=B/case/'candidate_bank.jsonl';fp=J/case/'final_conditional_trees.jsonl';rp=J/case/'result.json';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};state={r['net_id']:r['candidate'] for r in map(json.loads,fp.read_text().splitlines())};observed=read(rp)['failure'];assert observed['phase']=='COMPLETE_PACKAGE';outside=Counter()
  for net,options in bank.items():
   sets=[owned(c) for c in options];common=set.intersection(*sets)
   if net not in packages[case]:outside.update(common)
  import hashlib
  stamp=hashlib.sha256(json.dumps(sorted((n,c) for n,c in outside.items() if c),separators=(',',':')).encode()).hexdigest();assert stamp==clause['outside_unique_NET_occupancy_sha256'];cut=clause['conditional_budget_cut'];assert all(caps[n]==1 and outside[n]==0 for n in cut);owners=sorted(net for net,c in state.items() if owned(c)&set(cut));tests={(observed['net_id'],min(observed['failed_CIDs'])):'NEXT_FAILURE'}
  for net in owners:
   if net==clause['NET']:continue
   for q in bank[net][0]['records']:tests.setdefault((net,q['connection_id']),'CURRENT_CUT_OWNER')
  group=dict(case=case,cut=cut,available_unit_capacity=sum(caps[n]-outside[n] for n in cut),known_NET=clause['NET'],known_CID=clause['connection_id'],known_certificate_query=clause['negative_certificate_query'],outside_occupancy_sha256=stamp,current_cut_owner_NETs=owners);groups.append(group)
  for (net,cid),why in sorted(tests.items()):
   assert net in packages[case];q=next(r for r in bank[net][0]['records'] if r['connection_id']==cid);key=f'{case}/cid_{cid}';structure={n for n,t in enumerate(types) if caps[n]==0 or (t=='SOURCE' and n!=q['source']) or (t=='SINK' and n!=q['sink'])};plan=dict(case=case,key=key,net_id=net,connection_id=cid,source=q['source'],sink=q['sink'],budget=q['budget_integer'],cut=cut,reason=why);plans.append(plan);contexts[key]=(outside,structure,q)
  for p in (bp,fp,rp):bindings[str(p)]=sha(p)
 policy='Proof-only demand/capacity check, no new routing trial. Per fixed case reuse its certified conditional cut and outside occupancy. Test lowest next failed CID and every CID of every current selected cut-owner NET except the already certified known NET. For each CID prove baseline outside path, each singleton cut removal, and full cut removal, with physical witnesses or capped Bellman potentials. For each distinct NET with any negative full-cut query take its lowest such CID as a demand witness. Add the existing certified NET witness. If distinct required NETs exceed sum of remaining cut capacities, this fixed-outside budget package is impossible regardless of protected-tree choices. Preserve nonviolating cases as inconclusive, no threshold/model sweep.'
 (O/'protocol.json').write_text(json.dumps(dict(policy=policy,cases=groups,queries=plans,bindings=bindings,unavailable_cases_preserved=6),indent=2)+'\n');bindings[str(O/'protocol.json')]=sha(O/'protocol.json');rows=[];total=0
 for plan in plans:
  outside,structure,q=contexts[plan['key']];source,sink,budget=q['source'],q['sink'],q['budget_integer'];assert 0<=budget<2**64-1;out=O/plan['key'];out.mkdir(parents=True);cache={};queries=[]
  def ask(mode,extra):
   nonlocal total
   key=(mode,tuple(sorted(extra)))
   if key in cache:return cache[key]
   taboo=(mask(outside,Counter()) if mode=='outside' else {n for n,c in enumerate(caps) if not c})|structure|set(extra);qid=len(queries);record=dict(query_id=qid,mode=mode,extra_forbidden_nodes=list(key[1]),forbidden_nodes=len(taboo),source=source,sink=sink,budget=budget);parent={};dist={source:0};settled=set();queue=[(0,source)];found=None
   if source not in taboo and sink not in taboo:
    while queue:
     value,u=heapq.heappop(queue)
     if u in settled or value!=dist[u]:continue
     settled.add(u)
     if u==sink:found=value;break
     for pos in range(offsets[u],offsets[u+1]):
      eid=edge_order[pos];v=vs[eid]
      if v in taboo:continue
      value2=value+weights[switches[eid]]
      if value2<=budget and value2<dist.get(v,10**100):dist[v]=value2;parent[v]=(u,eid);heapq.heappush(queue,(value2,v))
   if found is not None:
    edges=[];u=sink;seen=set()
    while u!=source:assert u not in seen;seen.add(u);u,eid=parent[u];edges.append(eid)
    edges.reverse();record.update(status='BUDGET_PATH',physical_edge_ids=edges,witness_delay=found)
   elif source in taboo or sink in taboo:record.update(status='NO_BUDGET_PATH',proof_kind='FORBIDDEN_ENDPOINT')
   else:
    cap=budget+1;potential=array('Q',[cap])*len(caps);assert potential.itemsize==8;potential[sink]=0;queue=[(0,sink)]
    while queue:
     value,v=heapq.heappop(queue)
     if value!=potential[v]:continue
     for pos in range(reverse_offsets[v],reverse_offsets[v+1]):
      eid=reverse_edges[pos];u=us[eid]
      if u in taboo:continue
      value2=value+weights[switches[eid]]
      if value2<potential[u]:potential[u]=value2;heapq.heappush(queue,(value2,u))
    assert potential[source]==cap and potential[sink]==0;p=out/f'query_{qid:04d}.potential_u64.bin'
    with p.open('wb') as f:potential.tofile(f)
    record.update(status='NO_BUDGET_PATH',proof_kind='CAPPED_BELLMAN_LOWER_BOUND',potential_file=str(p),potential_sha256=sha(p),byteorder=sys.byteorder,itemsize=8,cap=cap);bindings[str(p)]=sha(p)
   path=out/f'query_{qid:04d}.json';path.write_text(json.dumps(record,indent=2)+'\n');bindings[str(path)]=sha(path);queries.append(record);cache[key]=record;total+=1;return record
  baseline=ask('outside',set());assert baseline['status']=='BUDGET_PATH';singletons=[dict(node=n,query_id=ask('outside',{n})['query_id'],unavoidable=ask('outside',{n})['status']=='NO_BUDGET_PATH') for n in plan['cut']];whole=ask('outside',plan['cut']);row=dict(case=plan['case'],key=plan['key'],NET=plan['net_id'],CID=plan['connection_id'],baseline_query_id=baseline['query_id'],singleton_tests=singletons,full_cut_query_id=whole['query_id'],budget_requires_cut=whole['status']=='NO_BUDGET_PATH',queries=len(queries));p=out/'result.json';p.write_text(json.dumps(dict(result=row,queries=[dict(query_id=r['query_id'],path=str(out/f"query_{r['query_id']:04d}.json")) for r in queries]),indent=2)+'\n');bindings[str(p)]=sha(p);rows.append(row);print('CUT_DEMAND_QUERY',row,flush=True)
 collisions=[]
 for group in groups:
  witnesses={group['known_NET']:dict(NET=group['known_NET'],CID=group['known_CID'],certificate_query=group['known_certificate_query'],source='EXISTING_VERIFIED_CUT')}
  for row in sorted((r for r in rows if r['case']==group['case'] and r['budget_requires_cut']),key=lambda r:(r['NET'],r['CID'])):witnesses.setdefault(row['NET'],dict(NET=row['NET'],CID=row['CID'],certificate_query=str(O/row['key']/f"query_{row['full_cut_query_id']:04d}.json"),source='NEW_FULL_CUT_CERTIFICATE'))
  collision=dict(case=group['case'],cut=group['cut'],available_unit_capacity=group['available_unit_capacity'],required_distinct_NETs=len(witnesses),witnesses=[witnesses[n] for n in sorted(witnesses)],fixed_outside_budget_capacity_contradiction=len(witnesses)>group['available_unit_capacity']);collisions.append(collision);print('CUT_DEMAND_CAPACITY_RESULT',collision,flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
 (O/'verification.json').write_text(json.dumps(dict(status='CUT_DEMAND_CAPACITY_CERTIFICATES_PREPARED_PENDING_INDEPENDENT_REPLAY',rows=rows,collisions=collisions,queries=total,bindings=bindings,labels_opened=False,budgets_changed=False,scope='If verified, a violated cut demand bound refutes the entire budget-constrained package with these fixed outside owners, not only one set of root trees. Does not refute general routing, relaxed outside owners, timing models or congestion ranking.'),indent=2)+'\n')
if __name__=='__main__':main()
