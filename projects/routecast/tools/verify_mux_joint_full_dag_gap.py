"""Independent backward DAG recurrence and native candidate evidence binding."""
import json
from functools import lru_cache
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_joint_full_dag_gap_2026-10-07';r=json.loads((out/'receipt.json').read_text());checked=[];counterexamples=[]
gate=ROOT/'experiments/mux_retained_joint_quality_gate_2026-10-06';gv=json.loads((gate/'verification.json').read_text());assert r['native_verification_sha256']==sha(gate/'verification.json') and gv['receipt_sha256']==sha(gate/'receipt.json');native={(row['width'],row['index']):row for row in gv['rows']}
for row in r['rows']:
 if row['status']=='INITIAL_DIAGNOSTIC_SKIP':continue
 assert all(sha(f)==h for f,h in row['files'].items())
 w,i=row['width'],row['index'];nf=native[(w,i)];assert row['native_candidate_cpd_ns']==nf.get('predicted_cpd_ns') and row['native_original_cpd_ns']==nf.get('original_cpd_ns') and row['native_selected']==nf.get('selected')
 def read(p):return json.loads(p.read_text())
 graph=read(ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json');mapping=read(ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json');meta=read(ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json');b=read(ROOT/f'experiments/mux_retained_joint_budgets_2026-10-06/w{w}_m{i}.json');candidate=read(ROOT/f'experiments/mux_retained_joint_cached_reroute_2026-10-06/w{w}_m{i}/prediction.json')
 incoming={int(n):[] for n in graph['nodes']}
 for eid,e in graph['edges'].items():
  if not e['disabled']:incoming[e['sink']].append((e['source'],eid))
 def evaluate(vector):
  @lru_cache(None)
  def arrival(n):
   values=[F(0)]
   for u,eid in incoming[n]:
    c=meta['edge_connection_ids'].get(eid)
    delay=(vector[str(c)]+F(mapping['external_edges'][eid]['old_local_offset_seconds'])*10**9) if c is not None else F(graph['edges'][eid]['max_delay_seconds'])*10**9
    values.append(arrival(u)+delay)
   return max(values)
  return max(arrival(int(n)) for n,kind in graph['nodes'].items() if kind=='SINK')
 affected=set(b['affected_connection_ids']);initial={k:F(b['budgets_ns'].get(k,b['default_budget_ns'])) if int(k) in affected else F(v) for k,v in meta['floor_ns'].items()}
 # Authenticate fixed retained floors against original native RR branch mapping.
 for eid,c in meta['edge_connection_ids'].items():
  if c not in affected:assert initial[str(c)]==F(mapping['external_edges'][eid]['branch']['rr_delay_seconds'])*10**9
 assert evaluate(initial)==F(row['initial_budget_full_dag_cpd_ns'])
 assert row['initial_budget_full_dag_pass']==(evaluate(initial)<=F(row['target_cpd_ns']))
 records={str(q['connection_id']):q for q in candidate['records']}
 if row['complete']:
  assert set(records)==set(initial) and candidate['failure'] is None
  actual={k:F(q['answer']['delay']*10**9,candidate['scale']) for k,q in records.items()}
  assert evaluate(actual)==F(row['actual_full_dag_cpd_ns'])
  over=sorted(int(k) for k in actual if actual[k]>initial[k]);assert over==sorted(row['actual_over_initial_bound_connection_ids'])
  final={k:actual[k] if q.get('mode')=='NATIVE_REFERENCE_RETAINED' else F(b['budgets_ns'].get(k,b['default_budget_ns'])) for k,q in records.items()}
  assert evaluate(final)==F(row['final_query_budget_full_dag_cpd_ns'])
  # Candidate STA uses imported predicted CPD, selected canonical may be reference.
  assert row['native_candidate_cpd_ns'] is not None
  if not over and evaluate(actual)<=F(row['target_cpd_ns']) and F(str(row['native_candidate_cpd_ns']))<=F(row['target_cpd_ns']) and not row['initial_budget_full_dag_pass']:
   counterexamples.append(dict(width=w,index=i,budget_bound_ns=row['initial_budget_full_dag_cpd_ns'],actual_model_ns=row['actual_full_dag_cpd_ns'],native_candidate_ns=row['native_candidate_cpd_ns']))
 else:assert row['actual_full_dag_cpd_ns'] is None
 checked.append((w,i))
assert len(r['rows'])==12 and len(checked)==5 and [(x['width'],x['index']) for x in counterexamples]==[(8,2),(8,3)]
(out/'verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),receipt_sha256=sha(out/'receipt.json'),cases_checked=checked,counterexamples=counterexamples,scope='Independent backward fullDAG: fixed retained floors agree original mapped native RR branch delay, entire actual connection-delay vector within initial envelope and meets model/native candidate target in two cases while worst-budget envelope fails. Selected canonical output not substituted for candidate STA. Finite retrospective existence counterexample to interpreting sufficient budget certification as infeasibility; not global universal/native-offset theorem or new prospective improvement.'),indent=2)+'\n');print('verified conservative budget counterexamples',counterexamples)
