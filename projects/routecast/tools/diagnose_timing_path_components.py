"""Retrospective critical-path decomposition of authenticated timing models."""
import json
from fractions import Fraction as F
from pathlib import Path
from exact_incremental_timing_dag import ExactTimingDAG
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'experiments/mux_cold_actual_timing_model_2026-10-07'
rp=base/'receipt.json';vp=base/'verification.json'
r=json.loads(rp.read_text());assert json.loads(vp.read_text())['receipt_sha256']==sha(rp)
assert all(sha(p)==h for p,h in r['bindings'].items())
rows=[]
for row in r['rows']:
 w,i=row['width'],row['index']
 s=json.loads((ROOT/f'experiments/mux_full_cohort_cold_lifecycle_2026-10-06/mux_w{w}_m{i}_0/accepted_state.json').read_text())
 actual={str(q['connection_id']):F(q['answer']['delay']*10**9,s['scale']) for q in s['records']}
 g=json.loads((ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json').read_text())
 m=json.loads((ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json').read_text())
 a=json.loads((ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json').read_text())
 dag=ExactTimingDAG.from_native_metadata(g,m,a,actual)
 current=min(n for n in dag.sinks if dag.arrivals[n]==dag.cpd)
 path=[];fixed=F(0);route=F(0)
 while dag.arrivals[current]>0:
  options=[(u,offset,c) for u,offset,c in dag.incoming[current] if dag.arrivals[u]+offset+(actual[c] if c is not None else 0)==dag.arrivals[current]]
  assert options
  u,offset,c=min(options,key=lambda x:(x[0],str(x[2]),x[1]))
  path.append(dict(source=u,sink=current,fixed_ns=str(offset),connection_id=c,route_ns=str(actual[c] if c is not None else 0)))
  fixed+=offset;route+=actual[c] if c is not None else 0;current=u
 assert fixed+route==dag.cpd==F(row['actual_model_cpd_ns'])
 rows.append(dict(width=w,index=i,cpd_ns=str(dag.cpd),fixed_component_ns=str(fixed),route_component_ns=str(route),external_connections_on_path=sum(e['connection_id'] is not None for e in path),max_connection_ns=str(max(actual.values())),model_minus_native_ns=row['model_minus_native_ns'],path=list(reversed(path))))
out=ROOT/'experiments/timing_path_components_2026-10-07';out.mkdir(exist_ok=True)
result=dict(source_sha256=sha(Path(__file__)),bindings={str(rp):sha(rp),str(vp):sha(vp),**r['bindings']},rows=rows,negative_model_errors=sum(F(x['model_minus_native_ns'])<0 for x in rows),positive_model_errors=sum(F(x['model_minus_native_ns'])>0 for x in rows),scope='Exact arithmetic decomposition of old-offset DAG over archived cold-route vectors; not a decomposition of native STA error. Both signs preclude treating this empirical model as a proven native upper/lower bound. No prospective result or net gain.')
(out/'diagnosis.json').write_text(json.dumps(result,indent=2)+'\n')
print([(x['width'],x['index'],x['external_connections_on_path'],float(F(x['route_component_ns'])),float(F(x['fixed_component_ns']))) for x in rows])
print('error signs',result['negative_model_errors'],result['positive_model_errors'])
