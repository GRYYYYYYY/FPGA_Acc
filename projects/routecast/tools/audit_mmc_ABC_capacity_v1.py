"""Original-frame/RR path replay of C-forcing and fixed-overload UNSAT cores."""
import json,time,xml.parsers.expat as X
from pathlib import Path
from collections import defaultdict
from array import array
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_ABC_capacity_v1_2026-10-21';P=D/'verification.json';v=json.loads(P.read_text());assert all(sha(p)==h for key in ['bindings','files'] for p,h in v[key].items())
OP=R/'experiments/mmc_bank_mandatory_capacity_v1_2026-10-21/verification.json';old=json.loads(OP.read_text());oldcases={r['case']:r for r in old['rows']};CP=R/'experiments/mmc_cover_budget_avoidance_v1_2026-10-21/complete_C_alternatives.jsonl';C=defaultdict(dict)
for r in map(json.loads,CP.open()):C[r['case']][r['net_id']]=r['records']
wanted=set();documents=[];bindings={str(P):sha(P),str(OP):sha(OP),str(CP):sha(CP),str(Path(__file__)):sha(__file__)};start=time.perf_counter();graph=None
for item in v['rows']:
 s=json.loads(Path(item['result_file']).read_text());case=s['case'];assert s['result']['satisfiable'] is False and s['result']['reason']=='FIXED_OWNER_OVERLOAD' and s['hard_overloads'];nets={r['net_id'] for w in s['hard_overloads'] for r in w['owners']}|{x['net_id'] for x in s['forced_C']}|{x['unextended_NET'] for x in s['forced_C']};arms={}
 ep=json.loads(Path(oldcases[case]['endpoint']).read_text());queries={q['connection_id']:q for q in ep['connections'] if q['net_id'] in nets};g=Path(ep['inputs']['graph']['path'])
 if graph is None:graph=g;graph_hash=ep['graph_sha256']
 assert g==graph and ep['graph_sha256']==graph_hash
 for arm,path in oldcases[case]['frames'].items():
  assert old['bindings'][path]==sha(path);bindings[path]=sha(path);frame=json.loads(Path(path).read_text());records=[r for r in frame['records'] if r['net_id'] in nets];assert len(records)==len(queries) and {r['connection_id'] for r in records}==set(queries);arms[arm]=records
 arms['C']=[r for rs in C[case].values() for r in rs]
 for arm,records in arms.items():
  for r in records:
   assert all(r[k]==queries[r['connection_id']][k] for k in ['net_id','source','sink']);wanted.update(r['answer']['physical_edge_ids'])
 documents.append((s,arms))
assert sha(graph)==graph_hash;bindings[str(graph)]=graph_hash
caps=array('I');kinds=[];arcs={};stack=[];eid=0
def begin(name,a):
 global eid
 parent=stack[-1] if stack else None;stack.append(name)
 if name=='node' and parent=='rr_nodes':assert int(a['id'])==len(caps);caps.append(int(a['capacity']));kinds.append(a['type'])
 elif name=='edge' and parent=='rr_edges':
  if eid in wanted:arcs[eid]=(int(a['src_node']),int(a['sink_node']),int(a['switch_id']))
  eid+=1
def end(name):assert stack.pop()==name
parser=X.ParserCreate();parser.StartElementHandler=begin;parser.EndElementHandler=end
with graph.open('rb') as f:
 while block:=f.read(8*1024*1024):parser.Parse(block,False)
parser.Parse(b'',True);assert set(arcs)==wanted;rows=[]
for s,arms in documents:
 unions={};paths=0
 for arm,records in arms.items():
  owned=defaultdict(set);parents=defaultdict(dict)
  for r in records:
   net=r['net_id'];node=r['source'];assert kinds[node]=='SOURCE' and caps[node]>0;seen={node};owned[net].add(node)
   for e in r['answer']['physical_edge_ids']:
    a,b,sw=arcs[e];assert node==a and b not in seen and caps[b]>0
    if b in parents[net]:assert parents[net][b]==(a,sw)
    parents[net][b]=(a,sw);owned[net].add(b);seen.add(b);node=b
   assert node==r['sink'] and kinds[node]=='SINK';paths+=1
  unions[arm]=owned
 case=s['case'];chosen=set(C[case]);assert {x['net_id'] for x in s['forced_C']}==chosen;forced=set()
 for x in s['forced_C']:
  net,other,n=x['net_id'],x['unextended_NET'],x['channel'];assert other not in chosen and caps[n]==1 and kinds[n] in ['CHANX','CHANY']
  assert n in unions['A'][net]&unions['B'][net]&unions['A'][other]&unions['B'][other] and n not in unions['C'][net];forced.add(net)
  # Other has no C alternative; capacity forbids A or B for this NET.
 hist=defaultdict(int)
 for w in s['hard_overloads']:
  n=w['node'];assert caps[n]==w['capacity']==1 and kinds[n] in ['CHANX','CHANY'];owners=w['owners'];assert len({o['net_id'] for o in owners})==len(owners)>caps[n]
  variants=[]
  for o in owners:
   net=o['net_id'];variants.append(o['variant'])
   if o['variant']=='C':assert net in forced and n in unions['C'][net]
   else:assert o['variant']=='AB' and net not in chosen and n in unions['A'][net]&unions['B'][net]
  hist['+'.join(sorted(variants))]+=1
 rows.append({'case':case,'all_C_forcing_witnesses_verified':len(forced),'all_fixed_overload_witnesses_verified':len(s['hard_overloads']),'overload_variant_patterns':dict(hist),'complete_connection_paths_replayed':paths,'supplied_ABC_library_UNSAT':True,'global_RR_infeasibility_claim':False})
 print('INDEPENDENT ABC UNSAT',json.dumps(rows[-1]),flush=True)
assert all(sha(p)==h for key in ['bindings','files'] for p,h in v[key].items()) and all(sha(p)==h for p,h in bindings.items())
result={'status':'ALL3_EXPANDED_ABC_LIBRARIES_UNSAT_BY_ORIGINAL_PATH_FORCING_AND_CAPACITY_CORES','rows':rows,'original_XML_edges_streamed':eid,'selected_original_arcs_replayed':len(arcs),'seconds':time.perf_counter()-start,'bindings':bindings,'scope':'Any choices in the supplied complete A/B/C libraries force all C trees by old capacity witnesses, then violate new capacity1 channels. Does not rule out other C trees, additional NET alternatives, different covers or full RR/native routing. No target labels or prediction/quality gain.'}
(D/'independent_verification_v1.json').write_text(json.dumps(result,indent=2)+'\n');print('ALL3 ABC UNSAT CORES INDEPENDENTLY_VERIFIED',flush=True)
