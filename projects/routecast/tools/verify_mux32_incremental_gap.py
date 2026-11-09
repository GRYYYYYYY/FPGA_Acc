"""Independent backward longest paths for all five counterfactual vectors."""
import json
from collections import defaultdict,deque
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux32_incremental_gap_2026-10-07';p=out/'diagnosis.json';r=json.loads(p.read_text());assert all(sha(f)==h for f,h in r['bindings'].items())
load=lambda f:json.loads((ROOT/f).read_text())
c=load('experiments/owner50_retained_rr_2026-10-07_predictor/w32_m2/result.json')['result']['candidate'];s=load('experiments/mux_full_cohort_cold_lifecycle_2026-10-06/mux_w32_m2_0/accepted_state.json');g=load('experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json');m=load('experiments/mux_full_timing_rr_2026-10-06/w32.json');a=load('experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json')
inc={str(q['connection_id']):F(q['answer']['delay']*10**9,c['scale']) for q in c['records']};cold={str(q['connection_id']):F(q['answer']['delay']*10**9,s['scale']) for q in s['records']};old={str(cid):F(m['external_edges'][eid]['branch']['rr_delay_seconds'])*10**9 for eid,cid in a['edge_connection_ids'].items()};affected=set(map(str,c['affected']['affected_complete_net_connection_ids']))
adj=defaultdict(list);ind={int(n):0 for n in g['nodes']}
for eid,e in g['edges'].items():
 if not e['disabled']:adj[e['source']].append((e['sink'],eid));ind[e['sink']]+=1
queue=deque(n for n in ind if not ind[n]);order=[]
while queue:
 u=queue.popleft();order.append(u)
 for v,eid in adj[u]:
  ind[v]-=1
  if not ind[v]:queue.append(v)
assert len(order)==len(ind)
for row in r['rows']:
 name=row['vector'];values=old if name=='published_old' else cold if name=='cold' else inc if name=='incremental' else {k:(cold[k] if ((k in affected)==(name=='incremental_with_cold_affected')) else inc[k]) for k in inc}
 tail={n:F(0) for n in order}
 for u in reversed(order):
  for v,eid in adj[u]:
   cid=a['edge_connection_ids'].get(eid);delay=(values[str(cid)]+F(m['external_edges'][eid]['old_local_offset_seconds'])*10**9) if cid is not None else F(g['edges'][eid]['max_delay_seconds'])*10**9
   tail[u]=max(tail[u],delay+tail[v])
 assert max(tail.values())==F(row['model_cpd_ns'])
critical=r['rows'][1]['critical_external_connections'];assert [x['connection_id'] for x in critical]==['763','812','817']
excess=F(r['rows'][1]['model_cpd_ns'])-F(r['rows'][0]['model_cpd_ns']);cap=inc['763']-excess
result=dict(source_sha256=sha(Path(__file__)),diagnosis_sha256=sha(p),backward_vectors_verified=5,incremental_excess_over_published_ns=str(excess),connection_763_current_ns=str(inc['763']),connection_763_necessary_cap_if_other_delays_fixed_ns=str(cap),scope='Critical-path necessary cap only, not sufficient across all paths or proof of feasible physical route. Counterfactual cold delays evaluator-only; no executable hybrid or native guarantee.')
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
