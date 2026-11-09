"""Independent partial XML audit and necessity minima for first joint conflict."""
import sys,json,heapq
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from immutable_xml_prediction_audit import ImmutableXMLAudit
out=R/'experiments/misex_joint_constraints_v1_2026-10-07';base=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');bindings={**p['inputs'],**p['sources'],**r['files'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json')};assert all(sha(k)==v for k,v in bindings.items());(out/'verification_v4_protocol.json').write_text(json.dumps(dict(bindings=bindings))+'\n');graph,digest,nodes,f,rc,queries=load_endpoints(base/'endpoints.json');ep=json.loads((base/'endpoints.json').read_text());a=ImmutableXMLAudit(graph,digest);rows=[]
for file in sorted(out.glob('branch*/net*.json')):
 c=json.loads(file.read_text());records={q['connection_id']:q for q in c['records']};parents=defaultdict(dict)
 for rec in c['records']:
  assert rc.path(rec['source'],rec['sink'],rec['answer']['physical_edge_ids'])==rec['answer']['delay']<=rec['budget_integer'];u=rec['source']
  for e in rec['answer']['physical_edge_ids']:
   edge=a.graph.edges[e];assert edge.source==u;incoming=(u,e);u=edge.sink;assert u not in parents[rec['net_id']] or parents[rec['net_id']][u]==incoming;parents[rec['net_id']][u]=incoming
 connections=[dict(q,method='searched' if q['connection_id'] in records else 'failed',physical_edge_ids=records[q['connection_id']]['answer']['physical_edge_ids'] if q['connection_id'] in records else None) for q in queries];adapted=dict(connections=connections,physical_graph_sha256=digest,node_occupancy={str(k):v for k,v in c['ledger'].items()},methods=dict(Counter(q['method'] for q in connections)),completed=len(records),requested=len(queries));audit=a.verify(ep,adapted);assert audit['all_physical_and_union_checks_passed'] and audit['all_type_overuse_units']==0;rows.append(dict(file=str(file),completed=len(records),xml_rc_parents_capacity_pass=True));print('PASS',file.name,file.parent.name,flush=True)
event=json.loads(Path(next(k for k in p['inputs'] if k.endswith('batch5.json'))).read_text());kept=[q for q in event['before_records'] if q['net_id'] not in set(event['released_net_ids'])];slots={e:s for s,e in enumerate(f['edge_ids'])};owners=defaultdict(set)
for rec in kept:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
reverse=[[] for _ in nodes]
for u in range(len(nodes)):
 for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):reverse[f['dest_ranks'][s]].append((u,s))
node=r['branches'][0]['conflict_node'];assert node==22430 and f['capacities'][node]==1
minima=[]
for q in [event['batch_failure']['query'],event['query']]:
 ledger=Counter(n for net,own in owners.items() if net!=q['net_id'] for n in own)
 for mode,banned in [('fixed_owners',False),('fixed_owners',True),('unrestricted',True)]:
  if mode=='unrestricted':ledger=Counter()
  allowed=lambda n:f['capacities'][n]>ledger.get(n,0) and not(banned and n==node)
  results=[];forward_path=None
  for backward in (False,True):
   root=q['sink'] if backward else q['source'];target=q['source'] if backward else q['sink'];dist={root:0 if backward else rc.initial(root)} if allowed(root) else {};heap=[(d,u) for u,d in dist.items()];result=None;back={}
   while heap:
    d,u=heapq.heappop(heap)
    if d!=dist[u]:continue
    if u==target:result=d+(rc.initial(target) if backward else 0);break
    arcs=reverse[u] if backward else ((f['dest_ranks'][s],s) for s in range(f['row_offsets'][u],f['row_offsets'][u+1]))
    for v,s in arcs:
     if not allowed(v):continue
     nd=d+rc.increments[s]
     if v not in dist or nd<dist[v]:dist[v]=nd;back[v]=(u,f['edge_ids'][s]);heapq.heappush(heap,(nd,v))
   if not backward and result is not None:
    forward_path=[];v=q['sink']
    while v!=q['source']:v,e=back[v];forward_path.append(e)
    forward_path.reverse();assert rc.path(q['source'],q['sink'],forward_path)==result
   results.append(result)
  assert results[0]==results[1];floor=json.loads((out/'branch0'/f"net{q['net_id']}.json").read_text());rec=next(x for x in floor['records'] if x['connection_id']==q['connection_id']);budget=rec['budget_integer'];used={q['source']}|set(f['dest_ranks'][slots[e]] for e in (forward_path or []));fixed=Counter(n for net,own in owners.items() if net!=q['net_id'] for n in own);saturated={n for n in used if fixed[n]>=f['capacities'][n]};blockers=sorted(net for net,own in owners.items() if net!=q['net_id'] and own.intersection(saturated));minima.append(dict(physical_edge_ids=forward_path,other_owner_blockers=blockers,net_id=q['net_id'],query=q,capacity_condition=mode,node_banned=banned,minimum_integer=results[0],budget_integer=budget,within_budget=results[0] is not None and results[0]<=budget,forward_reverse_equal=True));print('minimum',q['net_id'],banned,results[0],budget,flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'verification_v4.json').write_text(json.dumps(dict(bindings=bindings,partial_states=rows,capacity_node=node,capacity=1,scale=rc.scale,minima=minima,scope='Lower bounds ignore retained-tree constraints and same-NET own restrictions; external owners fixed. Not native/global impossibility.'),indent=2)+'\n')
