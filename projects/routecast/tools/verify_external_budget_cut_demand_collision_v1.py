"""Expat original-graph replay: physical witnesses and Bellman lower bounds."""
import json,sys,hashlib,xml.parsers.expat
from array import array
from fractions import Fraction
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'prospective_external_family_blocker_release_v1_2026-10-19';H=E/'prospective_external_family_clause_guided_root_replacement_v1_2026-10-19';C=E/'prospective_external_family_budget_resource_cuts_v1_2026-10-19';D=E/'prospective_external_family_budget_cut_demand_collision_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 proof=read(D/'verification.json');protocol=read(D/'protocol.json');assert proof['status']=='CUT_DEMAND_CAPACITY_CERTIFICATES_PREPARED_PENDING_INDEPENDENT_REPLAY'
 for receipt in (proof,protocol):assert all(sha(p)==h for p,h in receipt['bindings'].items())
 priorproof=read(C/'independent_verification_v1.json');assert all(sha(p)==h for p,h in priorproof['bindings'].items());previous_clauses=read(C/'learned_conditional_budget_constraints_v1.json')['clauses'];packages={r['case']:set(r['package_NETs']) for r in read(H/'protocol.json')['cases']};graph=next(Path(p) for p in proof['bindings'] if p.endswith('/rr_graph.xml'));caps=array('I');types=[];us=array('I');vs=array('I');switches=array('I');weights={};stack=[];active={};timings=0
 def start(name,attrs):
  nonlocal timings
  parent=stack[-1] if stack else None;stack.append(name)
  if name=='node' and parent=='rr_nodes':assert int(attrs['id'])==len(caps);caps.append(int(attrs['capacity']));types.append(attrs['type'])
  elif name=='timing' and parent=='node':assert Fraction(attrs['R'])==Fraction(attrs['C'])==0;timings+=1
  elif name=='switch' and parent=='switches':active['switch']=int(attrs['id'])
  elif name=='timing' and parent=='switch':
   assert all(Fraction(attrs.get(k,'0'))==0 for k in ('R','Cin','Cout','Cinternal'));w=Fraction(attrs.get('Tdel','0'))*10**18;assert w.denominator==1 and w>=0;weights[active['switch']]=w.numerator
  elif name=='edge' and parent=='rr_edges':us.append(int(attrs['src_node']));vs.append(int(attrs['sink_node']));switches.append(int(attrs['switch_id']))
 def end(name):assert stack.pop()==name
 parser=xml.parsers.expat.ParserCreate();parser.StartElementHandler=start;parser.EndElementHandler=end
 with graph.open('rb') as f:parser.ParseFile(f)
 assert timings==len(caps) and len(us)==len(vs)==len(switches) and all(s in weights for s in switches);n=len(caps);bindings={str(p):sha(p) for p in (D/'verification.json',D/'protocol.json',C/'independent_verification_v1.json',C/'learned_conditional_budget_constraints_v1.json',H/'independent_verification_v1.json',H/'protocol.json',graph,Path(__file__).resolve())};rows=[];clauses=[];positive=negative=inequalities=0
 def owned(c):
  ns={r['source'] for r in c['records']}
  for r in c['records']:ns.update(vs[e] for e in r['answer']['physical_edge_ids'])
  return ns
 contexts={};expected_plans=[];expected_groups=[]
 for clause in previous_clauses:
  case=clause['case'];bp=B/case/'candidate_bank.jsonl';fp=H/case/'final_conditional_trees.jsonl';rp=H/case/'result.json';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};state={r['net_id']:r['candidate'] for r in map(json.loads,fp.read_text().splitlines())};observed=read(rp)['failure'];assert observed['phase']=='COMPLETE_PACKAGE';outside=Counter()
  for net,options in bank.items():
   sets=[owned(c) for c in options];common=set.intersection(*sets)
   if net not in packages[case]:outside.update(common)
  stamp=hashlib.sha256(json.dumps(sorted((node,count) for node,count in outside.items() if count),separators=(',',':')).encode()).hexdigest();assert stamp==clause['outside_unique_NET_occupancy_sha256'] and sha(graph)==clause['graph_sha256'];cut=clause['conditional_budget_cut'];assert all(caps[node]==1 and outside[node]==0 for node in cut);known=next(r for r in bank[clause['NET']][0]['records'] if r['connection_id']==clause['connection_id']);knownproof=read(clause['negative_certificate_query']);assert knownproof['status']=='NO_BUDGET_PATH' and knownproof['mode']=='outside' and knownproof['extra_forbidden_nodes']==cut;assert (knownproof['source'],knownproof['sink'],knownproof['budget'])==(known['source'],known['sink'],known['budget_integer']);assert priorproof['bindings'][clause['negative_certificate_query']]==sha(clause['negative_certificate_query']);owners=sorted(net for net,c in state.items() if owned(c)&set(cut));tests={(observed['net_id'],min(observed['failed_CIDs'])):'NEXT_FAILURE'}
  for net in owners:
   if net!=clause['NET']:
    for q in bank[net][0]['records']:tests.setdefault((net,q['connection_id']),'CURRENT_CUT_OWNER')
  expected_groups.append(dict(case=case,cut=cut,available_unit_capacity=sum(caps[node]-outside[node] for node in cut),known_NET=clause['NET'],known_CID=clause['connection_id'],known_certificate_query=clause['negative_certificate_query'],outside_occupancy_sha256=stamp,current_cut_owner_NETs=owners))
  for (net,cid),reason in sorted(tests.items()):
   assert net in packages[case];q=next(r for r in bank[net][0]['records'] if r['connection_id']==cid);expected_plans.append(dict(case=case,key=f'{case}/cid_{cid}',net_id=net,connection_id=cid,source=q['source'],sink=q['sink'],budget=q['budget_integer'],cut=cut,reason=reason))
  contexts[case]=(outside,bank)
  for p in (bp,fp,rp):bindings[str(p)]=sha(p)
 assert protocol['cases']==expected_groups and protocol['queries']==expected_plans
 for plan in expected_plans:
  case=plan['case'];outside,bank=contexts[case];source,sink,budget=plan['source'],plan['sink'],plan['budget'];struct={node for node,t in enumerate(types) if caps[node]==0 or (t=='SOURCE' and node!=source) or (t=='SINK' and node!=sink)};base=struct|{node for node,cap in enumerate(caps) if outside[node]>=cap};out=D/plan['key'];rp=out/'result.json';data=read(rp);result=data['result'];queries=[];casepos=caseneg=0
  for qid,item in enumerate(data['queries']):
   path=out/f'query_{qid:04d}.json';assert item==dict(query_id=qid,path=str(path));q=read(path);assert q['query_id']==qid and q['mode']=='outside' and (q['source'],q['sink'],q['budget'])==(source,sink,budget);extra=q['extra_forbidden_nodes'];assert extra==sorted(set(extra)) and set(extra)<=set(plan['cut']);taboo=base|set(extra);assert q['forbidden_nodes']==len(taboo);blocked=bytearray(n)
   for node in taboo:blocked[node]=1
   if q['status']=='BUDGET_PATH':
    assert not blocked[source] and not blocked[sink];u=source;seen={u};delay=0
    for eid in q['physical_edge_ids']:
     assert type(eid) is int and 0<=eid<len(us) and us[eid]==u;v=vs[eid];assert v not in seen and not blocked[v] and caps[v]>0;seen.add(v);delay+=weights[switches[eid]];u=v
    assert u==sink and delay==q['witness_delay']<=budget;positive+=1;casepos+=1
   else:
    assert q['status']=='NO_BUDGET_PATH';negative+=1;caseneg+=1
    if q['proof_kind']=='FORBIDDEN_ENDPOINT':assert blocked[source] or blocked[sink]
    else:
     assert q['proof_kind']=='CAPPED_BELLMAN_LOWER_BOUND' and not blocked[source] and not blocked[sink];pp=out/f'query_{qid:04d}.potential_u64.bin';assert str(pp)==q['potential_file'] and sha(pp)==q['potential_sha256'] and pp.stat().st_size==n*8;phi=array('Q')
     with pp.open('rb') as f:phi.fromfile(f,n)
     if q['byteorder']!=sys.byteorder:phi.byteswap()
     assert q['itemsize']==phi.itemsize==8 and q['cap']==budget+1 and max(phi)<=budget+1 and phi[sink]==0 and phi[source]==budget+1
     for u,v,switch in zip(us,vs,switches):
      if blocked[u] or blocked[v]:continue
      assert phi[u]<=weights[switch]+phi[v];inequalities+=1
     bindings[str(pp)]=sha(pp)
   queries.append(q);bindings[str(path)]=sha(path)
  assert result['NET']==plan['net_id'] and result['CID']==plan['connection_id'] and result['key']==plan['key'];assert queries[result['baseline_query_id']]['status']=='BUDGET_PATH' and not queries[result['baseline_query_id']]['extra_forbidden_nodes'];assert len(result['singleton_tests'])==len(plan['cut'])
  for node,test in zip(plan['cut'],result['singleton_tests']):assert test['node']==node and queries[test['query_id']]['extra_forbidden_nodes']==[node] and test['unavoidable']==(queries[test['query_id']]['status']=='NO_BUDGET_PATH')
  full=queries[result['full_cut_query_id']];assert full['extra_forbidden_nodes']==plan['cut'] and result['budget_requires_cut']==(full['status']=='NO_BUDGET_PATH');assert {tuple(q['extra_forbidden_nodes']) for q in queries}=={(),tuple(plan['cut'])}|{(node,) for node in plan['cut']};assert result['queries']==len(queries);rows.append(dict(case=case,key=plan['key'],NET=plan['net_id'],CID=plan['connection_id'],cut=plan['cut'],budget_requires_cut=result['budget_requires_cut'],full_cut_query_id=result['full_cut_query_id'],positive_paths_verified=casepos,negative_certificates_verified=caseneg));bindings[str(rp)]=sha(rp)
 collisions=[]
 for group in expected_groups:
  witnesses={group['known_NET']:dict(NET=group['known_NET'],CID=group['known_CID'],certificate_query=group['known_certificate_query'],source='EXISTING_VERIFIED_CUT')}
  for row in sorted((r for r in rows if r['case']==group['case'] and r['budget_requires_cut']),key=lambda r:(r['NET'],r['CID'])):witnesses.setdefault(row['NET'],dict(NET=row['NET'],CID=row['CID'],certificate_query=str(D/row['key']/f"query_{row['full_cut_query_id']:04d}.json"),source='NEW_FULL_CUT_CERTIFICATE'))
  collisions.append(dict(case=group['case'],cut=group['cut'],available_unit_capacity=group['available_unit_capacity'],required_distinct_NETs=len(witnesses),witnesses=[witnesses[net] for net in sorted(witnesses)],fixed_outside_budget_capacity_contradiction=len(witnesses)>group['available_unit_capacity']))
 assert collisions==proof['collisions'];assert all(sha(p)==h for p,h in bindings.items())
 (D/'independent_verification_v1.json').write_text(json.dumps(dict(status='CUT_DEMAND_CAPACITY_TEST_DOMAIN_PATHS_AND_BOUND_AGGREGATION_INDEPENDENTLY_VERIFIED',rows=rows,collisions=collisions,positive_paths_verified=positive,negative_certificates_verified=negative,original_edge_Bellman_inequalities_verified=inequalities,bindings=bindings,scope='All next failed CIDs and all CIDs of current cut-owner NETs other than the prior certified NET were retained. A capacity contradiction, if any, is conditional on exact outside occupancy. Absence of a contradiction for these tested cuts is not general feasibility, absence of other cuts, or NET-tree completeness.'),indent=2)+'\n');print('CUT_DEMAND_INDEPENDENT_RESULT',json.dumps(dict(positive_paths=positive,negative_certificates=negative,conditional_capacity_contradictions=[r['case'] for r in collisions if r['fixed_outside_budget_capacity_contradiction']])),flush=True)
if __name__=='__main__':main()
