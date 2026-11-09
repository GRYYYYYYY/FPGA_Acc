"""Independent original XML query minima and full-capacity CBS trace audit."""
import json,time,sys,xml.parsers.expat as X
from fractions import Fraction
from pathlib import Path
from array import array
from collections import Counter
from pre_route_endpoints import sha
from raw_mask_dual_check_v1 import Checker
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_bounded_joint_CBS_v1_2026-10-21';P=D/'verification.json';v=json.loads(P.read_text());assert all(sha(p)==h for k in ['bindings','files'] for p,h in v[k].items());S=R/'experiments/mmc_cover_plus151_residual_v1_2026-10-21';A=S/'independent_verification_v1.json';oldproof=json.loads(A.read_text());assert all(sha(p)==h for p,h in oldproof['bindings'].items());oldv=json.loads((S/'verification.json').read_text());old={(i['case'],i['net_id']):json.loads(Path(i['result']).read_text()) for i in oldv['rows']};graph=next(Path(p) for p in v['bindings'] if p.endswith('.xml'));bindings={str(p):sha(p) for p in [P,A,Path(__file__),D/'raw_dual_check.so',R/'tools/raw_mask_dual_check_v1.py',R/'tools/soft_demand_cpp/raw_mask_dual_check_v1.cpp']}
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
checker=Checker(D/'raw_dual_check.so');query_count=0;inequalities=0;cache={}

def tree_support(r):
 parents={};owned=set()
 for q in r['connections']:
  if not q['reachable']:continue
  node=q['source'];seen={node};owned.add(node);value=r['initial']
  for eid in q['physical_edge_ids']:
   a,b=us[eid],vs[eid];assert a==node and b not in seen and caps[b]>0
   if b in parents:assert parents[b]==(a,eid)
   parents[b]=(a,eid);seen.add(b);owned.add(b);value+=weights[eid];node=b
  assert node==q['sink'] and value==q['minimum']
 return {n for n in owned if kinds[n] in [5,6] and caps[n]>0}
for p in sorted(D.glob('case_*/query_*/result.json')):
 r=json.loads(p.read_text());reference=old[r['case'],r['net_id']];extra=set(r['extra_forbidden']);assert all(kinds[n] in [5,6] and caps[n]==1 for n in extra);blocked=set(r['blocked_nodes']);assert blocked==set(reference['blocked_nodes'])|extra and r['source']==reference['source'] and r['initial']==0
 mask=bytearray(len(caps))
 for n in blocked:assert kinds[n] in [5,6] and caps[n]==1;mask[n]=1
 potential=array('Q');potential.frombytes(Path(r['potential_file']).read_bytes());cut=bytearray(Path(r['reachable_file']).read_bytes());unreachable=any(not q['reachable'] for q in r['connections']);inequalities+=checker.check(us,vs,weights,caps,potential,cut,mask,r['source'],r['initial'],r['cutoff'],unreachable);refs={q['connection_id']:q for q in reference['connections']};assert len(r['connections'])==len(refs) and {q['connection_id'] for q in r['connections']}==set(refs)
 for q in r['connections']:
  ref=refs[q['connection_id']];assert all(q[k]==ref[k] for k in ['source','sink','budget']);assert kinds[q['source']]==1 and kinds[q['sink']]==2
  if q['reachable']:assert cut[q['sink']] and q['minimum']==potential[q['sink']] and q['within_budget']==(q['minimum']<=q['budget'])
  else:assert not cut[q['sink']] and q['minimum'] is None and not q['within_budget']
 support=tree_support(r);assert not support&blocked;assert r['all_connections_within_budget']==all(q['within_budget'] for q in r['connections']);cache[str(p)]=(r,support);query_count+=1
print('CBS ORIGINAL QUERY CERTIFICATES',query_count,flush=True)
rows=[]
for case_row in v['rows']:
 case=case_row['case'];bankpath=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19'/case/'banks.jsonl';assert sha(bankpath)==v['bindings'][str(bankpath)];banks={b['net_id']:(set(b['A']),set(b['B'])) for b in map(json.loads,bankpath.open())};extended={net for c,net in old if c==case};count=0;feasible=0
 for p in sorted((D/case).glob('assessment_*.json')):
  state=json.loads(p.read_text());trees={}
  for n,path in state['trees'].items():
   net=int(n)
   if path not in cache:
    r=json.loads(Path(path).read_text());assert r==old[case,net];cache[path]=(r,tree_support(r))
   r,support=cache[path];assert r['all_connections_within_budget'] and r['case']==case and r['net_id']==net;trees[net]=support
  assert set(trees)==extended
  def owns(net,b,node):return node in trees[net] if net in trees else node in banks[net][int(b)]
  conflict=state['conflict'];answer=state['result']
  if answer is None:
   assert conflict;node=conflict[0][1];assert all(n==node and node in trees[net] for net,n in conflict);others={net for net,(aa,bb) in banks.items() if net not in extended and node in aa&bb};assert len({net for net,n in conflict}|others)>caps[node] and kinds[node] in [5,6]
  elif answer['satisfiable']:
   picks={int(net):b for net,b in answer['assignment'].items()};assert set(picks)==set(banks)-extended;ledger=Counter(n for net,(aa,bb) in banks.items() for n in (trees[net] if net in trees else bb if picks[net] else aa) if kinds[n] in [5,6] and caps[n]>0);assert all(c<=caps[n] for n,c in ledger.items());assert conflict is None;feasible+=1
  else:
   clauses=state['forbidden'];channels=state['clause_channels'];net=answer['conflict_NET'];required=set()
   for name,initial,terminal in [('false_to_true',[net,False],[net,True]),('true_to_false',[net,True],[net,False])]:
    current=initial
    for step in answer[name]:
     assert step['from']==current;k=step['clause'];clause=clauses[k];node=channels[k];assert kinds[node] in [5,6] and caps[node]==1 and len(clause) in [1,2]
     assert all(n not in extended and owns(n,b,node) for n,b in clause)
     if len(clause)==1:
      ns={n for n in trees if node in trees[n]};required.update((n,node) for n in ns);assert ns or any(n not in extended and n!=clause[0][0] and node in aa&bb for n,(aa,bb) in banks.items())
     else:assert clause[0][0]!=clause[1][0]
     arcs=[(clause[0],[clause[-1][0],not clause[-1][1]])]
     if len(clause)==2:arcs.append((clause[1],[clause[0][0],not clause[0][1]]))
     assert (step['from'],step['to']) in arcs;current=step['to']
    assert current==terminal
   assert {tuple(x) for x in conflict}==required
  count+=1
 assert (case_row['status']=='FEASIBLE')==(feasible==1);rows.append(dict(case=case,producer_status=case_row['status'],assessments_verified=count,full_capacity_feasible_states=feasible,expanded=case_row['expanded'],queries=case_row['queries']))
assert all(sha(p)==h for k in ['bindings','files'] for p,h in v[k].items()) and all(sha(p)==h for p,h in bindings.items());result=dict(status='CBS_QUERY_MINIMA_BUDGET_PRUNES_AND_RESOURCE_CONFLICT_ASSESSMENTS_VERIFIED',rows=rows,query_certificates=query_count,eligible_XML_inequalities=inequalities,seconds=time.perf_counter()-start,bindings=bindings,scope='Each saved query minimum, original budget and path tree, each recorded conflict disjunction and full-channel feasible assessment if present. Search frontier bookkeeping not independently exhaustively reconstructed; producer exhaustion is not an independently certified whole-domain UNSAT claim. No native/STA/prediction/gain.');(D/'independent_verification_v1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(rows),flush=True)
