"""Independent Fraction critical path and previously certified physical minima parity."""
import json
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict,deque
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/fresh_critical_owner_discovery_v1_2026-10-08';rp=D/'receipt.json';r=json.loads(rp.read_text());assert all(sha(p)==h for p,h in r['bindings'].items())
bp=R/'experiments/fresh_native_budget_repairs_v1_2026-10-08/verification.json';b=json.loads(bp.read_text());assert all(sha(p)==h for p,h in b['bindings'].items());delay={x['connection_id']:F(x['delay_seconds']) for x in b['rows']}
tg=json.loads((R/'experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json').read_text());mapping=json.loads((R/'experiments/mux_full_timing_rr_2026-10-06/w32.json').read_text());allocation=json.loads((R/'experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json').read_text());edges={eid:e for eid,e in tg['edges'].items() if not e['disabled']};adj=defaultdict(list);degree={int(n):0 for n in tg['nodes']};weights={}
for eid,e in edges.items():
 adj[e['source']].append((e['sink'],eid));degree[e['sink']]+=1
 weights[eid]=delay[allocation['edge_connection_ids'][eid]]+F(mapping['external_edges'][eid]['old_local_offset_seconds']) if eid in allocation['edge_connection_ids'] else F(e['max_delay_seconds'])
queue=deque(n for n,v in degree.items() if not v);order=[]
while queue:
 u=queue.popleft();order.append(u)
 for v,eid in adj[u]:
  degree[v]-=1
  if not degree[v]:queue.append(v)
assert len(order)==len(degree);forward={n:F(0) for n in order}
for u in order:
 for v,eid in adj[u]:forward[v]=max(forward[v],forward[u]+weights[eid])
for eid,e in edges.items():assert forward[e['sink']]>=forward[e['source']]+weights[eid]
cpd=max(forward[int(n)] for n,k in tg['nodes'].items() if k=='SINK');path=r['critical_timing_edge_ids'];assert sum(weights[eid] for eid in path)==cpd and F(r['model_cpd_ns'])==cpd*10**9
assert all(edges[a]['sink']==edges[b]['source'] for a,b in zip(path,path[1:])) and tg['nodes'][str(edges[path[-1]]['sink'])]=='SINK'
selected=sorted({allocation['edge_connection_ids'][eid] for eid in path if eid in allocation['edge_connection_ids']});assert selected==r['selected_connections']
O=R/'experiments/critical_branch_constraint_ablation_v1_2026-10-08';op=O/'receipt.json';ov=O/'verification.json';old=json.loads(op.read_text());cert=json.loads(ov.read_text());assert cert['all_twelve_constraint_ablation_certificates_pass'] and cert['receipt_sha256']==sha(op) and all(sha(p)==h for p,h in old['bindings'].items());prior={(e['connection_id'],e['scenario']):e for e in old['events']}
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2);meta=json.loads(Path(case['target']).read_text());queries={q['connection_id']:q for q in meta['connections']};state=json.loads(bp.with_name('receipt.json').read_text())['state'];unions=defaultdict(set)
for cid,branch in state.items():unions[queries[int(cid)]['net_id']].update(n for n,s in branch)
from immutable_xml_prediction_audit import ImmutableXMLAudit
xml=ImmutableXMLAudit(Path(meta['inputs']['graph']['path']),meta['graph_sha256']);assert len(r['events'])==2*len(selected)
for e in r['events']:
 ref=prior[e['connection_id'],e['scenario']];answer=e['search'];assert answer['status']=='FOUND' and answer['physical_edge_ids']==ref['physical_edge_ids'] and answer['delay']==ref['delay_integer'] and answer['cost']==0
 net=queries[e['connection_id']]['net_id'];outside={n:sum(n in used for owner,used in unions.items() if owner!=net) for n in {n for ns in unions.values() for n in ns}};blockers={}
 for eid in answer['physical_edge_ids']:
  dest=xml.graph.edges[eid].sink
  if outside.get(dest,0)>=xml.graph.nodes[dest].capacity:blockers[str(dest)]=sorted(owner for owner,used in unions.items() if owner!=net and dest in used)
 assert blockers==e['blocking_nodes'] and sorted({owner for owners in blockers.values() for owner in owners})==e['blocking_net_ids']
 if e['scenario']=='FULL_CONSTRAINTS':assert not blockers
bindings={**r['bindings'],**old['bindings'],str(rp):sha(rp),str(bp):sha(bp),str(op):sha(op),str(ov):sha(ov),str(Path(__file__)):sha(Path(__file__))};assert all(sha(p)==h for p,h in bindings.items())
out=dict(bindings=bindings,independent_full_fraction_cpd_and_attaining_path_pass=True,all_selected_full_and_relaxed_minimum_paths_equal_prior_certified_witnesses=True,all_blocking_node_owner_sets_reconstructed=True,selected_connections=selected,model_cpd_ns=str(cpd*10**9),component_elapsed_seconds=r['component_elapsed_seconds'],scope='Historical references consumed only by verifier. Relaxed witnesses remain hypothetical, blockers from one path are not minimum release set; owner transactions and native/QoR/end-to-end evaluation pending.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'},flush=True)
