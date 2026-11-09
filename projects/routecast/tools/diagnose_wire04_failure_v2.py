"""Original input versus ordinary-capacity versus tree-constrained failure."""
import sys,json,heapq
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from nonzero_rc_endpoint_context import load_endpoints
from owner_joint_repair_v1 import constrained_witness
from source_binding_v2 import closure
from pre_route_endpoints import sha
parent=R/'experiments/mcnc_prefix_wire04_v11_2026-10-07';base=R/'experiments/mcnc_prospective_v1_2026-10-07/bigkey';out=R/'experiments/wire04_bigkey_failure_diagnostic_v2_2026-10-07';out.mkdir();eventfile=parent/'bigkey/batch2.json';ep=base/'endpoints.json';inputs={str(p):sha(p) for p in (eventfile,ep)};inputs.update({x['path']:x['sha256'] for x in json.loads(ep.read_text())['inputs'].values()});files=list((parent/'bigkey').glob('repair_batch2_attempt1_branch*/net*.json'))+list((parent/'bigkey').glob('repair_batch2_attempt1_branch*/branch.json'));inputs.update({str(p):sha(p) for p in files});bindings={**inputs,**closure([Path(__file__)])};(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Post-outcome ordinary-capacity minimum diagnostics, not complete tree/joint routability proof. No native route producer input.'))+'\n');graph,digest,nodes,f,rc,queries=load_endpoints(ep);slots={e:s for s,e in enumerate(f['edge_ids'])};event=json.loads(eventfile.read_text());rows=[];reverse=[[] for _ in nodes]
for u in range(len(nodes)):
 for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):reverse[f['dest_ranks'][slot]].append((u,slot))
def reverse_min(q,banned):
 if q['source'] in banned or q['sink'] in banned:return None
 dist={q['sink']:0};heap=[(0,q['sink'])]
 while heap:
  d,u=heapq.heappop(heap)
  if dist[u]!=d:continue
  if u==q['source']:return d+rc.initial(u)
  for v,slot in reverse[u]:
   if v in banned or f['capacities'][v]<=0:continue
   nd=d+rc.increments[slot]
   if v not in dist or nd<dist[v]:dist[v]=nd;heapq.heappush(heap,(nd,v))
 return None
for branch in event['repair_attempts']:
 for net,failure in branch['failures'].items():
  if failure is None:continue
  net=int(net);file=parent/'bigkey'/f"repair_batch2_attempt1_branch{branch['index']}"/f'net{net}.json';state=json.loads(file.read_text());owners=defaultdict(set)
  for rec in state['records']:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
  other=Counter(n for owner,used in owners.items() if owner!=net for n in used);forbidden={n for owner,n in branch['constraints'] if owner==net};saturated={n for n,count in other.items() if count>=f['capacities'][n]};q=failure['query'];original=constrained_witness(f,rc,q,frozenset());conditioned=constrained_witness(f,rc,q,frozenset(forbidden|saturated));budget=failure['budget_integer'];item=dict(branch=branch['index'],net=net,query=q,budget_integer=budget,tree_failure=failure,forbidden_nodes=sorted(forbidden),saturated_other_nodes=len(saturated),original=original,ordinary_capacity=conditioned,ordinary_capacity_budget_feasible=conditioned is not None and conditioned['minimum_integer']<=budget)
  for witness in (original,conditioned):
   if witness is not None:assert rc.path(q['source'],q['sink'],witness['physical_edge_ids'])==witness['minimum_integer']
  if conditioned is not None:assert not ({q['source']}|{f['dest_ranks'][slots[e]] for e in conditioned['physical_edge_ids']}).intersection(forbidden|saturated)
  assert reverse_min(q,set())==original['minimum_integer'];assert reverse_min(q,forbidden|saturated)==(None if conditioned is None else conditioned['minimum_integer']);item['independent_reverse_minima_pass']=True
  rows.append(item);print(net,item['ordinary_capacity_budget_feasible'],None if conditioned is None else conditioned['minimum_integer'],budget,flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Feasible ordinary path cannot certify compatibility with retained tree parents or multi-group solution; infeasible ordinary minimum does certify this fixed occupancy/prohibition has no budget path.'),indent=2)+'\n')
