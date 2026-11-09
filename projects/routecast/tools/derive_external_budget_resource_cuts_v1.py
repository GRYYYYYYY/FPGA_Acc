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
 O=E/'prospective_external_family_budget_resource_cuts_v1_2026-10-19';O.mkdir(exist_ok=False);core_proof=D/'core_obstruction_analysis_v1.json';cp=read(core_proof);assert all(sha(p)==h for p,h in cp['bindings'].items());specs={s['case']:s for s in protocol['cases']};contexts={};plans=[];bindings={str(p):sha(p) for p in (D/'protocol.json',D/'independent_verification_v1.json',core_proof,graph,Path(__file__).resolve())}
 reverse_offsets=array('I',[0])*(len(caps)+1)
 for v in vs:reverse_offsets[v+1]+=1
 for i in range(len(caps)):reverse_offsets[i+1]+=reverse_offsets[i]
 cursor=array('I',reverse_offsets);reverse_edges=array('I',[0])*len(us)
 for eid,v in enumerate(vs):reverse_edges[cursor[v]]=eid;cursor[v]+=1
 for row in cp['rows']:
  case=row['case'];bp=B/case/'candidate_bank.jsonl';fp=D/case/'final_conditional_trees.jsonl';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};state={r['net_id']:r['candidate'] for r in map(json.loads,fp.read_text().splitlines())};package=set(specs[case]['package_NETs']);outside=Counter()
  for net,options in bank.items():
   sets=[owned(c) for c in options];common=set.intersection(*sets)
   if net not in package:outside.update(common)
  core=row['inclusion_minimal_protected_NETs'];usage=Counter(n for net in core for n in owned(state[net]));cid=min(row['minimal_core_obstruction']['failed_CIDs']);q=next(r for r in bank[row['failed_NET']][0]['records'] if r['connection_id']==cid);structure={n for n,t in enumerate(types) if caps[n]==0 or (t=='SOURCE' and n!=q['source']) or (t=='SINK' and n!=q['sink'])};base=mask(outside,Counter())|structure;all_core_blocked=mask(outside,usage)|structure;extra=sorted(all_core_blocked-base);unit_owned={n for n in usage if caps[n]==1};assert extra
  plan=dict(case=case,connection_id=cid,net_id=row['failed_NET'],source=q['source'],sink=q['sink'],budget=q['budget_integer'],frozen_core_NETs=core,conditional_core_extra_blocked_nodes=extra);plans.append(plan);contexts[case]=(outside,structure,unit_owned,q)
  for p in (bp,fp):bindings[str(p)]=sha(p)
 policy='Proof diagnosis only. Each fixed case uses the lowest failed CID from the independently inclusion-minimized frozen NET core and unchanged budget. In both full-positive-capacity graph and fixed-outside graph, obtain one budget-feasible path; every individually budget-unavoidable occupied unit node must lie on that path, so test all intersections with frozen-core unit occupancy. In conditional graph minimize the complete extra core-exhausted resource set using deterministic complement chunk deletion (start two chunks, shrink on failure preserved, increase granularity otherwise), then verify all single deletions are feasible. No tree generation, label reads, budget/threshold sweep, model selection or root mutation. Positive answers carry physical paths; negative answers carry endpoint-block proof or capped reverse-distance Bellman potential with cap budget+1, for independent edge-inequality verification.'
 (O/'protocol.json').write_text(json.dumps(dict(policy=policy,cases=plans,bindings=bindings,unavailable_cases_preserved=6),indent=2)+'\n');bindings[str(O/'protocol.json')]=sha(O/'protocol.json');rows=[];total=0
 for plan in plans:
  case=plan['case'];outside,structure,unit_owned,q=contexts[case];source,sink,budget=q['source'],q['sink'],q['budget_integer'];assert 0<=budget<2**64-1;out=O/case;out.mkdir(parents=True);cache={};queries=[]
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
  necessity={}
  for mode in ('full_graph','outside'):
   baseline=ask(mode,set());assert baseline['status']=='BUDGET_PATH';pathnodes={source}|{vs[eid] for eid in baseline['physical_edge_ids']};candidates=sorted(pathnodes&unit_owned);tested=[dict(node=n,query_id=ask(mode,{n})['query_id'],budget_unavoidable=ask(mode,{n})['status']=='NO_BUDGET_PATH') for n in candidates];necessity[mode]=dict(baseline_query_id=baseline['query_id'],complete_occupied_unit_candidate_nodes=candidates,single_node_tests=tested)
  current=list(plan['conditional_core_extra_blocked_nodes']);assert ask('outside',current)['status']=='NO_BUDGET_PATH';granularity=2;trace=[]
  while len(current)>=2:
   chunk=(len(current)+granularity-1)//granularity;reduced=False
   for start in range(0,len(current),chunk):
    trial=current[:start]+current[start+chunk:];answer=ask('outside',trial);trace.append(dict(before_size=len(current),deleted_chunk=current[start:start+chunk],query_id=answer['query_id'],obstruction_retained=answer['status']=='NO_BUDGET_PATH'))
    if answer['status']=='NO_BUDGET_PATH':current=trial;granularity=max(2,granularity-1);reduced=True;break
   if reduced:continue
   if granularity>=len(current):break
   granularity=min(len(current),granularity*2)
  cut=ask('outside',current);assert current and cut['status']=='NO_BUDGET_PATH';deletion_witnesses=[]
  for node in current:
   answer=ask('outside',set(current)-{node});assert answer['status']=='BUDGET_PATH';deletion_witnesses.append(dict(restored_node=node,query_id=answer['query_id']))
  singleton_cut_tests=[dict(node=n,query_id=ask('outside',{n})['query_id'],budget_unavoidable=ask('outside',{n})['status']=='NO_BUDGET_PATH') for n in current]
  row=dict(case=case,connection_id=plan['connection_id'],failed_NET=plan['net_id'],frozen_core_NETs=plan['frozen_core_NETs'],initial_extra_blocked_resources=len(plan['conditional_core_extra_blocked_nodes']),necessity=necessity,inclusion_minimal_conditional_budget_cut=current,cut_query_id=cut['query_id'],cut_node_types={n:types[n] for n in current},single_deletion_witnesses=deletion_witnesses,singleton_cut_tests=singleton_cut_tests,queries=len(queries));p=out/'result.json';p.write_text(json.dumps(dict(result=row,minimization_trace=trace,queries=[dict(query_id=r['query_id'],path=str(out/f"query_{r['query_id']:04d}.json")) for r in queries]),indent=2)+'\n');bindings[str(p)]=sha(p);rows.append(row);print('BUDGET_RESOURCE_CUT',json.dumps({k:v for k,v in row.items() if k!='necessity'}),flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
 (O/'verification.json').write_text(json.dumps(dict(status='ALL3_BUDGET_RESOURCE_NECESSITY_AND_CUT_PROOFS_PREPARED_PENDING_INDEPENDENT_REPLAY',rows=rows,queries=total,bindings=bindings,labels_opened=False,budgets_changed=False,scope='All physically admissible positive-capacity paths under stated base masks and unchanged per-CID integer delay budget, not only a parent-choice or shortest-path DAG. Certificates still require independent replay. No candidate generation or ranking, utility or general routing claim.'),indent=2)+'\n')
if __name__=='__main__':main()
