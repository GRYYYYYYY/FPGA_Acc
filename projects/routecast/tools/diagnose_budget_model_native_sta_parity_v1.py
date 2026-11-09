"""Compare frozen-local full-DAG predictions against three complete native-route states."""
import json,re
from fractions import Fraction as F
from collections import defaultdict,deque
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];gp=R/'experiments/branch_budget_global_dag_floors_v2_2026-10-08/verification.json';g=json.loads(gp.read_text());assert g['all_twelve_model_global_floor_certificates_pass']
gd=gp.with_name('diagnosis.json');assert g['diagnosis_sha256']==sha(gd);prior=json.loads(gd.read_text());assert all(sha(f)==h for f,h in prior['bindings'].items())
bindings={**prior['bindings'],str(gp):sha(gp),str(gd):sha(gd),str(Path(__file__)):sha(Path(__file__))}
tg=R/'experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json';mp=R/'experiments/mux_full_timing_rr_2026-10-06/w32.json';ap=R/'experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json';graph=json.loads(tg.read_text());mapping=json.loads(mp.read_text());allocation=json.loads(ap.read_text());assert allocation['graph_sha256']==sha(tg) and allocation['mapping_sha256']==sha(mp)
vectors=[('cold',R/'experiments/native_cold_branch_control_v8_2026-10-08/target_budget_verification.json',R/'experiments/native_cold_branch_control_v8_2026-10-08/cold/run.log'),('resume',R/'experiments/native_resume_branch_partial_v8_2026-10-08/target_budget_verification.json',R/'experiments/native_resume_branch_partial_v8_2026-10-08/resume/run.log'),('budget_repaired',R/'experiments/budget_repair_reconciled_dump_v1_2026-10-08/verification.json',R/'experiments/budget_repair_canonical_v3_2026-10-08/canonical/reload.log')]
rows=[]
for name,vp,log in vectors:
 v=json.loads(vp.read_text());assert all(sha(f)==h for f,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(vp)]=sha(vp);bindings[str(log)]=sha(log)
 delays={str(x['connection_id']):F(x['delay_seconds']) for x in v['rows']};assert len(delays)==len(v['rows'])==1929
 adj=defaultdict(list);ind={int(n):0 for n in graph['nodes']};enabled={eid:e for eid,e in graph['edges'].items() if not e['disabled']}
 for eid,e in enabled.items():adj[e['source']].append((e['sink'],eid));ind[e['sink']]+=1
 q=deque(n for n,d in ind.items() if not d);order=[]
 while q:
  u=q.popleft();order.append(u)
  for sink,eid in adj[u]:
   ind[sink]-=1
   if not ind[sink]:q.append(sink)
 assert len(order)==len(ind);arrival={n:F(0) for n in order};pred={};edge_delays={}
 for u in order:
  for sink,eid in adj[u]:
   delay=delays[str(allocation['edge_connection_ids'][eid])]+F(mapping['external_edges'][eid]['old_local_offset_seconds']) if eid in allocation['edge_connection_ids'] else F(enabled[eid]['max_delay_seconds'])
   edge_delays[eid]=delay;candidate=arrival[u]+delay
   if candidate>arrival[sink]:arrival[sink]=candidate;pred[sink]=(u,eid)
 terminals=[int(n) for n,kind in graph['nodes'].items() if kind=='SINK'];critical=max(terminals,key=lambda n:arrival[n]);model=arrival[critical]*10**9;path=[];node=critical
 while node in pred:node,eid=pred[node];path.append(eid)
 path.reverse();assert arrival[node]==0;value=F(0)
 for eid in path:
  e=enabled[eid];assert e['source']==node;value+=edge_delays[eid];node=e['sink'];assert arrival[node]==value
 assert value*10**9==model and all(arrival[e['sink']]>=arrival[e['source']]+edge_delays[eid] for eid,e in enabled.items())
 native=F(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log.read_text())[-1]);rows.append(dict(mode=name,model_cpd_ns=str(model),native_printed_cpd_ns=str(native),model_minus_native_ns=str(model-native),model_within_original_target=model<=F(allocation['target_cpd_ns']),native_within_original_target=native<=F(allocation['target_cpd_ns']),critical_path_edge_ids=path,arrival_seconds={str(n):str(v) for n,v in arrival.items()},edge_delay_seconds={eid:str(v) for eid,v in edge_delays.items()}))
assert all(sha(f)==h for f,h in bindings.items());D=R/'experiments/budget_model_native_sta_parity_v1_2026-10-08';D.mkdir(exist_ok=False)
(D/'diagnosis.json').write_text(json.dumps(dict(bindings=bindings,complete_connections_per_vector=1929,complete_vectors=3,rows=rows,scope='Complete physical-model vectors evaluated on fixed old full timing DAG with old local/intracluster offsets and rounded echo delays. Differences are observed, no causal attribution or uncertainty bound/native STA equivalence/performance claim.'),indent=2)+'\n');print([(x['mode'],float(F(x['model_cpd_ns'])),float(F(x['native_printed_cpd_ns'])),float(F(x['model_minus_native_ns']))) for x in rows])
