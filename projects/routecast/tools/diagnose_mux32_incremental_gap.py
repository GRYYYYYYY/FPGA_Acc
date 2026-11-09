"""Counterfactual delay-vector attribution, not executable hybrid routing."""
import json
from pathlib import Path
from fractions import Fraction as F
from exact_incremental_timing_dag import ExactTimingDAG
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];w=32;i=2
pf=ROOT/'experiments/owner50_retained_rr_2026-10-07_predictor/w32_m2/result.json'
pr=pf.parent.parent/'receipt.json';p=json.loads(pf.read_text());receipt=json.loads(pr.read_text());row=next(x for x in receipt['rows'] if (x['width'],x['index'])==(w,i));assert row['result_sha256']==sha(pf)
c=p['result']['candidate'];assert c['status']=='COMPLETE_CANDIDATE' and c['failure'] is None
sf=ROOT/'experiments/mux_full_cohort_cold_lifecycle_2026-10-06/mux_w32_m2_0/accepted_state.json'
s=json.loads(sf.read_text())
gf=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json';mf=ROOT/'experiments/mux_full_timing_rr_2026-10-06/w32.json';af=ROOT/'experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json'
g=json.loads(gf.read_text());m=json.loads(mf.read_text());a=json.loads(af.read_text())
inc={str(q['connection_id']):F(q['answer']['delay']*10**9,c['scale']) for q in c['records']};cold={str(q['connection_id']):F(q['answer']['delay']*10**9,s['scale']) for q in s['records']}
assert inc.keys()==cold.keys() and len(inc)==c['required_connections']==1929
old={}
for eid,cid in a['edge_connection_ids'].items():
 value=F(m['external_edges'][eid]['branch']['rr_delay_seconds'])*10**9;cid=str(cid)
 assert cid not in old or old[cid]==value
 old[cid]=value
assert old.keys()==inc.keys()
affected=set(map(str,c['affected']['affected_complete_net_connection_ids']));assert affected<=inc.keys()
unaffected=inc.keys()-affected;assert all(inc[k]==old[k] for k in unaffected)
vectors={'published_old':old,'incremental':inc,'cold':cold,'incremental_with_cold_affected':{k:cold[k] if k in affected else inc[k] for k in inc},'incremental_with_cold_unaffected':{k:inc[k] if k in affected else cold[k] for k in inc}}
rows=[]
for name,vector in vectors.items():
 dag=ExactTimingDAG.from_native_metadata(g,m,a,vector);n=min(n for n in dag.sinks if dag.arrivals[n]==dag.cpd);path=[]
 while dag.arrivals[n]>0:
  choices=[x for x in dag.incoming[n] if dag.arrivals[x[0]]+x[1]+(vector[x[2]] if x[2] is not None else 0)==dag.arrivals[n]]
  u,offset,cid=min(choices,key=lambda x:(x[0],str(x[2]),x[1]))
  if cid is not None:path.append(dict(connection_id=cid,affected=cid in affected,delay_ns=str(vector[cid])))
  n=u
 rows.append(dict(vector=name,model_cpd_ns=str(dag.cpd),critical_external_connections=list(reversed(path))))
assert F(rows[1]['model_cpd_ns'])==F(p['candidate_model_gate']['actual_cpd_ns'])
out=ROOT/'experiments/mux32_incremental_gap_2026-10-07';out.mkdir(exist_ok=True)
result=dict(source_sha256=sha(Path(__file__)),bindings={str(f):sha(f) for f in (pf,pr,sf,gf,mf,af)},affected_connections=len(affected),unaffected_connections=len(unaffected),unaffected_incremental_equals_old=True,rows=rows,scope='Retrospective DEVELOPMENT exact old-offset DAG delay-vector counterfactual. Hybrid vectors are not physically routed or capacity/legal checked, and cold vectors are evaluator oracle only. Attribution not deployable prediction, native-quality or netgain proof.')
(out/'diagnosis.json').write_text(json.dumps(result,indent=2)+'\n');print(result['affected_connections'],result['unaffected_connections']);print(rows)
