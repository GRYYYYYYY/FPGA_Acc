"""Independent layered all-arc certificate and net-union cut capacity proof."""
import sys,json,struct
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net466_cut_visit_demand_v1_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());domains=R/'experiments/misex_net466_first_channel_domains_v2_2026-10-07';verified=json.loads((domains/'verification.json').read_text());assert all(sha(k)==h for k,h in verified['bindings'].items());dr=json.loads((domains/'receipt.json').read_text());assert r['release']==sorted(dr['release']);hr=json.loads((R/'experiments/misex_net466_extra_owner_joint_v17_2026-10-07/receipt.json').read_text());cut=sorted({int(n) for b in hr['attempts'][0]['branches'][-4:] for n in b['overuse_by_node']});assert cut==r['cut_nodes'];_,_,nodes,f,rc,_=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');slots={edge:i for i,edge in enumerate(f['edge_ids'])};e=json.loads((R/'experiments/misex_net466_extra_owner_joint_v13_2026-10-07/event.json').read_text());owners=defaultdict(set)
for rec in e['before_records']:
 if rec['net_id'] not in r['release']:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[edge]] for edge in rec['answer']['physical_edge_ids'])
occupancy=Counter(n for own in owners.values() for n in own);allowed=bytes(f['capacities'][n]>occupancy[n] for n in range(len(nodes)));assert allowed==(out/'allowed.bin').read_bytes();source_rows={row['query']['connection_id']:row for row in dr['rows']};assert {row['query']['connection_id'] for row in r['rows']}==set(source_rows);INF=(1<<64)-1;cutset=set(cut);checks=0;demand=defaultdict(int)
for row in r['rows']:
 q=row['query'];original=source_rows[q['connection_id']];assert q==original['query'] and row['budget']==original['budget'];assert q['source'] not in cutset and q['sink'] not in cutset;p=Path(row['certificate_file']);assert sha(p)==row['certificate_sha256'];raw=p.read_bytes();assert len(raw)==8*len(nodes)*(len(cut)+1);layers=[struct.unpack_from('<'+str(len(nodes))+'Q',raw,8*len(nodes)*i) for i in range(len(cut)+1)]
 for i,d in enumerate(layers):
  assert d[q['sink']]==0 if allowed[q['sink']] else all(v==INF for v in d)
  for u in range(len(nodes)):
   if not allowed[u]:assert d[u]==INF;continue
   for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][edge];visits=int(v in cutset)
    if not allowed[v] or visits>i:continue
    target=layers[i-visits][v]
    if target!=INF:assert d[u]!=INF and d[u]<=rc.increments[edge]+target;checks+=1
 costs=[None if d[q['source']]==INF else rc.initial(q['source'])+d[q['source']] for d in layers];assert costs==row['minimum_delays_by_allowed_visits'];required=next((i for i,c in enumerate(costs) if c is not None and c<=row['budget']),len(cut)+1);assert required==row['minimum_required_cut_visits'];demand[q['net_id']]=max(demand[q['net_id']],required)
capacity=sum(f['capacities'][n]-occupancy[n] for n in cut);assert {str(net):count for net,count in demand.items()}==r['minimum_node_units_by_net'];assert sum(demand.values())==r['minimum_total_node_units'] and capacity==r['residual_node_units'];assert r['necessary_capacity_violation']==(sum(demand.values())>capacity);assert all(sha(k)==h for k,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,queries_verified=len(r['rows']),layered_all_arc_checks=checks,minimum_total_node_units=sum(demand.values()),residual_node_units=capacity,necessary_capacity_violation_verified=r['necessary_capacity_violation'],scope='Sound layered reverse lower bounds on simple-path distinct cut use; max per NET, fixed kept and original budgets. No violation is inconclusive; model proof is not native/global or workflow gain.'),indent=2)+'\n');print('PASS cut demand',len(r['rows']),checks,sum(demand.values()),capacity,r['necessary_capacity_violation'])
