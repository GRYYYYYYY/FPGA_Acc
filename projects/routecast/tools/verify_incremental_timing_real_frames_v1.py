"""Replay all real commits, compare affected propagation against full Fraction DAG."""
import json
from fractions import Fraction as F
from pathlib import Path
from exact_integer_global_timing_v3 import ExactGlobalTiming
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'raw_route_incremental_timing_candidate_v1_2026-10-08'
rp=D/'receipt.json';vp=D/'verification.json';r=json.loads(rp.read_text());v=json.loads(vp.read_text())
assert v['all1929_wire_events_answers_work_counts_and_full_state_equal']
bindings={**v['bindings'],str(rp):sha(rp),str(vp):sha(vp),str(Path(__file__)):sha(Path(__file__))}
frame=E/'fresh_critical_owner_transactions_v1_2026-10-08/plan0_complete_frame.json';bindings[str(frame)]=sha(frame)
delay={x['connection_id']:F(x['delay_seconds']) for x in json.loads(frame.read_text())['connections']}
paths=[E/'mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json',E/'mux_full_timing_rr_2026-10-06/w32.json',E/'mux_allfanin_budgets_2026-10-06/w32_m2.json']
for p in paths:bindings[str(p)]=sha(p)
tg,mapping,allocation=[json.loads(p.read_text()) for p in paths]
model=ExactGlobalTiming(tg,mapping,allocation,r['scale'],F('2.87238')/10**9,delay);frames=0;edgechecks=0
for event in [None,*[e for e in r['passes'][0]['events'] if e['status']=='COMMIT']]:
 if event is not None:
  cid=event['connection_id'];delay[cid]=F(event['new_delay_seconds']);model.update(cid,delay[cid])
 weights={eid:F(mapping['external_edges'][eid]['old_local_offset_seconds'])+delay[allocation['edge_connection_ids'][eid]] if eid in allocation['edge_connection_ids'] else F(e['max_delay_seconds']) for eid,e in model.edges.items()}
 forward={n:F(0) for n in model.order}
 for u in model.order:
  for v,eid in model.adj[u]:forward[v]=max(forward[v],forward[u]+weights[eid]);edgechecks+=1
 back={n:F(0) if n in model.terminals else None for n in model.order}
 for u in reversed(model.order):
  for v,eid in model.adj[u]:
   if back[v] is not None:
    value=weights[eid]+back[v]
    if back[u] is None or value>back[u]:back[u]=value
 assert {e:F(w,model.scale) for e,w in model.weights.items()}==weights
 assert {n:F(w,model.scale) for n,w in model.forward.items()}==forward
 assert {n:None if w is None else F(w,model.scale) for n,w in model.back.items()}==back
 assert model.cpd_seconds()==max(forward[n] for n in model.terminals)
 if event is not None:assert F(event['model_cpd_after_ns'])==model.cpd_seconds()*10**9
 frames+=1
assert frames==157 and model.update_work==r['timing_update_work']
assert all(sha(p)==h for p,h in bindings.items())
report=dict(bindings=bindings,complete_fraction_frames=frames,edge_checks=edgechecks,affected_forward_nodes=sum(w['forward_nodes'] for w in model.update_work),affected_backward_nodes=sum(w['backward_nodes'] for w in model.update_work),full_forward_nodes_per_update=len(model.order),scope='All156 real commits plus initial full weights/forward/back/CPD equal independent Fraction recurrences; physical and query guard identity bound separately. No new native run or full workflow performance proof.')
(D/'timing_frame_verification.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='bindings'})
