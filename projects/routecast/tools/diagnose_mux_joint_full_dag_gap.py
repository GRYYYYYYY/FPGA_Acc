"""Retrospective reported-path budget bound versus full DAG and native STA."""
import json
from pathlib import Path
from fractions import Fraction as F
from exact_incremental_timing_dag import ExactTimingDAG
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux_retained_joint_cached_reroute_2026-10-06';budgets=ROOT/'experiments/mux_retained_joint_budgets_2026-10-06';gate=ROOT/'experiments/mux_retained_joint_quality_gate_2026-10-06';out=ROOT/'experiments/mux_joint_full_dag_gap_2026-10-07';out.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text())
p=read(base/'protocol.json');verification=read(base/'verification.json');assert verification['receipt_sha256']==sha(base/'receipt.json');gv=read(gate/'verification.json');assert gv['receipt_sha256']==sha(gate/'receipt.json');native={(r['width'],r['index']):r for r in gv['rows']};rows=[]
for c in p['cases']:
 w,i=c['width'],c['index'];bf=budgets/f'w{w}_m{i}.json';b=read(bf)
 if b['status']!='JOINT_VECTOR_CONSTRUCTED':rows.append(dict(width=w,index=i,status='INITIAL_DIAGNOSTIC_SKIP'));continue
 meta_file=ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json';meta=read(meta_file);graph_file=ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json';map_file=ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json';graph=read(graph_file);mapping=read(map_file)
 assert sha(graph_file)==meta['graph_sha256'] and sha(map_file)==meta['mapping_sha256']
 candidate_file=base/f'w{w}_m{i}/prediction.json';candidate=read(candidate_file);affected=set(b['affected_connection_ids'])
 # meta floor for retained connections is the fixed actual old RR delay.
 # For affected connections it may be a relaxed lower bound, so never use it there.
 old_budget={k:F(v) for k,v in meta['floor_ns'].items()}
 vector={k:(F(b['budgets_ns'].get(k,b['default_budget_ns'])) if int(k) in affected else v) for k,v in old_budget.items()}
 dag=ExactTimingDAG.from_native_metadata(graph,mapping,meta,vector);target=F(meta['target_cpd_ns']);bound=dag.cpd
 records={str(q['connection_id']):q for q in candidate['records']};complete=candidate['failure'] is None and len(records)==candidate['required_connections']
 actual=None;violations=[];post_bound=None
 if complete:
  assert set(records)==set(vector)
  actual_vector={k:F(q['answer']['delay']*10**9,candidate['scale']) for k,q in records.items()}
  actual=dag.update(actual_vector)
  # Retrospective final membership: retained paths stay exact; query budgets for changed paths.
  post={k:(actual_vector[k] if q.get('mode')=='NATIVE_REFERENCE_RETAINED' else F(b['budgets_ns'].get(k,b['default_budget_ns']))) for k,q in records.items()}
  post_bound=dag.update(post)
  violations=[int(k) for k in actual_vector if actual_vector[k]>vector[k]]
 nf=native[(w,i)]
 row=dict(width=w,index=i,status=candidate['status'],complete=complete,affected_connections=len(affected),initial_budget_full_dag_cpd_ns=str(bound),target_cpd_ns=str(target),initial_budget_full_dag_pass=bound<=target,actual_full_dag_cpd_ns=str(actual) if actual is not None else None,final_query_budget_full_dag_cpd_ns=str(post_bound) if post_bound is not None else None,actual_over_initial_bound_connection_ids=violations,native_original_cpd_ns=nf.get('original_cpd_ns'),native_candidate_cpd_ns=nf.get('predicted_cpd_ns'),native_selected=nf.get('selected'),files={str(f):sha(f) for f in (bf,meta_file,graph_file,map_file,candidate_file)})
 rows.append(row);print(w,i,row['initial_budget_full_dag_cpd_ns'],row['actual_full_dag_cpd_ns'],row['native_original_cpd_ns'],flush=True)
(out/'receipt.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),evaluator_sha256=sha(ROOT/'tools/exact_incremental_timing_dag.py'),baseline_verification_sha256=sha(base/'verification.json'),native_verification_sha256=sha(gate/'verification.json'),rows=rows,scope='Retrospective old-local-offset DAG hypothesis, before-routing budget envelope uses affected/default query caps and unaffected old floors. Final envelope uses actual retained membership; not prospective allocation. Incomplete candidate actualCPD absent. Native STA independent observed evidence, not equality guarantee or proof of global infeasibility. All12 inherited cases retained; no cold oracle fed rerouter.'),indent=2)+'\n')
