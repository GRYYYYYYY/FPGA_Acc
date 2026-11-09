"""A-only whole-design capacity repair with finite input-frozen ownership scope."""
import json,time
from pathlib import Path
from types import SimpleNamespace
from collections import Counter,defaultdict
from array import array
from pre_route_endpoints import sha
from MMC_zero_node_RC_shared_CSR_v1 import load
from masked_raw_forward_v1 import Search
from resumable_resource_cbs_v2 import search as cbs,restore_v1,SearchBudgetExceeded
wall_start=time.perf_counter();R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_A_only_joint_CBS_resume_v2_2026-10-21';D.mkdir(exist_ok=False);P=R/'experiments/mmc_A_only_repair_protocol_v1_2026-10-21/protocol_v2.json';plan=json.loads(P.read_text());assert all(plan['eligibility'].values());graph=next(Path(p) for p in plan['bindings'] if p.endswith('.xml'));binary=R/'experiments/wide_cost_backend_build_v1_2026-10-13/search.so';bindings={str(p):sha(p) for p in [P,graph,binary,Path(__file__),R/'tools/resumable_resource_cbs_v2.py',R/'tools/masked_raw_forward_v1.py',R/'tools/MMC_zero_node_RC_shared_CSR_v1.py',R/'tools/wide_cost_search_bridge_v2.py']};limits={k:plan['limits_per_case'][k] for k in ['max_states','max_queries','max_seconds']};OLD=R/'experiments/mmc_A_only_joint_CBS_v1_2026-10-21';CONT=OLD/'continuation_protocol_v2.json';continuation=json.loads(CONT.read_text());old_v=json.loads((OLD/'verification.json').read_text());old_a=json.loads((OLD/'independent_verification_v1.json').read_text());assert all(sha(p)==h for p,h in continuation['source_hashes'].items());assert all(sha(p)==h for p,h in old_a['bindings'].items());assert all(sha(p)==h for k in ['bindings','files'] for p,h in old_v[k].items());bindings.update({str(p):sha(p) for p in [CONT,OLD/'verification.json',OLD/'independent_verification_v1.json',OLD/'case_01_full_candidate_v1.json']});limits={'max_states':128,'max_queries':512,'max_seconds':60}
(D/'protocol.json').write_text(json.dumps({'plan':str(P),'limits_per_case':limits,'scope':plan['evidence_scope'],'bindings':bindings},indent=2)+'\n');start=time.perf_counter();row,dest,cost,caps,kinds,_=load(graph);channels={n for n,k in enumerate(kinds) if k in ['CHANX','CHANY'] and caps[n]>0};assert len(channels)==258720 and all(caps[n]==1 for n in channels);engine=Search({'row_offsets':row,'dest_ranks':dest,'capacities':caps},SimpleNamespace(increments=cost,initial=lambda n:0),binary);setup=time.perf_counter()-start;files={};rows=[];print('A_ONLY_SETUP',setup,flush=True)
try:
 for item in plan['rows']:
  if item['case'] not in continuation['cases']:continue
  tick=time.perf_counter();case=item['case'];work=D/case;work.mkdir();framepath=Path(item['frame_A']);assert sha(framepath)==plan['bindings'][str(framepath)];bindings[str(framepath)]=sha(framepath);frame=json.loads(framepath.read_text());groups=defaultdict(list);banks=defaultdict(set)
  for q in frame['records']:
   groups[q['net_id']].append(q);banks[q['net_id']].add(q['source']);banks[q['net_id']].update(dest[e] for e in q['answer']['physical_edge_ids'])
  assert len(banks)==55300 and len(frame['records'])==115572;banks={n:owned&channels for n,owned in banks.items()};owners=defaultdict(list)
  for net,support in banks.items():
   for n in support:owners[n].append(net)
  conflicts=[{'channel':n,'owners':sorted(ns)} for n,ns in sorted(owners.items()) if len(ns)>1];assert conflicts==item['initial_conflicts'];selected=set(item['reroutable_NETs']);assert selected=={n for w in conflicts for n in w['owners']};fixed=Counter(n for net,support in banks.items() if net not in selected for n in support);assert all(c<=1 for c in fixed.values());blocked=set(fixed);initial={};references={}
  for net in sorted(selected):
   connections=[dict(connection_id=q['connection_id'],source=q['source'],sink=q['sink'],budget=q['budget_integer'],reachable=True,minimum=q['answer']['delay'],within_budget=q['answer']['delay']<=q['budget_integer'],physical_edge_ids=q['answer']['physical_edge_ids']) for q in groups[net]];assert all(q['within_budget'] for q in connections);r=dict(case=case,net_id=net,source=connections[0]['source'],initial=0,connections=connections,all_connections_within_budget=True);p=work/('initial_NET_%d.json'%net);p.write_text(json.dumps(r,indent=2)+'\n');files[str(p)]=sha(p);references[net]=r;assert not banks[net]&blocked;initial[net]={'support':banks[net],'cost':sum(q['minimum'] for q in connections),'result':str(OLD/case/p.name)}
  counts={'assessments':0,'queries':0,'cache_hits':0,'requests':0};last={};request_trace=[];query_cache={};tree_cache={}
  for cp in sorted((OLD/case).glob('query_*/result.json')):
   cr=json.loads(cp.read_text());query_cache[cr['net_id'],tuple(cr['extra_forbidden'])]=str(cp)
  def load_tree(path):
   if path not in tree_cache:
    r=json.loads(Path(path).read_text());good=r['all_connections_within_budget'];support={dest[e] for q in r['connections'] for e in q['physical_edge_ids']} & channels;tree_cache[path]={'support':support,'cost':sum(q['minimum'] for q in r['connections']),'result':path} if good else None
   return tree_cache[path]
  def trace(net,extra,path,reused):
   request_trace.append({'request':len(request_trace)+1,'net_id':net,'extra_forbidden':sorted(extra),'result':str(path),'reused':reused})
  def assess(trees):
   counts['assessments']+=1;owned=defaultdict(list)
   for net,t in trees.items():
    assert not t['support']&blocked
    for n in t['support']:owned[n].append(net)
   conflict=next(([(net,n) for net in sorted(ns)] for n,ns in sorted(owned.items()) if len(ns)>1),None)
   if conflict is None:
    ledger=fixed.copy()
    for t in trees.values():ledger.update(t['support'])
    assert all(c<=1 for c in ledger.values())
   state=dict(assessment=counts['assessments'],trees={net:t['result'] for net,t in trees.items()},conflict=conflict,full_CHANNEL_capacity_feasible=conflict is None);p=work/('assessment_%03d.json'%counts['assessments']);p.write_text(json.dumps(state,indent=2)+'\n');files[str(p)]=sha(p);last.clear();last.update(state);return conflict
  def reroute(net,extra):
   key=(net,tuple(sorted(extra)))
   if key in query_cache:
    counts['requests']+=1;counts['cache_hits']+=1;path=query_cache[key];trace(net,extra,path,True);return load_tree(path)
   if counts['queries']>=128:raise SearchBudgetExceeded()
   counts['requests']+=1;counts['queries']+=1;qt=time.perf_counter();r=references[net];mask=blocked|set(extra);answer=engine.query(r['source'],{q['sink'] for q in r['connections']},mask);out=work/('query_%03d_NET_%d'%(counts['queries'],net));out.mkdir();raw=array('Q');raw.frombytes(answer['raw_u128_bytes']);assert all(raw[2*n+1]==0 for n in range(len(caps)) if answer['settled_bytes'][n]);potential=array('Q',(raw[2*n] if answer['settled_bytes'][n] else answer['cutoff'] for n in range(len(caps))));(out/'potential.u64').write_bytes(potential.tobytes());(out/'reachable.u8').write_bytes(answer['settled_bytes']);connections=[];support=set()
   for q in r['connections']:
    a=answer['answers'][q['sink']];slots=a.get('slots',[]);connections.append(dict(connection_id=q['connection_id'],source=q['source'],sink=q['sink'],budget=q['budget'],reachable=a['reachable'],minimum=a.get('minimum'),within_budget=a['reachable'] and a['minimum']<=q['budget'],physical_edge_ids=slots));support.update(dest[e] for e in slots)
   good=all(q['within_budget'] for q in connections);result=dict(case=case,net_id=net,source=r['source'],initial=0,cutoff=answer['cutoff'],extra_forbidden=sorted(extra),blocked_nodes=sorted(mask),connections=connections,all_connections_within_budget=good,potential_file=str(out/'potential.u64'),reachable_file=str(out/'reachable.u8'),seconds=time.perf_counter()-qt);p=out/'result.json';p.write_text(json.dumps(result,indent=2)+'\n')
   for f in out.iterdir():files[str(f)]=sha(f)
   query_cache[key]=str(p);trace(net,extra,p,False)
   print('A_ONLY_QUERY',case,counts['queries'],net,good,flush=True);return {'support':support&channels,'cost':sum(q['minimum'] for q in connections),'result':str(p)} if good else None
  def score(trees):
   ledger=Counter(n for t in trees.values() for n in t['support']);return (sum(max(0,c-1) for c in ledger.values()),sum(t['cost'] for t in trees.values()))
  prior_case=next(r for r in old_v['rows'] if r['case']==case)
  def old_query(sid,net,mask):
   path=OLD/case/('query_%03d_NET_%d'%(sid,net))/'result.json';r=json.loads(path.read_text());assert r['net_id']==net and r['extra_forbidden']==sorted(mask);return load_tree(str(path))
  restored=restore_v1(initial,prior_case['events'],old_query)
  def encode_checkpoint(cp):
   if cp is None:return None
   return {'states':{sid:{'masks':{n:sorted(mask) for n,mask in st['masks'].items()},'trees':{n:t['result'] for n,t in st['trees'].items()}} for sid,st in cp['states'].items()},'seen':[list((n,list(mask)) for n,mask in key) for key in sorted(cp['seen'])],'serial':cp['serial'],'frontier':cp['frontier'],'pending':cp['pending']}
  imported=work/'imported_checkpoint.json';imported.write_text(json.dumps(encode_checkpoint(restored),indent=2)+'\n');files[str(imported)]=sha(imported);print('A_ONLY_RESUME_IMPORT',case,'frontier',len(restored['frontier']),'pending',len(restored['pending']),flush=True)
  result=cbs(initial,assess,reroute,score,checkpoint=restored,**limits);checkpoint=result.pop('checkpoint',None);cp_path=work/'checkpoint.json';cp_path.write_text(json.dumps(encode_checkpoint(checkpoint),indent=2)+'\n');files[str(cp_path)]=sha(cp_path);trace_path=work/'route_requests.json';trace_path.write_text(json.dumps(request_trace,indent=2)+'\n');files[str(trace_path)]=sha(trace_path);result.update(new_raw_searches=counts['queries'],cache_hits=counts['cache_hits'],imported_frontier=len(restored['frontier']),imported_pending=len(restored['pending']),checkpoint_file=str(cp_path));result.pop('trees',None);result['masks']={n:sorted(mask) for n,mask in result.get('masks',{}).items()};result.update(case=case,selected_NETs=len(selected),last_assessment=last['assessment'],case_total_seconds=time.perf_counter()-tick);p=work/'result.json';p.write_text(json.dumps(result,indent=2)+'\n');files[str(p)]=sha(p);rows.append(result);print('A_ONLY_CASE',case,result['status'],result['expanded'],result['queries'],flush=True)
finally:engine.close()
assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps({'rows':rows,'setup_seconds':setup,'total_seconds':time.perf_counter()-wall_start,'bindings':bindings,'files':files,'independent_verification_pending':True,'scope':'case02/03 frontier continuation with preserved auditedcase01; total timer includes prior validation and frontier/cache restoration after Python imports. All3 input-frozen A-only conflict owner scopes; archived A acquisition excluded from this functional diagnostic timing. No B choices or B paths used in route inference. No quality, native legality or matched net gain claim.'},indent=2)+'\n')
