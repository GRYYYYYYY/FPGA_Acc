"""Full-DAG floor proof by upper potentials and an attaining critical path, no new DAG search."""
import json
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/branch_budget_global_dag_floors_v2_2026-10-08';dp=D/'diagnosis.json';d=json.loads(dp.read_text());assert all(sha(f)==h for f,h in d['bindings'].items())
expected={(w,i) for w in (8,16,32) for i in range(4)};assert len(d['rows'])==12 and {(x['width'],x['index']) for x in d['rows']}==expected
rows=[];checks=0
for x in d['rows']:
 w,i=x['width'],x['index'];tg=R/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json';mp=R/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json';ap=R/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json';ad=R/f'experiments/branch_budget_admission_census_v1_2026-10-08/w{w}_m{i}_admission.json'
 graph=json.loads(tg.read_text());mapping=json.loads(mp.read_text());allocation=json.loads(ap.read_text());admission=json.loads(ad.read_text());floors={str(y['connection_id']):F(y['minimum_seconds']) for y in admission['rows']}
 assert allocation['graph_sha256']==sha(tg)==mapping['timing_graph_sha256'] and allocation['mapping_sha256']==sha(mp)
 potential={int(n):F(t) for n,t in x['arrival_seconds'].items()};assert set(potential)==set(map(int,graph['nodes'])) and all(t>=0 for t in potential.values())
 enabled={eid:e for eid,e in graph['edges'].items() if not e['disabled']};assert set(x['edge_delay_seconds'])==set(enabled);delays={}
 for eid,e in enabled.items():
  if eid in allocation['edge_connection_ids']:
   cid=str(allocation['edge_connection_ids'][eid]);delay=floors[cid]+F(mapping['external_edges'][eid]['old_local_offset_seconds'])
  else:delay=F(e['max_delay_seconds'])
  assert delay==F(x['edge_delay_seconds'][eid]);delays[eid]=delay
  assert potential[e['sink']]>=potential[e['source']]+delay;checks+=1
 terminals=[int(n) for n,kind in graph['nodes'].items() if kind=='SINK'];maximum=max(potential[n] for n in terminals)
 path=x['critical_path_edge_ids'];assert path
 first=enabled[path[0]]['source'];node=first;value=F(0);assert potential[first]==0
 for eid in path:
  e=enabled[eid];assert e['source']==node;value+=delays[eid];node=e['sink'];assert potential[node]==value
 assert node in terminals and value==maximum and maximum*10**9==F(x['fixed_local_model_floor_cpd_ns'])
 target=F(allocation['target_cpd_ns']);assert target==F(x['target_cpd_ns']) and x['fixed_local_model_global_floor_feasible']==(maximum*10**9<=target)
 rows.append(dict(width=w,index=i,all_enabled_edge_upper_inequalities_pass=True,critical_path_attains_upper_potential=True,fixed_local_model_global_floor_feasible=x['fixed_local_model_global_floor_feasible'],floor_cpd_ns=x['fixed_local_model_floor_cpd_ns'],target_cpd_ns=x['target_cpd_ns']))
assert all(sha(f)==h for f,h in d['bindings'].items())
report=dict(diagnosis_sha256=sha(dp),verifier_sha256=sha(Path(__file__)),all_twelve_model_global_floor_certificates_pass=True,complete_cases=12,edge_inequalities=checks,model_global_floor_feasible_cases=sum(x['fixed_local_model_global_floor_feasible'] for x in rows),rows=rows,scope='Certified full-DAG optimistic lower-delay vector under frozen old local/intracluster offsets. Feasible lower vector is not joint physical/shared-tree or target STA feasibility; violated critical path proves only this fixed-local model fails target. No budget adjustment.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('all12 full-DAG certificates pass; edges',checks,'optimistic model feasible',report['model_global_floor_feasible_cases'])
