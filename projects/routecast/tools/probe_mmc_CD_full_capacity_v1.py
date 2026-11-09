"""Full positive-channel binary C/D versus unextended A/B ownership selection."""
import json,time,itertools,xml.parsers.expat as X
from pathlib import Path
from collections import defaultdict,Counter
from array import array
from pre_route_endpoints import sha
from binary_owner_capacity_v1 import solve
R=Path(__file__).resolve().parents[1];S=R/'experiments/mmc_conflict_neighbor_avoidance_v1_2026-10-21';D=R/'experiments/mmc_CD_full_capacity_v1_2026-10-21';D.mkdir(exist_ok=False)
P=S/'verification.json';A=S/'independent_verification_v1.json';v=json.loads(P.read_text());audit=json.loads(A.read_text());assert all(sha(p)==h for p,h in audit['bindings'].items());C=R/'experiments/mmc_cover_plus151_residual_v1_2026-10-21/complete_C_alternatives.jsonl';F=R/'experiments/mmc_coupled_chooser_cost_and_data_scope_v1_2026-10-19/input_only_choice_protocol_v1.json';frozen=json.loads(F.read_text());Crows=list(map(json.loads,C.open()));new={(r['case'],r['net_id']):json.loads(Path(r['result']).read_text()) for r in v['rows']};graph=next(Path(p) for p in v['bindings'] if p.endswith('.xml') and 'rr' in p.lower());bindings={str(p):sha(p) for p in [P,A,C,F,graph,Path(__file__),R/'tools/binary_owner_capacity_v1.py']};start=time.perf_counter();dest=array('I');channels=set();stack=[]
def begin(tag,a):
 parent=stack[-1] if stack else None;stack.append(tag)
 if tag=='node' and parent=='rr_nodes' and a['type'] in ['CHANX','CHANY'] and int(a['capacity'])>0:assert int(a['capacity'])==1;channels.add(int(a['id']))
 elif tag=='edge' and parent=='rr_edges':dest.append(int(a['sink_node']))
def end(tag):assert stack.pop()==tag
parser=X.ParserCreate();parser.StartElementHandler=begin;parser.EndElementHandler=end
with graph.open('rb') as f:
 while b:=f.read(8*1024*1024):parser.Parse(b,False)
parser.Parse(b'',True);assert len(channels)==258720
replacements=defaultdict(dict)
for c in Crows:
 key=c['case'],c['net_id'];r=new[key];a={n for q in c['records'] for n in [q['source'],*(dest[e] for e in q['answer']['physical_edge_ids'])]}&channels
 b={n for q in r['connections'] for n in [q['source'],*(dest[e] for e in (q['physical_edge_ids'] or []))]}&channels if r['all_connections_within_budget'] else a
 replacements[c['case']][c['net_id']]=(a,b)
rows=[]
for case,replace in sorted(replacements.items()):
 bp=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19'/case/'banks.jsonl';assert sha(bp)==frozen['bindings'][str(bp)];bindings[str(bp)]=sha(bp);banks={r['net_id']:(set(r['A'])&channels,set(r['B'])&channels) for r in map(json.loads,bp.open())};banks.update(replace);assert len(banks)==55300;fixed=defaultdict(list);variable=defaultdict(list)
 for net,(a,b) in banks.items():
  for n in a&b:fixed[n].append(net)
  for n in a-b:variable[n].append((net,False))
  for n in b-a:variable[n].append((net,True))
 hard=[];clauses=[];witness=[]
 for n in sorted(set(fixed)|set(variable)):
  if len(fixed[n])>1:hard.append({'node':n,'NETs':fixed[n]});continue
  if fixed[n]:
   for lit in variable[n]:clauses.append((lit,));witness.append(n)
  else:
   for pair in itertools.combinations(variable[n],2):clauses.append(pair);witness.append(n)
 result={'satisfiable':False,'reason':'FIXED_OWNER_OVERLOAD'} if hard else solve(banks,clauses)
 if result['satisfiable']:
  picks=result['assignment'];ledger=Counter(n for net,(a,b) in banks.items() for n in (b if picks[net] else a));assert all(x<=1 for x in ledger.values())
 out={'case':case,'hard_overloads':hard,'forbidden':clauses,'clause_channels':witness,'result':result,'replaced_NETs':sorted(replace),'D_inadmissible_NETs':[n for n in replace if not new[case,n]['all_connections_within_budget']]};p=D/(case+'.json');p.write_text(json.dumps(out,indent=2)+'\n');rows.append({'case':case,'satisfiable':result['satisfiable'],'fixed_overload_channels':len(hard),'clauses':len(clauses),'D_inadmissible_NETs':out['D_inadmissible_NETs'],'result_file':str(p)});print('CD CAPACITY',json.dumps(rows[-1]),flush=True)
assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps({'rows':rows,'seconds':time.perf_counter()-start,'bindings':bindings,'scope':'All positive CHANNELs, fixed complete C/D pair per extended NET, frozen A/B per unextended NET. Budget-failing D disabled. Exact2SAT or fixed-overload witness; independently audit before scientific admission. No general routing infeasibility or gain claim.'},indent=2)+'\n')
