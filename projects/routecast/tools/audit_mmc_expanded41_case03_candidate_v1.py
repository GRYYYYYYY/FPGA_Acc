"""Independent original XML query minima and full-capacity CBS trace audit."""
import json,time,sys,xml.parsers.expat as X
from fractions import Fraction
from pathlib import Path
from array import array
from collections import Counter
from pre_route_endpoints import sha
from raw_mask_dual_check_v1 import Checker
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_expanded41_conflict_first_CBS_v1_2026-10-21';P=D/'verification.json';v=json.loads(P.read_text());assert all(sha(p)==h for k in ['bindings','files'] for p,h in v[k].items());S=R/'experiments/mmc_cover_plus151_residual_v1_2026-10-21';A=S/'independent_verification_v1.json';oldproof=json.loads(A.read_text());assert all(sha(p)==h for p,h in oldproof['bindings'].items());oldv=json.loads((S/'verification.json').read_text());old={(i['case'],i['net_id']):json.loads(Path(i['result']).read_text()) for i in oldv['rows']};graph=next(Path(p) for p in v['bindings'] if p.endswith('.xml'));bindings={str(p):sha(p) for p in [P,A,Path(__file__),D/'raw_dual_check.so',R/'tools/raw_mask_dual_check_v1.py',R/'tools/soft_demand_cpp/raw_mask_dual_check_v1.cpp']}
provenance=D/'audit_binary_provenance.json';bp=json.loads(provenance.read_text());assert bp['sha256']==sha(bp['source'])==sha(D/'raw_dual_check.so');assert bp['prior_audit_sha256']==sha(bp['prior_audit']);bindings[str(provenance)]=sha(provenance)
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

base_audit=D/'independent_verification_v1.json';ba=json.loads(base_audit.read_text());assert all(sha(p)==h for p,h in ba['bindings'].items());assert next(r for r in ba['rows'] if r['case']=='case_03')['full_capacity_feasible_states']==1;bindings[str(base_audit)]=sha(base_audit)
case='case_03';result=next(r for r in v['rows'] if r['case']==case);state_path=D/case/('assessment_%03d.json'%result['last_assessment']);state=json.loads(state_path.read_text());assert state['result']['satisfiable'];picks={int(n):b for n,b in state['result']['assignment'].items()};treepaths={int(n):p for n,p in state['trees'].items()};planpath=R/'experiments/mmc_bank_mandatory_capacity_v1_2026-10-21/verification.json';plan=json.loads(planpath.read_text());row=next(r for r in plan['rows'] if r['case']==case);ep_path=Path(row['endpoint']);endpoints={q['connection_id']:q for q in json.loads(ep_path.read_text())['connections']};bindings[str(ep_path)]=sha(ep_path);bindings[str(planpath)]=sha(planpath);bindings[str(state_path)]=sha(state_path);records=[];arm_paths={}
for arm,path in row['frames'].items():
 assert sha(path)==plan['bindings'][path];bindings[path]=sha(path);arm_paths[arm]=path;frame=json.loads(Path(path).read_text())
 for q in frame['records']:
  n=q['net_id']
  if n not in treepaths and picks[n]==(arm=='B'):records.append((n,q['connection_id'],q['source'],q['sink'],q['budget_integer'],q['answer']['delay'],q['answer']['physical_edge_ids']))
for n,path in treepaths.items():
 r=json.loads(Path(path).read_text());assert r['all_connections_within_budget'];bindings[path]=sha(path)
 for q in r['connections']:records.append((n,q['connection_id'],q['source'],q['sink'],q['budget'],q['minimum'],q['physical_edge_ids']))
assert len(records)==len(endpoints)==115572 and {q[1] for q in records}==set(endpoints)
parents={};owned={};connections=0;max_ratio=0
for net,cid,source,sink,budget,reported,edges in records:
 ep=endpoints[cid];assert (net,source,sink)==(ep['net_id'],ep['source'],ep['sink']);assert kinds[source]==1 and kinds[sink]==2 and caps[source]>0;node=source;seen={source};delay=0;parent=parents.setdefault(net,{});union=owned.setdefault(net,{source})
 for e in edges:
  a,b=us[e],vs[e];assert node==a and b not in seen and caps[b]>0
  if b in parent:assert parent[b]==(a,e)
  parent[b]=(a,e);seen.add(b);union.add(b);delay+=weights[e];node=b
 assert node==sink and delay==reported and delay<=budget;connections+=1;max_ratio=max(max_ratio,delay/budget)
assert len(owned)==55300 and set(owned)==set(picks)|set(treepaths);ledger=Counter(n for union in owned.values() for n in union if kinds[n] in [5,6] and caps[n]>0);assert all(x<=caps[n] for n,x in ledger.items())
manifest={'case':case,'full_NETs':55300,'full_connections':connections,'all_positive_CHANNELs':258720,'overused_CHANNELs':0,'all_selected_paths_original_budget_qualified':True,'selected_original_frames':arm_paths,'unextended_pick_B_NETs':sorted(n for n,b in picks.items() if b),'extended_tree_paths':treepaths,'max_selected_path_budget_ratio':max_ratio,'independent_XML_audit_seconds':time.perf_counter()-start,'bindings':bindings,'scope':'Full one-case source/sink paths, consistent shared physical parents, original model budgets, and distinct-NET positive CHANNEL capacity. Original fixed input frames; not native/canonical VPR/STA legality, original full9 predictor admission, unseen designs, cost acceptance or end-to-end benefit.'}
assert all(sha(p)==h for p,h in bindings.items());(D/'case03_full_candidate_verification_v1.json').write_text(json.dumps(manifest,indent=2)+'\n');print('FULL CASE03 CANDIDATE VERIFIED',55300,connections,'CHANNEL overuse0',flush=True)
