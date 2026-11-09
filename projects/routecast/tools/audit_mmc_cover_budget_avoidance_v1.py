"""Independent original-XML dual/primal tree and unchanged-budget audit."""
import json,sys,time,xml.parsers.expat as X
from fractions import Fraction
from pathlib import Path
from array import array
from collections import defaultdict
from pre_route_endpoints import sha
from raw_mask_dual_check_v1 import Checker
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_cover_budget_avoidance_v1_2026-10-21';P=D/'verification.json';v=json.loads(P.read_text());assert sys.byteorder=='little'
assert all(sha(p)==h for doc in ['bindings','files'] for p,h in v[doc].items());planfile=R/'experiments/mmc_bank_mandatory_capacity_v1_2026-10-21/verification.json';plan=json.loads(planfile.read_text());plans={r['case']:r for r in plan['rows']};refs={};expected_masks={};bindings={str(P):sha(P),str(Path(__file__)):sha(__file__),str(D/'raw_dual_check.so'):sha(D/'raw_dual_check.so'),str(R/'tools/soft_demand_cpp/raw_mask_dual_check_v1.cpp'):sha(R/'tools/soft_demand_cpp/raw_mask_dual_check_v1.cpp'),str(R/'tools/raw_mask_dual_check_v1.py'):sha(R/'tools/raw_mask_dual_check_v1.py')}
for case,row in plans.items():
 chosen={n for c in row['owner_conflict_components'] for n in c['cover']};masks={n:set() for n in chosen}
 for w in row['witnesses']:
  rest=sorted(set(w['NETs'])-chosen);keeper=rest[0] if rest else min(w['NETs'])
  for n in set(w['NETs'])&chosen:
   if n!=keeper:masks[n].add(w['node'])
 for n,b in masks.items():expected_masks[case,n]=b
 case_refs={}
 for arm,path in row['frames'].items():
  records=json.loads(Path(path).read_text())['records'];case_refs[arm]={r['connection_id']:r for r in records if r['net_id'] in chosen}
  origin=Path(path).parent;protocol=origin/'protocol.json';doc=json.loads(protocol.read_text());base=Path(doc['structural_node_base_proof']);assert json.loads(base.read_text())['scale']==10**18
  receipt=json.loads((origin/'receipt.json').read_text());assert receipt['bindings'][str(base)]==sha(base)==v['bindings'][str(base)];bindings[str(protocol)]=sha(protocol);bindings[str(base)]=sha(base)
 refs[case]=case_refs
 first_ep=json.loads(Path(row['endpoint']).read_text())
graph=Path(first_ep['inputs']['graph']['path']);assert v['bindings'][str(graph)]==sha(graph);bindings[str(graph)]=sha(graph)
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
parse_seconds=time.perf_counter()-start;checker=Checker(D/'raw_dual_check.so');rows=[];total_checked=0
for item in v['rows']:
 r=json.loads(Path(item['result']).read_text());case,net=r['case'],r['net_id'];blocked=set(r['blocked_nodes']);assert blocked==expected_masks[case,net]
 mask=bytearray(len(caps))
 for n in blocked:assert kinds[n] in [5,6] and caps[n]==1;mask[n]=1
 potential=array('Q');potential.frombytes(Path(r['potential_file']).read_bytes());cut=bytearray(Path(r['reachable_file']).read_bytes());require_cut=any(not q['reachable'] for q in r['connections'])
 checked=checker.check(us,vs,weights,caps,potential,cut,mask,r['source'],r['initial'],r['cutoff'],require_cut);total_checked+=checked
 qa={cid:q for cid,q in refs[case]['A'].items() if q['net_id']==net};qb={cid:q for cid,q in refs[case]['B'].items() if q['net_id']==net};assert len(r['connections'])==len(qa) and {q['connection_id'] for q in r['connections']}==set(qa)==set(qb)
 parents={};union=set();passed=0
 for q in r['connections']:
  original=qa[q['connection_id']];assert all(q[k]==original[k] for k in ['source','sink']);assert q['budget']==original['budget_integer']==qb[q['connection_id']]['budget_integer'];assert kinds[q['source']]==1 and kinds[q['sink']]==2
  if not q['reachable']:assert not cut[q['sink']] and require_cut and q['minimum'] is None and not q['within_budget'];continue
  assert cut[q['sink']] and q['minimum']==potential[q['sink']]
  node=q['source'];value=r['initial'];seen={node};union.add(node)
  for edge in q['physical_edge_ids']:
   assert type(edge) is int and 0<=edge<len(us);a1,b=us[edge],vs[edge];assert a1==node and b not in seen and caps[b]>0 and not mask[b]
   if b in parents:assert parents[b]==(a1,edge)
   parents[b]=(a1,edge);assert potential[b]==potential[a1]+weights[edge];seen.add(b);union.add(b);value+=weights[edge];node=b
  assert node==q['sink'] and value==q['minimum'];assert q['within_budget']==(value<=q['budget']);passed+=q['within_budget']
 all_pass=passed==len(qa);assert all_pass==item['whole_NET_budget_feasible']==r['all_connections_within_budget'];assert not union.intersection(blocked)
 rows.append({'case':case,'net_id':net,'connections':len(qa),'within_budget':passed,'complete_shared_parent_tree_verified':all_pass,'exact_minimum_duals_verified':True,'eligible_XML_edge_inequalities':checked,'blocked_nodes':sorted(blocked),'owned_nodes':len(union)})
 print('INDEPENDENT RAW TREE',case,net,passed,len(qa),flush=True)
assert set(expected_masks)=={(r['case'],r['net_id']) for r in rows};assert all(sha(p)==h for doc in ['bindings','files'] for p,h in v[doc].items()) and all(sha(p)==h for p,h in bindings.items())
result={'status':'ALL36_ORIGINAL_XML_RAW_DUALS_COMPLETE_NET_TREES_AND_UNCHANGED_BUDGETS_PASS','rows':rows,'all_connections':sum(r['connections'] for r in rows),'all_within_budget':sum(r['within_budget'] for r in rows),'all_complete_shared_parent_trees':all(r['complete_shared_parent_tree_verified'] for r in rows),'total_eligible_XML_edge_inequalities':total_checked,'independent_XML_parse_seconds':parse_seconds,'total_audit_seconds':time.perf_counter()-start,'bindings':bindings,'scope':'Fixed keeper plan, exact raw costs and original perpin budgets. Complete individual NET trees only; no simultaneous full-design capacity, structural/criticality objective admission, STA/native/canonical legality, prediction or gain claim.'}
(D/'independent_verification_v1.json').write_text(json.dumps(result,indent=2)+'\n');print('ALL36 FULL_XML_DUAL_AND_TREE_CERTIFICATES_PASS',result['all_connections'],flush=True)
