"""Independent full-DAG safety proof for all single-connection prospective upper bounds."""
import json
from fractions import Fraction as F
from collections import defaultdict,deque
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/complete_wire_global_headroom_v1_2026-10-08';dp=D/'diagnosis.json';d=json.loads(dp.read_text());assert all(sha(p)==h for p,h in d['bindings'].items())
base=json.loads((R/'experiments/complete_wire_contraction_v2_2026-10-08/verification_v3.json').read_text());assert all(sha(p)==h for p,h in base['bindings'].items());values={str(x['connection_id']):F(x['delay_seconds']) for x in base['rows']}
tg=json.loads((R/'experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json').read_text());mapping=json.loads((R/'experiments/mux_full_timing_rr_2026-10-06/w32.json').read_text());allocation=json.loads((R/'experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json').read_text());budget=json.loads((R/'experiments/mux_connection_budgets_2026-10-06/w32.json').read_text());edges={eid:e for eid,e in tg['edges'].items() if not e['disabled']};adj=defaultdict(list);ind={int(n):0 for n in tg['nodes']};groups=defaultdict(set);weights={}
for eid,e in edges.items():
 adj[e['source']].append((e['sink'],eid));ind[e['sink']]+=1
 if eid in allocation['edge_connection_ids']:
  cid=str(allocation['edge_connection_ids'][eid]);groups[cid].add(eid);weights[eid]=values[cid]+F(mapping['external_edges'][eid]['old_local_offset_seconds'])
 else:weights[eid]=F(e['max_delay_seconds'])
q=deque(n for n,v in ind.items() if not v);order=[]
while q:
 u=q.popleft();order.append(u)
 for dest,eid in adj[u]:
  ind[dest]-=1
  if not ind[dest]:q.append(dest)
assert len(order)==len(ind);terminals={int(n) for n,k in tg['nodes'].items() if k=='SINK'};forward={int(n):F(t) for n,t in d['forward_seconds'].items()};back={int(n):None if t is None else F(t) for n,t in d['back_seconds'].items()};assert set(forward)==set(back)==set(order) and all(t>=0 for t in forward.values())
for n in terminals:assert back[n] is not None and back[n]>=0
for eid,e in edges.items():
 assert forward[e['sink']]>=forward[e['source']]+weights[eid]
 if back[e['sink']] is not None:assert back[e['source']] is not None and back[e['source']]>=weights[eid]+back[e['sink']]
target=F(d['target_model_cpd_ns'])/10**9;assert max(forward[n] for n in terminals)<=target and max(forward[n] for n in terminals)*10**9==F(d['current_model_cpd_ns'])
assert len(d['rows'])==len(values)==1929 and {str(x['connection_id']) for x in d['rows']}==set(values)
positive=0;checks=0;rejected=[]
for x in d['rows']:
 cid=str(x['connection_id']);old=values[cid];original=F(budget['budgets_ns'].get(cid,budget['default_budget_ns']))/10**9;assert F(x['current_delay_seconds'])==old
 if old>original:assert x['status']=='ORIGINAL_BUDGET_INFEASIBLE_RETAIN';rejected.append(int(cid));continue
 assert x['status']=='FIXED_MODEL_BOUND_COMPUTED';upper=F(x['safe_upper_seconds']);assert old<=upper<=original and upper-old==F(x['allowed_increase_seconds']);count={n:0 for n in order}
 for u in order:
  for dest,eid in adj[u]:count[dest]=max(count[dest],count[u]+int(eid in groups[cid]))
 k=max(count[n] for n in terminals);assert k==x['max_occurrences_per_model_path']
 relevant=[eid for eid in groups[cid] if back[edges[eid]['sink']] is not None]
 if relevant:
  assert k>0;slack=min(target-forward[edges[eid]['source']]-weights[eid]-back[edges[eid]['sink']] for eid in relevant);assert slack>=0 and slack==F(x['min_edge_slack_seconds']);assert upper==min(original,old+slack/k)
  # For any sink path containing k'<=k query edges: each edge slack<=path slack,
  # so k'*(upper-old)<=k*(upper-old)<=min edge slack<=path slack.
  assert k*(upper-old)<=slack;checks+=len(relevant)
 else:assert k==0 and upper==original
 if upper>old:positive+=1
assert rejected==[785,1637] and positive==d['positive_safe_increase_connections']==1927 and all(sha(p)==h for p,h in d['bindings'].items())
report=dict(diagnosis_sha256=sha(dp),verifier_sha256=sha(Path(__file__)),all1929_single_connection_bound_certificates_pass=True,positive_safe_increase_connections=positive,rejected_original_budget_connection_ids=rejected,covered_query_edge_slack_checks=checks,scope='Certified single-query bound only on fixed-old-local DAG. Bounds cannot be applied jointly without recalculating current forward/back/slack/multiplicity; no native STA equivalence, changed budgets or candidate publication.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS all1929 single-query bounds, safe increase',positive,'original failures',rejected)
