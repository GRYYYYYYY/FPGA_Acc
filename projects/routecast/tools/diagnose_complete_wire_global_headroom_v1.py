"""Conservative single-query RC headroom under fixed-local full-DAG global CPD guard."""
import json
from fractions import Fraction as F
from collections import defaultdict,deque
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];S=R/'experiments/complete_wire_contraction_v2_2026-10-08';vp=S/'verification_v3.json';v=json.loads(vp.read_text());assert v['all1929_events_and_complete_original_xml_fraction_frame_pass'] and all(sha(p)==h for p,h in v['bindings'].items());delay={str(x['connection_id']):F(x['delay_seconds']) for x in v['rows']}
tgp=R/'experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json';mp=R/'experiments/mux_full_timing_rr_2026-10-06/w32.json';ap=R/'experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json';tg=json.loads(tgp.read_text());m=json.loads(mp.read_text());a=json.loads(ap.read_text());assert a['graph_sha256']==sha(tgp)==m['timing_graph_sha256'] and a['mapping_sha256']==sha(mp)
bp=R/'experiments/mux_connection_budgets_2026-10-06/w32.json';b=json.loads(bp.read_text());edges={eid:e for eid,e in tg['edges'].items() if not e['disabled']};adj=defaultdict(list);ind={int(n):0 for n in tg['nodes']};groups=defaultdict(list);weights={}
for eid,e in edges.items():
 adj[e['source']].append((e['sink'],eid));ind[e['sink']]+=1
 if eid in a['edge_connection_ids']:
  cid=str(a['edge_connection_ids'][eid]);weights[eid]=delay[cid]+F(m['external_edges'][eid]['old_local_offset_seconds']);groups[cid].append(eid)
 else:weights[eid]=F(e['max_delay_seconds'])
q=deque(n for n,d in ind.items() if not d);order=[]
while q:
 u=q.popleft();order.append(u)
 for dest,eid in adj[u]:
  ind[dest]-=1
  if not ind[dest]:q.append(dest)
assert len(order)==len(ind);forward={n:F(0) for n in order};terminals={int(n) for n,k in tg['nodes'].items() if k=='SINK'}
for u in order:
 for dest,eid in adj[u]:forward[dest]=max(forward[dest],forward[u]+weights[eid])
back={n:F(0) if n in terminals else None for n in order}
for u in reversed(order):
 for dest,eid in adj[u]:
  if back[dest] is not None:back[u]=max(back[u] if back[u] is not None else weights[eid]+back[dest],weights[eid]+back[dest])
target=F('2.87238')/10**9;cpd=max(forward[n] for n in terminals);assert cpd<=target
rows=[]
for cid,old in sorted(delay.items(),key=lambda x:int(x[0])):
 budget=F(b['budgets_ns'].get(cid,b['default_budget_ns']))/10**9
 if old>budget:rows.append(dict(connection_id=int(cid),status='ORIGINAL_BUDGET_INFEASIBLE_RETAIN',current_delay_seconds=str(old)));continue
 represented=[eid for eid in groups[cid] if back[edges[eid]['sink']] is not None]
 if represented:
  count={n:0 for n in order}
  for u in order:
   for dest,eid in adj[u]:count[dest]=max(count[dest],count[u]+int(eid in groups[cid]))
  multiplicity=max(count[n] for n in terminals);assert multiplicity>0
  slack=min(target-forward[edges[eid]['source']]-weights[eid]-back[edges[eid]['sink']] for eid in represented);assert slack>=0
  upper=min(budget,old+slack/multiplicity)
 else:multiplicity=0;slack=None;upper=budget
 assert old<=upper<=budget;rows.append(dict(connection_id=int(cid),status='FIXED_MODEL_BOUND_COMPUTED',current_delay_seconds=str(old),original_budget_seconds=str(budget),safe_upper_seconds=str(upper),allowed_increase_seconds=str(upper-old),max_occurrences_per_model_path=multiplicity,min_edge_slack_seconds=str(slack) if slack is not None else None))
D=R/'experiments/complete_wire_global_headroom_v1_2026-10-08';D.mkdir(exist_ok=False);bindings={**v['bindings'],str(vp):sha(vp),**{str(p):sha(p) for p in (tgp,mp,ap,bp,Path(__file__))}};assert all(sha(p)==h for p,h in bindings.items())
report=dict(bindings=bindings,connections=1929,target_model_cpd_ns='2.87238',current_model_cpd_ns=str(cpd*10**9),positive_safe_increase_connections=sum(x.get('allowed_increase_seconds','0')!='0' for x in rows),rows=rows,forward_seconds={str(n):str(t) for n,t in forward.items()},back_seconds={str(n):str(t) if t is not None else None for n,t in back.items()},scope='Single-connection conservative safe bound in fixed-old-local full-DAG model only; bounds cannot be applied simultaneously without recomputation, not new original budgets or native STA guarantee. Independent bound certification pending.')
(D/'diagnosis.json').write_text(json.dumps(report,indent=2)+'\n');print('model CPD',float(cpd*10**9),'single-query safe increase opportunities',report['positive_safe_increase_connections'])
