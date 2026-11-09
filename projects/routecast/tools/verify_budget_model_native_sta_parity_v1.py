"""Independent all-edge arithmetic and attaining-path checks for three actual delay vectors."""
import json,re
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/budget_model_native_sta_parity_v1_2026-10-08';dp=D/'diagnosis.json';d=json.loads(dp.read_text());assert all(sha(f)==h for f,h in d['bindings'].items());assert d['complete_vectors']==len(d['rows'])==3 and {x['mode'] for x in d['rows']}=={'cold','resume','budget_repaired'}
tg=json.loads((R/'experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json').read_text());mp=json.loads((R/'experiments/mux_full_timing_rr_2026-10-06/w32.json').read_text());a=json.loads((R/'experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json').read_text());enabled={eid:e for eid,e in tg['edges'].items() if not e['disabled']};checks=0
sources={'cold':('native_cold_branch_control_v8_2026-10-08/target_budget_verification.json','native_cold_branch_control_v8_2026-10-08/cold/run.log'),'resume':('native_resume_branch_partial_v8_2026-10-08/target_budget_verification.json','native_resume_branch_partial_v8_2026-10-08/resume/run.log'),'budget_repaired':('budget_repair_reconciled_dump_v1_2026-10-08/verification.json','budget_repair_canonical_v3_2026-10-08/canonical/reload.log')}
for x in d['rows']:
 vp,lp=[R/'experiments'/s for s in sources[x['mode']]];v=json.loads(vp.read_text());assert all(sha(f)==h for f,h in v['bindings'].items());delays={str(y['connection_id']):F(y['delay_seconds']) for y in v['rows']};assert len(delays)==1929
 pot={int(n):F(t) for n,t in x['arrival_seconds'].items()};assert set(pot)==set(map(int,tg['nodes'])) and all(t>=0 for t in pot.values()) and set(x['edge_delay_seconds'])==set(enabled)
 weights={}
 for eid,e in enabled.items():
  delay=delays[str(a['edge_connection_ids'][eid])]+F(mp['external_edges'][eid]['old_local_offset_seconds']) if eid in a['edge_connection_ids'] else F(e['max_delay_seconds']);weights[eid]=delay
  assert delay==F(x['edge_delay_seconds'][eid]) and pot[e['sink']]>=pot[e['source']]+delay;checks+=1
 path=x['critical_path_edge_ids'];assert path;node=enabled[path[0]]['source'];assert pot[node]==0;total=F(0)
 for eid in path:
  e=enabled[eid];assert node==e['source'];total+=weights[eid];node=e['sink'];assert total==pot[node]
 terminals=[int(n) for n,k in tg['nodes'].items() if k=='SINK'];assert node in terminals and total==max(pot[n] for n in terminals)
 native=F(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',lp.read_text())[-1]);model=total*10**9
 assert model==F(x['model_cpd_ns']) and native==F(x['native_printed_cpd_ns']) and model-native==F(x['model_minus_native_ns'])
 assert x['model_within_original_target']==(model<=F(a['target_cpd_ns'])) and x['native_within_original_target']==(native<=F(a['target_cpd_ns']))
assert all(sha(f)==h for f,h in d['bindings'].items())
report=dict(diagnosis_sha256=sha(dp),verifier_sha256=sha(Path(__file__)),all_three_complete_actual_delay_vectors_pass=True,connections_per_vector=1929,edge_inequalities=checks,scope='Exact fixed-model arithmetic/native printed result comparison; not calibration, error bound, or native STA equivalence.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS three full vectors, edge inequalities',checks)
