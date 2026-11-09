"""All positive-CHANNEL capacities for fixed C support and remaining A/B choices."""
import json,itertools,time,xml.parsers.expat as X
from pathlib import Path
from collections import defaultdict,Counter
from pre_route_endpoints import sha
from binary_owner_capacity_v1 import solve
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_ABC_capacity_v1_2026-10-21';D.mkdir()
CROOT=R/'experiments/mmc_cover_budget_avoidance_v1_2026-10-21';CP=CROOT/'complete_C_alternatives.jsonl';decision=json.loads((CROOT/'research_decision_v1.json').read_text());assert decision['bindings'][str(CP)]==sha(CP);PC=R/'experiments/mmc_bank_mandatory_capacity_v1_2026-10-21/verification.json';old=json.loads(PC.read_text());P=R/'experiments/mmc_coupled_chooser_cost_and_data_scope_v1_2026-10-19/input_only_choice_protocol_v1.json';bankplan=json.loads(P.read_text());records=list(map(json.loads,CP.open()));bycase=defaultdict(dict);wanted=set()
for r in records:
 assert r['net_id'] not in bycase[r['case']];bycase[r['case']][r['net_id']]=r
 for q in r['records']:wanted.update(q['answer']['physical_edge_ids'])
ep=json.loads(Path(old['rows'][0]['endpoint']).read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];bindings={str(p):sha(p) for p in [Path(__file__),CP,CROOT/'independent_verification_v1.json',CROOT/'research_decision_v1.json',PC,P,R/'tools/binary_owner_capacity_v1.py',R/'tests/test_binary_owner_capacity_v1.py']};bindings[str(graph)]=ep['graph_sha256']
(D/'protocol.json').write_text(json.dumps({'bindings':bindings,'cases':['case_01','case_02','case_03'],'policy':'Exactly the registered C trees, cover and keeper plan; all other NETs keep complete original A/B choices. No new searches, masks, native labels or case selection.','forcing_certificate':'Each cover NET has an original mandatory capacity1 channel shared with a noncover NET, whose two alternatives both own it. A/B of the cover NET also own it, so C is necessary within this supplied ABC library.','constraints':'All positive CHANNELs from original XML, not old eligible-only mask. Fixed owners = forced C plus common A/B owners; >capacity is an immediate UNSAT witness. Otherwise pairwise forbidden binary owner states, exact2SAT with checkable implication paths or a directly capacity-verified assignment.','validation':'700 three-variable formulas against exhaustive assignments; UNSAT implication paths replayed. Full real ownership certificate audited separately.','scope':'Supplied candidate representability only; no full VPR/STA/native, prediction, family or gain claim.','native_calls':0},indent=2)+'\n')
start=time.perf_counter();stack=[];arcs={};caps={};nodes=0;edge_id=0
def begin(name,a):
 global nodes,edge_id
 parent=stack[-1] if stack else None;stack.append(name)
 if name=='node' and parent=='rr_nodes':
  n=int(a['id']);assert n==nodes;nodes+=1
  if a['type'] in ['CHANX','CHANY'] and int(a['capacity'])>0:caps[n]=int(a['capacity'])
 elif name=='edge' and parent=='rr_edges':
  if edge_id in wanted:arcs[edge_id]=(int(a['src_node']),int(a['sink_node']),int(a['switch_id']))
  edge_id+=1
def end(name):assert stack.pop()==name
parser=X.ParserCreate();parser.StartElementHandler=begin;parser.EndElementHandler=end
with graph.open('rb') as f:
 while block:=f.read(8*1024*1024):parser.Parse(block,False)
parser.Parse(b'',True);assert len(caps)==258720 and set(caps.values())=={1} and set(arcs)==wanted
Cunions={}
for case,nets in bycase.items():
 Cunions[case]={}
 for net,r in nets.items():
  owned=set();parents={}
  for q in r['records']:
   node=q['source'];seen={node};owned.add(node)
   for eid in q['answer']['physical_edge_ids']:
    u,w,s=arcs[eid];assert u==node and w not in seen
    if w in parents:assert parents[w]==(u,s)
    parents[w]=(u,s);seen.add(w);owned.add(w);node=w
   assert node==q['sink']
  Cunions[case][net]=owned
(D/'C_node_unions.json').write_text(json.dumps({case:{str(n):sorted(o) for n,o in nets.items()} for case,nets in Cunions.items()})+'\n');rows=[]
for item in old['rows']:
 case=item['case'];chosen=set(bycase[case]);assert chosen=={n for comp in item['owner_conflict_components'] for n in comp['cover']}
 bp=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19'/case/'banks.jsonl';assert sha(bp)==bankplan['bindings'][str(bp)];bindings[str(bp)]=sha(bp)
 banks={r['net_id']:(set(r['A']),set(r['B'])) for r in map(json.loads,bp.open())};assert len(banks)==55300
 forcing=[]
 for net in sorted(chosen):
  options=[(w['node'],other) for w in item['witnesses'] if net in w['NETs'] for other in w['NETs'] if other not in chosen];assert options
  node,other=min(options);assert node in banks[net][0]&banks[net][1]&banks[other][0]&banks[other][1] and node not in Cunions[case][net]
  forcing.append({'net_id':net,'channel':node,'unextended_NET':other})
 fixed=defaultdict(list);variable=defaultdict(list)
 for net,(a,b) in banks.items():
  if net in chosen:
   for node in Cunions[case][net]&caps.keys():fixed[node].append({'net_id':net,'variant':'C'})
  else:
   for node in (a&b)&caps.keys():fixed[node].append({'net_id':net,'variant':'AB'})
   for node in (a-b)&caps.keys():variable[node].append((net,False))
   for node in (b-a)&caps.keys():variable[node].append((net,True))
 hard=[];clauses=[];clause_witness=[]
 for node in sorted(set(fixed)|set(variable)):
  if len(fixed[node])>1:hard.append({'node':node,'capacity':1,'owners':fixed[node]});continue
  if fixed[node]:
   for literal in sorted(variable[node]):clauses.append((literal,));clause_witness.append({'node':node,'fixed_owner':fixed[node][0]})
  else:
   for a,b in itertools.combinations(sorted(variable[node]),2):clauses.append((a,b));clause_witness.append({'node':node})
 if hard:answer={'satisfiable':False,'reason':'FIXED_OWNER_OVERLOAD','witnesses':hard}
 else:answer=solve(set(banks)-chosen,clauses)
 state={'case':case,'forced_C':forcing,'hard_overloads':hard,'forbidden':clauses,'clause_witnesses':clause_witness,'result':answer,'positive_CHANNELs':len(caps)}
 if answer['satisfiable']:
  picks={int(n):bool(b) for n,b in answer['assignment'].items()};ledger=Counter(node for net,(a,b) in banks.items() for node in ((Cunions[case][net] if net in chosen else b if picks[net] else a)&caps.keys()));assert all(ledger[n]<=caps[n] for n in caps)
  state['selected_CHANNEL_ledger']=dict(ledger)
 out=D/(case+'.json');out.write_text(json.dumps(state,indent=2)+'\n');rows.append({'case':case,'forced_C_NETs':len(chosen),'hard_overload_nodes':len(hard),'clauses':len(clauses),'satisfiable':answer['satisfiable'],'reason':answer.get('reason','2SAT_SCC'),'result_file':str(out)})
 print('ABC CAPACITY',json.dumps(rows[-1]),flush=True)
assert all(sha(p)==h for p,h in bindings.items())
files={str(p):sha(p) for p in D.glob('*.json')};(D/'verification.json').write_text(json.dumps({'rows':rows,'graph_nodes':nodes,'graph_edges':edge_id,'seconds':time.perf_counter()-start,'bindings':bindings,'files':files,'scope':'Fixed supplied ABC library, all positive CHANNEL capacities. C forcing justified by original mandatory witnesses. Does not establish general RR infeasibility, timing/STA/native or prediction/gain.'},indent=2)+'\n')
