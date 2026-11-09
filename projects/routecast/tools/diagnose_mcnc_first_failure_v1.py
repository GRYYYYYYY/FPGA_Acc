"""Post-outcome diagnosis only: exact scalar floor, owner cuts, tree conflict."""
import json,sys,heapq,time
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from source_binding_v2 import closure
from native_route_ledger_import_compact import physical_paths
base=R/'experiments/mcnc_prospective_v1_2026-10-07';out=R/'experiments/mcnc_first_failure_diagnosis_v1_2026-10-07';out.mkdir();inputs={};sources=closure([Path(__file__)])
for name in ('bigkey','dsip','misex3'):
 w=base/name
 for file in ('endpoints.json','candidate.json','design.route','rr_graph.xml'):inputs[str(w/file)]=sha(w/file)
protocol=dict(inputs=inputs,sources=sources,cases=['bigkey','dsip','misex3'],queries='Exactly each archived first failure; all retained, no retuning',search='Independent Python exact integer scalar Dijkstra; unrestricted positive-capacity graph and frozen other whole-NET owner occupancy; no label cutoff. Same additive buffered RC lattice, no native loaded tree delay equivalence claim.',scope='Post-outcome development diagnosis. Cannot strengthen original prospective protocol or claim heldout success. Native path inspected only after candidate production.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for name in protocol['cases']:
 w=base/name;start=time.perf_counter();c=json.loads((w/'candidate.json').read_text());q=c['failure']['query'];graph,digest,nodes,f,rc,queries=load_endpoints(w/'endpoints.json');assert rc.scale==c['scale'] and next(x for x in queries if x['connection_id']==q['connection_id'])==q
 slot_by_eid={eid:s for s,eid in enumerate(f['edge_ids'])};arc={};owners=defaultdict(set);parents=defaultdict(dict)
 for u in range(len(nodes)):
  for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):arc[u,f['dest_ranks'][s],f['switch_ids'][s]]=s
 for r in c['records']:
  net=r['net_id'];u=r['source'];owners[net].add(u)
  for eid in r['answer']['physical_edge_ids']:
   s=slot_by_eid[eid];v=f['dest_ranks'][s];assert f['row_offsets'][u]<=s<f['row_offsets'][u+1];parent=(u,eid);assert v not in parents[net] or parents[net][v]==parent;parents[net][v]=parent;owners[net].add(v);u=v
  assert u==r['sink']
 occupancy=Counter(n for ns in owners.values() for n in ns);assert dict(occupancy)=={int(n):v for n,v in c['ledger'].items()}
 other=Counter(n for net,ns in owners.items() if net!=q['net_id'] for n in ns)
 def shortest(blocked):
  src,sink=q['source'],q['sink'];allowed=lambda n:f['capacities'][n]>blocked.get(n,0)
  if not allowed(src):return dict(minimum_integer=None,edge_ids=None,settled=0,source_blocked=True)
  dist={src:rc.initial(src)};back={};queue=[(dist[src],src)];settled=0
  while queue:
   delay,u=heapq.heappop(queue)
   if delay!=dist[u]:continue
   settled+=1
   if u==sink:
    path=[];v=sink
    while v!=src:v,eid=back[v];path.append(eid)
    path.reverse();assert rc.path(src,sink,path)==delay
    return dict(minimum_integer=delay,edge_ids=path,settled=settled,source_blocked=False)
   for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][s]
    if not allowed(v):continue
    nd=delay+rc.increments[s]
    if v not in dist or nd<dist[v]:dist[v]=nd;back[v]=(u,f['edge_ids'][s]);heapq.heappush(queue,(nd,v))
  return dict(minimum_integer=None,edge_ids=None,settled=settled,source_blocked=False)
 floors={mode:shortest(blocked) for mode,blocked in [('unrestricted',{}),('other_net_conditioned',other)]};budget=rc.scale//10**9
 for value in floors.values():value['minimum_ns']=None if value['minimum_integer'] is None else str(rc.seconds(value['minimum_integer']));value['within_original_1ns_budget']=value['minimum_integer'] is not None and value['minimum_integer']<=budget
 ep=json.loads((w/'endpoints.json').read_text());name_of_net=ep['net_names'][str(q['net_id'])];native=[p for p in physical_paths(w/'design.route')[name_of_net] if p[0][0]==q['source'] and p[-1][0]==q['sink']];assert len(native)==1;slots=[arc[u,v,sw] for (u,_),(v,sw) in zip(native[0],native[0][1:])];native_delay=rc.initial(q['source'])+sum(rc.increments[s] for s in slots)
 conflicts=[]
 if c['failure']['status']=='MULTI_PARENT_REJECTED':
  event=next(e for e in reversed(c['events']) if e['type']=='QUERY' and e['query']==q);answer=event['answer'];assert answer['status']=='FOUND';u=q['source']
  for eid in answer['physical_edge_ids']:
   s=slot_by_eid[eid];v=f['dest_ranks'][s];incoming=(u,eid)
   if v in parents[q['net_id']] and parents[q['net_id']][v]!=incoming:conflicts.append(dict(node=v,retained_parent=list(parents[q['net_id']][v]),new_parent=list(incoming)))
   u=v
  assert u==q['sink'] and [x['node'] for x in conflicts]==c['failure']['nodes'];assert rc.path(q['source'],q['sink'],answer['physical_edge_ids'])==answer['delay']<=budget
 row=dict(name=name,query=q,failure=c['failure'],scale=rc.scale,budget_integer=budget,floors=floors,native_path_additive_integer=native_delay,native_path_additive_ns=str(rc.seconds(native_delay)),tree_conflicts=conflicts,whole_net_owner_ledger_exact=True,diagnostic_seconds=time.perf_counter()-start);rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,{mode:(v['minimum_ns'],v['within_original_1ns_budget']) for mode,v in floors.items()},conflicts,flush=True)
assert all(sha(p)==h for p,h in {**inputs,**sources}.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
