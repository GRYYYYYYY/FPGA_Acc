"""Independent full-channel ledger or original-owner UNSAT certificate replay."""
import json,time,xml.parsers.expat as X
from pathlib import Path
from array import array
from collections import defaultdict,Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_CD_full_capacity_v1_2026-10-21';P=D/'verification.json';v=json.loads(P.read_text());assert all(sha(p)==h for p,h in v['bindings'].items());S=R/'experiments/mmc_conflict_neighbor_avoidance_v1_2026-10-21';V=S/'verification.json';A=S/'independent_verification_v1.json';a=json.loads(A.read_text());assert all(sha(p)==h for p,h in a['bindings'].items());sv=json.loads(V.read_text());assert all(sha(p)==h for k in ['bindings','files'] for p,h in sv[k].items());C=R/'experiments/mmc_cover_plus151_residual_v1_2026-10-21/complete_C_alternatives.jsonl';crows=list(map(json.loads,C.open()));new={(r['case'],r['net_id']):json.loads(Path(r['result']).read_text()) for r in sv['rows']};graph=next(Path(p) for p in v['bindings'] if p.endswith('.xml'));bindings={str(p):sha(p) for p in [P,V,A,C,graph,Path(__file__)]};start=time.perf_counter();us=array('I');vs=array('I');channels=set();stack=[]
def begin(tag,attrs):
 parent=stack[-1] if stack else None;stack.append(tag)
 if tag=='node' and parent=='rr_nodes' and attrs['type'] in ['CHANX','CHANY'] and int(attrs['capacity'])>0:assert int(attrs['capacity'])==1;channels.add(int(attrs['id']))
 elif tag=='edge' and parent=='rr_edges':us.append(int(attrs['src_node']));vs.append(int(attrs['sink_node']))
def end(tag):assert stack.pop()==tag
parser=X.ParserCreate();parser.StartElementHandler=begin;parser.EndElementHandler=end
with graph.open('rb') as f:
 while b:=f.read(8*1024*1024):parser.Parse(b,False)
parser.Parse(b'',True);assert len(channels)==258720 and len(us)==8097539

def support(qs,old):
 owned=set();parents={}
 for q in qs:
  node=q['source'];seen={node};owned.add(node)
  for e in (q['answer']['physical_edge_ids'] if old else q['physical_edge_ids']):
   src,dst=us[e],vs[e];assert src==node and dst not in seen
   if dst in parents:assert parents[dst]==src
   parents[dst]=src;seen.add(dst);owned.add(dst);node=dst
  assert node==q['sink']
 return owned&channels
oldroot=R/'experiments/mmc_cover_plus151_residual_v1_2026-10-21'
oldproof=oldroot/'independent_verification_v1.json';oldaudit=json.loads(oldproof.read_text());assert oldaudit['all_within_budget']==oldaudit['all_connections']==453;assert all(sha(p)==h for p,h in oldaudit['bindings'].items());bindings[str(oldproof)]=sha(oldproof)
oldv=json.loads((oldroot/'verification.json').read_text());oldresults={(i['case'],i['net_id']):json.loads(Path(i['result']).read_text()) for i in oldv['rows']}
for c in crows:
 old=oldresults[c['case'],c['net_id']];assert len(c['records'])==len(old['connections'])
 for q,o in zip(c['records'],old['connections']):
  assert all(q[k]==o[k] for k in ['connection_id','source','sink']);assert q['answer']['physical_edge_ids']==o['physical_edge_ids'] and q['answer']['delay']==o['minimum'] and q['budget_integer']==o['budget'] and o['within_budget']
replace=defaultdict(dict)
for c in crows:
 case,net=c['case'],c['net_id'];r=new[case,net];aa=support(c['records'],True);bb=support(r['connections'],False) if r['all_connections_within_budget'] else aa;replace[case][net]=(aa,bb)
rows=[]
for item in v['rows']:
 case=item['case'];p=Path(item['result_file']);bindings[str(p)]=sha(p);state=json.loads(p.read_text());bp=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19'/case/'banks.jsonl';assert sha(bp)==v['bindings'][str(bp)];bindings[str(bp)]=sha(bp);banks={r['net_id']:(set(r['A'])&channels,set(r['B'])&channels) for r in map(json.loads,bp.open())};banks.update(replace[case]);assert len(banks)==55300
 result=state['result']
 if result['satisfiable']:
  assignment={int(n):b for n,b in result['assignment'].items()};assert set(assignment)==set(banks) and all(type(b) is bool for b in assignment.values());ledger=Counter(n for net,(aa,bb) in banks.items() for n in (bb if assignment[net] else aa));assert all(ledger[n]<=1 for n in channels)
  mode='FULL258720_CHANNEL_LEDGER_VERIFIED'
 elif state['hard_overloads']:
  for w in state['hard_overloads']:
   n=w['node'];nets=w['NETs'];assert n in channels and len(set(nets))==len(nets)>1 and all(n in banks[net][0]&banks[net][1] for net in nets)
  mode='FIXED_COMMON_OWNER_OVERLOAD_VERIFIED'
 else:
  clauses=state['forbidden'];witness=state['clause_channels'];assert len(clauses)==len(witness)
  def clause_valid(k):
   c=clauses[k];n=witness[k];assert n in channels and len(c) in [1,2]
   for net,b in c:assert type(b) is bool and n in banks[net][int(b)]
   if len(c)==2:assert c[0][0]!=c[1][0]
   else:assert any(net!=c[0][0] and n in aa&bb for net,(aa,bb) in banks.items())
  net=result['conflict_NET']
  for key,initial,target in [('false_to_true',[net,False],[net,True]),('true_to_false',[net,True],[net,False])]:
   current=initial
   for step in result[key]:
    assert step['from']==current;k=step['clause'];clause_valid(k);c=clauses[k];edges=[(c[0],[c[-1][0],not c[-1][1]])]
    if len(c)==2:edges.append((c[1],[c[0][0],not c[0][1]]))
    assert (step['from'],step['to']) in edges;current=step['to']
   assert current==target
  mode='CONTRADICTORY_ORIGINAL_OWNER_IMPLICATION_PATHS_VERIFIED'
 rows.append({'case':case,'satisfiable':result['satisfiable'],'certificate':mode,'all_positive_CHANNELs_checked':len(channels)});print('INDEPENDENT CD',json.dumps(rows[-1]),flush=True)
assert all(sha(p)==h for p,h in bindings.items()) and all(sha(p)==h for p,h in v['bindings'].items());out={'status':'ALL3_BINARY_C_D_CAPACITY_RESULTS_INDEPENDENTLY_VERIFIED','rows':rows,'seconds':time.perf_counter()-start,'bindings':bindings,'scope':'Only supplied budget-admissible C/D and frozen A/B candidates; not arbitrary coordinated trees, full RR/native/STA legality, prediction or net benefit.'};(D/'independent_verification_v1.json').write_text(json.dumps(out,indent=2)+'\n')
