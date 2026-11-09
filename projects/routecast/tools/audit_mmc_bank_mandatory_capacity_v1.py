"""Independent original-frame/RR-path capacity witnesses and exhaustive cover audit."""
import json,itertools,time,xml.parsers.expat as X
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_bank_mandatory_capacity_v1_2026-10-21';P=D/'verification.json';v=json.loads(P.read_text());assert all(sha(p)==h for p,h in v['bindings'].items())
start=time.perf_counter();cases=[];wanted=set();terminals=set();witness_nodes=set();graph=None
for row in v['rows']:
 ep=json.loads(Path(row['endpoint']).read_text());g=Path(ep['inputs']['graph']['path'])
 if graph is None:graph=g;graph_hash=ep['graph_sha256']
 assert g==graph and ep['graph_sha256']==graph_hash
 nets={net for w in row['witnesses'] for net in w['NETs']};witness_nodes.update(w['node'] for w in row['witnesses']);queries={q['connection_id']:q for q in ep['connections'] if q['net_id'] in nets};arms={}
 for arm,path in row['frames'].items():
  frame=json.loads(Path(path).read_text());records=[r for r in frame['records'] if r['net_id'] in nets];assert len(records)==len(queries) and {r['connection_id'] for r in records}==set(queries)
  for r in records:
   assert all(r[k]==queries[r['connection_id']][k] for k in ['net_id','source','sink']);wanted.update(r['answer']['physical_edge_ids']);terminals.update([r['source'],r['sink']])
  arms[arm]=records
 cases.append((row,arms))
assert sha(graph)==graph_hash;arcs={};node_info={};edge_index=0;stack=[]
def begin(name,a):
 global edge_index
 parent=stack[-1] if stack else None;stack.append(name)
 if name=='node' and parent=='rr_nodes':
  n=int(a['id'])
  if n in witness_nodes or n in terminals:node_info[n]=(a['type'],int(a['capacity']))
 elif name=='edge' and parent=='rr_edges':
  if edge_index in wanted:arcs[edge_index]=(int(a['src_node']),int(a['sink_node']),int(a['switch_id']))
  edge_index+=1
def end(name):assert stack.pop()==name
parser=X.ParserCreate();parser.StartElementHandler=begin;parser.EndElementHandler=end
with graph.open('rb') as f:
 while block:=f.read(8*1024*1024):parser.Parse(block,False)
parser.Parse(b'',True);assert set(arcs)==wanted
out=[]
for row,arms in cases:
 owned={};path_count=0
 for arm,records in arms.items():
  unions=defaultdict(set);parents=defaultdict(dict)
  for r in records:
   net=r['net_id'];u=r['source'];assert node_info[u][0]=='SOURCE';seen={u};unions[net].add(u)
   for eid in r['answer']['physical_edge_ids']:
    src,dst,switch=arcs[eid];assert src==u and dst not in seen
    if dst in parents[net]:assert parents[net][dst]==(src,switch)
    parents[net][dst]=(src,switch);seen.add(dst);unions[net].add(dst);u=dst
   assert u==r['sink'] and node_info[u][0]=='SINK';path_count+=1
  owned[arm]=unions
 edges=set()
 for w in row['witnesses']:
  n=w['node'];assert node_info[n][0] in ['CHANX','CHANY'] and node_info[n][1]==w['capacity']==1
  assert len(set(w['NETs']))>w['capacity']
  for net in w['NETs']:assert n in owned['A'][net] and n in owned['B'][net]
  edges.update(itertools.combinations(sorted(set(w['NETs'])),2))
 checked_edges=set();checked_nets=set();minimum=0
 for part in row['owner_conflict_components']:
  ns=part['NETs'];es={tuple(e) for e in part['edges']};assert len(ns)<=24 and not checked_nets.intersection(ns);checked_nets.update(ns);checked_edges.update(es)
  assert es=={e for e in edges if e[0] in set(ns)}
  optimal=None
  for k in range(len(ns)+1):
   for choice in itertools.combinations(sorted(ns),k):
    chosen=set(choice)
    if all(chosen.intersection(e) for e in es):optimal=choice;break
   if optimal is not None:break
  assert list(optimal)==part['cover'] and len(optimal)==part['minimum_departures'];minimum+=len(optimal)
 assert checked_edges==edges and minimum==row['necessary_new_support_NETs_lower_bound']
 out.append({'case':row['case'],'mandatory_channel_witnesses_verified':len(row['witnesses']),'distinct_forced_NETs':len(checked_nets),'complete_physical_connection_paths_checked':path_count,'minimum_necessary_support_departures_verified':minimum,'full_native_or_RR_infeasibility_claim':False})
assert sha(graph)==graph_hash and all(sha(p)==h for p,h in v['bindings'].items())
result={'status':'ALL3_A_B_MANDATORY_CAPACITY_AND_EXHAUSTIVE_COVER_CERTIFICATES_PASS','rows':out,'RR_edges_streamed':edge_index,'selected_original_RR_arcs_verified':len(arcs),'seconds':time.perf_counter()-start,'bindings':{str(P):sha(P),str(Path(__file__)):sha(__file__),str(graph):graph_hash},'scope':'Every listed distinct NET is forced to own the same capacity1 channel in both supplied complete A/B trees. No A/B-only assignment can satisfy these channels. Cover bound is necessary for new support, not sufficient repair, timing-budget recertification, global RR infeasibility or prediction quality. All unlisted bank/path properties rely on their existing source proofs.'}
(D/'independent_verification_v1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:x for k,x in result.items() if k!='bindings'},indent=2),flush=True)
