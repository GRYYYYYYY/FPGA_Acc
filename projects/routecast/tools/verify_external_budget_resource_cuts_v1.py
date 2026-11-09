"""Expat original-graph replay: physical witnesses and Bellman lower bounds."""
import json,sys,hashlib,xml.parsers.expat
from array import array
from fractions import Fraction
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'prospective_external_family_blocker_release_v1_2026-10-19';H=E/'prospective_external_family_monotone_witness_package_v1_2026-10-19';D=E/'prospective_external_family_budget_resource_cuts_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 proof=read(D/'verification.json');protocol=read(D/'protocol.json');assert proof['status']=='ALL3_BUDGET_RESOURCE_NECESSITY_AND_CUT_PROOFS_PREPARED_PENDING_INDEPENDENT_REPLAY'
 for receipt in (proof,protocol):assert all(sha(p)==h for p,h in receipt['bindings'].items())
 coreproof=H/'core_obstruction_analysis_v1.json';oldcores={r['case']:r for r in read(coreproof)['rows']};packages={r['case']:set(r['package_NETs']) for r in read(H/'protocol.json')['cases']};graph=next(Path(p) for p in proof['bindings'] if p.endswith('/rr_graph.xml'));caps=array('I');types=[];us=array('I');vs=array('I');switches=array('I');weights={};stack=[];active={};timings=0
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
 assert timings==len(caps) and len(us)==len(vs)==len(switches) and all(s in weights for s in switches);n=len(caps);bindings={str(p):sha(p) for p in (D/'verification.json',D/'protocol.json',coreproof,H/'protocol.json',graph,Path(__file__).resolve())};rows=[];clauses=[];positive=negative=inequalities=0
 def owned(c):
  ns={r['source'] for r in c['records']}
  for r in c['records']:ns.update(vs[e] for e in r['answer']['physical_edge_ids'])
  return ns
 for plan in protocol['cases']:
  case=plan['case'];bp=B/case/'candidate_bank.jsonl';fp=H/case/'final_conditional_trees.jsonl';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};state={r['net_id']:r['candidate'] for r in map(json.loads,fp.read_text().splitlines())};old=oldcores[case];assert plan['frozen_core_NETs']==old['inclusion_minimal_protected_NETs'] and plan['connection_id']==min(old['minimal_core_obstruction']['failed_CIDs']) and plan['net_id']==old['failed_NET'];record=next(r for r in bank[plan['net_id']][0]['records'] if r['connection_id']==plan['connection_id']);source,sink,budget=record['source'],record['sink'],record['budget_integer'];assert (source,sink,budget)==(plan['source'],plan['sink'],plan['budget']);outside=Counter()
  for net,options in bank.items():
   sets=[owned(c) for c in options];common=set.intersection(*sets);assert all(all(node in ns for ns in sets) for node in {node for ns in sets for node in ns if caps[node]>1})
   if net not in packages[case]:outside.update(common)
  assert all(count<=caps[node] for node,count in outside.items());core_nodes={net:owned(state[net]) for net in plan['frozen_core_NETs']};usage=Counter(node for ns in core_nodes.values() for node in ns);unit_owned={node for node in usage if caps[node]==1};struct={node for node,t in enumerate(types) if caps[node]==0 or (t=='SOURCE' and node!=source) or (t=='SINK' and node!=sink)};outside_mask=struct|{node for node,cap in enumerate(caps) if outside[node]>=cap};core_mask=struct|{node for node,cap in enumerate(caps) if outside[node]+usage[node]>=cap};extra=sorted(core_mask-outside_mask);assert plan['conditional_core_extra_blocked_nodes']==extra;out=D/case;rp=out/'result.json';data=read(rp);result=data['result'];assert result['initial_extra_blocked_resources']==len(extra);queries=[];pathnodes={};bykey={};casepos=caseneg=caseineq=0
  for qid,item in enumerate(data['queries']):
   path=out/f'query_{qid:04d}.json';assert item==dict(query_id=qid,path=str(path));q=read(path);assert q['query_id']==qid and (q['source'],q['sink'],q['budget'])==(source,sink,budget);assert q['mode'] in ('outside','full_graph');assert q['extra_forbidden_nodes']==sorted(set(q['extra_forbidden_nodes']));key=(q['mode'],tuple(q['extra_forbidden_nodes']));assert key not in bykey;bykey[key]=qid;taboo=(outside_mask if q['mode']=='outside' else struct)|set(q['extra_forbidden_nodes']);assert all(0<=node<n for node in taboo) and q['forbidden_nodes']==len(taboo);blocked=bytearray(n)
   for node in taboo:blocked[node]=1
   if q['status']=='BUDGET_PATH':
    assert not blocked[source] and not blocked[sink];u=source;seen={u};delay=0
    for eid in q['physical_edge_ids']:
     assert type(eid) is int and 0<=eid<len(us) and us[eid]==u;v=vs[eid];assert v not in seen and not blocked[v] and caps[v]>0;seen.add(v);delay+=weights[switches[eid]];u=v
    assert u==sink and delay==q['witness_delay']<=budget;pathnodes[qid]=seen;positive+=1;casepos+=1
   else:
    assert q['status']=='NO_BUDGET_PATH';negative+=1;caseneg+=1
    if q['proof_kind']=='FORBIDDEN_ENDPOINT':assert blocked[source] or blocked[sink]
    else:
     assert q['proof_kind']=='CAPPED_BELLMAN_LOWER_BOUND' and not blocked[source] and not blocked[sink];pp=out/f'query_{qid:04d}.potential_u64.bin';assert str(pp)==q['potential_file'] and sha(pp)==q['potential_sha256'] and q['itemsize']==8 and q['cap']==budget+1 and pp.stat().st_size==n*8;phi=array('Q')
     with pp.open('rb') as f:phi.fromfile(f,n)
     if q['byteorder']!=sys.byteorder:phi.byteswap()
     assert len(phi)==n and phi.itemsize==8 and max(phi)<=budget+1 and phi[sink]==0 and phi[source]==budget+1;checked=0
     for u,v,s in zip(us,vs,switches):
      if blocked[u] or blocked[v]:continue
      assert phi[u]<=weights[s]+phi[v],(case,qid,u,v);checked+=1
     inequalities+=checked;caseineq+=checked;bindings[str(pp)]=sha(pp)
   queries.append(q);bindings[str(path)]=sha(path)
  assert len(queries)==result['queries'];unavoidable={}
  for mode,description in result['necessity'].items():
   assert mode in ('full_graph','outside');baseline=queries[description['baseline_query_id']];assert baseline['mode']==mode and not baseline['extra_forbidden_nodes'] and baseline['status']=='BUDGET_PATH';candidates=sorted(pathnodes[baseline['query_id']]&unit_owned);assert description['complete_occupied_unit_candidate_nodes']==candidates and [t['node'] for t in description['single_node_tests']]==candidates;mandatory=[]
   for test in description['single_node_tests']:
    q=queries[test['query_id']];assert q['mode']==mode and q['extra_forbidden_nodes']==[test['node']] and test['budget_unavoidable']==(q['status']=='NO_BUDGET_PATH')
    if test['budget_unavoidable']:mandatory.append(test['node'])
   unavoidable[mode]=mandatory
  assert set(unavoidable)=={'full_graph','outside'};current=extra;granularity=2;trace=data['minimization_trace'];position=0
  while len(current)>=2:
   size=(len(current)+granularity-1)//granularity;reduced=False
   for startpos in range(0,len(current),size):
    trial=current[:startpos]+current[startpos+size:];q=queries[bykey['outside',tuple(trial)]];entry=trace[position];position+=1;blocked=q['status']=='NO_BUDGET_PATH';assert entry==dict(before_size=len(current),deleted_chunk=current[startpos:startpos+size],query_id=q['query_id'],obstruction_retained=blocked)
    if blocked:current=trial;granularity=max(2,granularity-1);reduced=True;break
   if reduced:continue
   if granularity>=len(current):break
   granularity=min(len(current),granularity*2)
  assert position==len(trace) and current==result['inclusion_minimal_conditional_budget_cut'];cut=queries[result['cut_query_id']];assert cut['mode']=='outside' and cut['extra_forbidden_nodes']==current and cut['status']=='NO_BUDGET_PATH';assert set(current)<=set(extra) and current
  assert len(result['single_deletion_witnesses'])==len(current)
  for node,item in zip(current,result['single_deletion_witnesses']):
   q=queries[item['query_id']];assert item['restored_node']==node and q['mode']=='outside' and q['extra_forbidden_nodes']==sorted(set(current)-{node}) and q['status']=='BUDGET_PATH'
  for node,test in zip(current,result['singleton_cut_tests']):
   q=queries[test['query_id']];assert test['node']==node and q['mode']=='outside' and q['extra_forbidden_nodes']==[node] and test['budget_unavoidable']==(q['status']=='NO_BUDGET_PATH')
  assert {int(k):v for k,v in result['cut_node_types'].items()}=={node:types[node] for node in current};outside_hash=hashlib.sha256(json.dumps(sorted(outside.items()),separators=(',',':')).encode()).hexdigest();owners={node:sorted(net for net,ns in core_nodes.items() if node in ns) for node in current};assert all(caps[node]==1 for node in current)
  clause=dict(case=case,connection_id=plan['connection_id'],NET=plan['net_id'],source=source,sink=sink,budget_integer=budget,graph_sha256=sha(graph),outside_unique_NET_occupancy_sha256=outside_hash,conditional_budget_cut=current,necessity='At least one cut node must retain positive residual capacity for this NET. For these unit nodes: OR(not occupied_by_other_NET(node) for node in cut). Necessary only under the bound outside occupancy; not sufficient for routing.',frozen_core_owners=owners,negative_certificate_query=str(out/f"query_{cut['query_id']:04d}.json"),scope='Invalidate or rederive when outside occupancy assumptions, graph epoch, endpoints or budget change. No unconditional reservation is inferred from a conditional cut.')
  clauses.append(clause);row=dict(case=case,connection_id=plan['connection_id'],conditional_budget_cut=current,cut_node_types={node:types[node] for node in current},frozen_core_owners=owners,full_graph_budget_unavoidable_core_unit_nodes=unavoidable['full_graph'],conditional_budget_unavoidable_core_unit_nodes=unavoidable['outside'],positive_paths_verified=casepos,negative_certificates_verified=caseneg,original_edge_Bellman_inequalities_verified=caseineq,all_candidate_necessity_and_cut_minimization_replayed=True);rows.append(row)
  for p in (bp,fp,rp):bindings[str(p)]=sha(p)
  print('BUDGET_CUT_CERTIFICATE_PASS',json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());learned=D/'learned_conditional_budget_constraints_v1.json';assert not learned.exists();learned.write_text(json.dumps(dict(status='PROOF_BOUND_NECESSARY_CONDITIONAL_RESOURCE_AVAILABILITY_CLAUSES',clauses=clauses,labels_opened=False,scope='Graph-derived budget necessity under explicit case-specific outside occupancy; not a new predictor, route selection, quality or utility pass.'),indent=2)+'\n');bindings[str(learned)]=sha(learned)
 (D/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL3_BUDGET_RESOURCE_PATH_AND_BELLMAN_CERTIFICATES_INDEPENDENT_EXPAT_VERIFIED',rows=rows,positive_paths_verified=positive,negative_certificates_verified=negative,original_edge_Bellman_inequalities_verified=inequalities,bindings=bindings,scope='Negative Bellman potentials telescope over every allowed original graph path, not only sampled, shortest or parent-DAG paths. Positive witnesses prove existence. Complete occupied-unit necessity tests use containment in one feasible baseline path. Constraints retain outside-assumption/graph/endpoint/budget binding. No general routing, forecast, native utility or full-time gain.'),indent=2)+'\n')
if __name__=='__main__':main()
