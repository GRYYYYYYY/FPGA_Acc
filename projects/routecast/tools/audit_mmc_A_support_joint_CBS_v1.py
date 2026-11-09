"""Original-XML full A inputs, query minima and complete A-only capacity audit."""
import json,time,xml.parsers.expat as X
from pathlib import Path
from array import array
from fractions import Fraction
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from raw_mask_dual_check_v1 import Checker
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_A_support_joint_CBS_v1_2026-10-21';P=D/'verification.json';v=json.loads(P.read_text());assert all(sha(p)==h for k in ['bindings','files'] for p,h in v[k].items());PLAN=R/'experiments/mmc_A_only_repair_protocol_v1_2026-10-21/protocol_v2.json';plan=json.loads(PLAN.read_text());graph=next(Path(p) for p in v['bindings'] if p.endswith('.xml'));bindings={str(p):sha(p) for p in [P,PLAN,graph,Path(__file__),D/'raw_dual_check.so',R/'tools/raw_mask_dual_check_v1.py',R/'tools/soft_demand_cpp/raw_mask_dual_check_v1.cpp']};provenance=D/'audit_binary_provenance.json';bp=json.loads(provenance.read_text());assert bp['sha256']==sha(bp['source'])==sha(D/'raw_dual_check.so') and bp['prior_audit_sha256']==sha(bp['prior_audit']);bindings[str(provenance)]=sha(provenance)
start=time.perf_counter();caps=array('I');kinds=array('B');us=array('I');vs=array('I');weights=array('Q');switches={};stack=[];node_timing=0;current_switch=None;switch_type=None;last_source=-1
codes={'SOURCE':1,'SINK':2,'IPIN':3,'OPIN':4,'CHANX':5,'CHANY':6}
def begin(name,a):
 global current_switch,switch_type,node_timing,last_source
 parent=stack[-1] if stack else None;stack.append(name)
 if name=='node' and parent=='rr_nodes':
  assert int(a['id'])==len(caps);caps.append(int(a['capacity']));kinds.append(codes[a['type']])
 elif name=='timing' and parent=='node':
  assert Fraction(a['R'])==Fraction(a['C'])==0;node_timing+=1
 elif name=='switch' and parent=='switches':current_switch=int(a['id']);switch_type=a['type'];assert current_switch not in switches
 elif name=='timing' and parent=='switch':
  assert switch_type in ['buffer','mux','tristate'] and Fraction(a.get('Cinternal','0'))==0
  w=Fraction(a.get('Tdel','0'))*10**18;assert w.denominator==1 and 0<=w<2**64;switches[current_switch]=int(w)
 elif name=='edge' and parent=='rr_edges':
  a1,b,s=map(int,[a['src_node'],a['sink_node'],a['switch_id']]);assert a1>=last_source and a1<len(caps) and b<len(caps);last_source=a1;us.append(a1);vs.append(b);weights.append(switches[s])
def end(name):assert stack.pop()==name
parser=X.ParserCreate();parser.StartElementHandler=begin;parser.EndElementHandler=end
with graph.open('rb') as f:
 while data:=f.read(8*1024*1024):parser.Parse(data,False)
parser.Parse(b'',True);assert len(caps)==node_timing==904438 and len(us)==8097539 and len(caps)*max(weights)<2**64
channels={n for n in range(len(caps)) if kinds[n] in [5,6] and caps[n]>0};assert len(channels)==258720 and all(caps[n]==1 for n in channels);checker=Checker(D/'raw_dual_check.so');cache={};references={};A_support_by_case={};fixed_by_case={};source_counts={};selected_by_case={};source_paths=0;queries=0;inequalities=0

def physical_tree(r,blocked=frozenset()):
 parents={};owned=set()
 for q in r['connections']:
  assert kinds[q['source']]==1 and kinds[q['sink']]==2 and caps[q['source']]>0
  if not q['reachable']:continue
  node=q['source'];seen={node};owned.add(node);value=0
  for eid in q['physical_edge_ids']:
   a,b=us[eid],vs[eid];assert a==node and b not in seen and caps[b]>0 and b not in blocked
   if b in parents:assert parents[b]==(a,eid)
   parents[b]=(a,eid);seen.add(b);owned.add(b);value+=weights[eid];node=b
  assert node==q['sink'] and value==q.get('raw_cost',q.get('minimum'))
 return owned&channels
for item in plan['rows']:
 case=item['case'];framepath=Path(item['frame_A']);assert sha(framepath)==v['bindings'][str(framepath)];bindings[str(framepath)]=sha(framepath);frame=json.loads(framepath.read_text());epfile=Path(item['endpoint']);ep=json.loads(epfile.read_text());bindings[str(epfile)]=sha(epfile);assert ep['graph_sha256']==sha(graph);endpoints={q['connection_id']:q for q in ep['connections']};assert len(endpoints)==115572;groups=defaultdict(list);seen=set()
 for q in frame['records']:
  cid=q['connection_id'];assert cid not in seen;seen.add(cid);assert all(q[k]==endpoints[cid][k] for k in ['net_id','source','sink']);assert q['answer']['delay']<=q['budget_integer'];groups[q['net_id']].append(dict(connection_id=cid,source=q['source'],sink=q['sink'],budget=q['budget_integer'],reachable=True,raw_cost=q['answer']['delay'],within_budget=True,physical_edge_ids=q['answer']['physical_edge_ids']))
 assert seen==set(endpoints) and len(groups)==55300;owners=defaultdict(list);banks={}
 for net,qs in groups.items():
  r=dict(case=case,net_id=net,connections=qs,source=qs[0]['source'],initial=0,all_connections_within_budget=True);support=physical_tree(r);banks[net]=support;references[case,net]=r
  for n in support:owners[n].append(net)
 A_support_by_case[case]=set().union(*banks.values());source_paths+=len(seen);source_counts[case]=len(groups);conflicts=[{'channel':n,'owners':sorted(ns)} for n,ns in sorted(owners.items()) if len(ns)>1];assert conflicts==item['initial_conflicts'];selected=set(item['reroutable_NETs']);assert selected=={n for w in conflicts for n in w['owners']};selected_by_case[case]=selected;fixed=Counter(n for net,support in banks.items() if net not in selected for n in support);assert all(c<=1 for c in fixed.values());fixed_by_case[case]=fixed
 for net in selected:
  p=D/case/('initial_NET_%d.json'%net);r=json.loads(p.read_text());assert r==references[case,net];assert not banks[net]&fixed.keys();cache[str(p)]=(r,banks[net])
print('ALL3_FULL_ORIGINAL_A_PATHS_VERIFIED',source_paths,flush=True)
for p in sorted(D.glob('case_*/query_*/result.json')):
 r=json.loads(p.read_text());case,net=r['case'],r['net_id'];ref=references[case,net];blocked=set(fixed_by_case[case])|set(r['extra_forbidden']);assert blocked==set(r['blocked_nodes']);assert all(n in channels for n in blocked) and net in selected_by_case[case] and r['source']==ref['source'] and r['initial']==0;mask=bytearray(len(caps))
 for n in blocked:mask[n]=1
 expected_weight=(len(caps)-1)*max(weights)+1;assert r['deterministic_weight']==expected_weight;outside=channels-A_support_by_case[case];has_raw=r['has_raw_minimum_certificate'];potential=None;cut=None
 if has_raw:
  assert r['kind'] in ['RAW_FEASIBLE_FALLBACK','RAW_INFEASIBLE_CERTIFICATE'];potential=array('Q');potential.frombytes(Path(r['potential_file']).read_bytes());cut=bytearray(Path(r['reachable_file']).read_bytes());require_cut=any(not q['reachable'] for q in r['connections']);inequalities+=checker.check(us,vs,weights,caps,potential,cut,mask,r['source'],0,r['cutoff'],require_cut)
 else:assert r['kind']=='A_SUPPORT_PRIMAL' and r['all_connections_within_budget'] and not r['pruning_allowed'] and not any(k in r for k in ['potential_file','reachable_file','cutoff'])
 assert r['pruning_allowed']==(not r['all_connections_within_budget']);assert not r['pruning_allowed'] or has_raw
 qr={q['connection_id']:q for q in ref['connections']};assert len(r['connections'])==len(qr) and {q['connection_id'] for q in r['connections']}==set(qr)
 for q in r['connections']:
  original=qr[q['connection_id']];assert all(q[k]==original[k] for k in ['source','sink','budget'])
  if q['reachable']:
   assert q['within_budget']==(q['raw_cost']<=q['budget']);count=sum(vs[e] in outside for e in q['physical_edge_ids']);assert q['outside_A_visits']==count and q['weighted_objective']==q['raw_cost']+expected_weight*count
   if has_raw:assert cut[q['sink']] and q['raw_cost']==potential[q['sink']]
  else:assert has_raw and not cut[q['sink']] and q['raw_cost'] is None and not q['within_budget']
 support=physical_tree(r,blocked);assert not support&blocked and r['all_connections_within_budget']==all(q['within_budget'] for q in r['connections']);cache[str(p)]=(r,support);queries+=1
print('A_ONLY_ALL_QUERIES_VERIFIED',queries,flush=True);rows=[]
for item in v['rows']:
 case=item['case'];count=0;feasible=0
 for p in sorted((D/case).glob('assessment_*.json')):
  state=json.loads(p.read_text());trees={int(n):cache[path] for n,path in state['trees'].items()};assert set(trees)==selected_by_case[case];ledger=fixed_by_case[case].copy()
  for net,(r,support) in trees.items():assert r['case']==case and r['net_id']==net and r['all_connections_within_budget'] and not support&fixed_by_case[case].keys();ledger.update(support)
  if state['conflict'] is None:
   assert state['full_CHANNEL_capacity_feasible'] and all(ledger[n]<=caps[n] for n in channels);feasible+=1;ledgerpath=D/(case+'_CHANNEL_ledger_v1.json');ledgerpath.write_text(json.dumps({n:c for n,c in ledger.items() if c},separators=(',',':'))+'\n');manifest={'case':case,'full_NETs':55300,'full_connections':115572,'original_A_frame':next(x['frame_A'] for x in plan['rows'] if x['case']==case),'repaired_tree_paths':state['trees'],'CHANNEL_ledger':str(ledgerpath),'CHANNEL_ledger_sha256':sha(ledgerpath),'positive_CHANNELs':len(channels),'overused_CHANNELs':0,'all_original_model_budgets_verified':True,'source_assessment':str(p),'scope':'Complete original XML input paths and repaired trees, original budgets and distinct-NET CHANNEL capacity. No native/canonical/STA, quality, unseen or net gain claim.','producer_verification':str(P),'producer_verification_sha256':sha(P)};(D/(case+'_full_candidate_v1.json')).write_text(json.dumps(manifest,indent=2)+'\n')
  else:
   assert not state['full_CHANNEL_capacity_feasible'];ns=state['conflict'];channel=ns[0][1];assert channel in channels and len({net for net,n in ns})==len(ns)>caps[channel] and all(n==channel and channel in trees[net][1] for net,n in ns)
  count+=1
 assert (item['status']=='FEASIBLE')==(feasible==1);rows.append({'case':case,'producer_status':item['status'],'selected_NETs':len(selected_by_case[case]),'assessments_verified':count,'full_capacity_feasible_states':feasible,'query_count':item['queries'],'weighted_searches':item['weighted_searches'],'raw_searches':item['raw_searches']})
assert all(sha(p)==h for p,h in bindings.items()) and all(sha(p)==h for k in ['bindings','files'] for p,h in v[k].items());out={'status':'ALL3_A_SUPPORT_PRIMAL_BUDGETS_RAW_PRUNING_CERTIFICATES_AND_CAPACITY_VERIFIED','rows':rows,'full_A_paths_verified':source_paths,'query_certificates':queries,'eligible_XML_edge_inequalities':inequalities,'seconds':time.perf_counter()-start,'bindings':bindings,'scope':'Weighted preferred trees are primal/budget verified only, not electrical minima or globally optimal L1 projection. Raw fallback/pruning states have complete original-edge dual/cut certificates. Inputs for all3 full55300NET/115572connection cases; each saved repaired tree original budget and primal/dual, each assessed conflict disjunction. Feasible manifest only if complete capacity verified. Frontier exhaustion alone not independently certified; no gate/quality/cost promotion.'};(D/'independent_verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(rows),flush=True)
