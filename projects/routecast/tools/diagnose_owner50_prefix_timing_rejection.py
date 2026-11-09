"""Offline exact prefix lower bounds; no deployment or saved-time claim."""
import json
from fractions import Fraction as F
from pathlib import Path
from exact_incremental_timing_dag import ExactTimingDAG
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'experiments/owner50_retained_rr_2026-10-07_predictor'
out=ROOT/'experiments/owner50_prefix_timing_diagnosis_2026-10-07'
out.mkdir(exist_ok=False)
files=[Path(__file__),ROOT/'tools/exact_incremental_timing_dag.py',source/'protocol.json',source/'receipt.json']
for p in sorted(source.glob('w*/result.json')):
 w=int(p.parent.name.split('_')[0][1:]);i=int(p.parent.name.split('_')[1][1:]);files.extend([p,ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json',ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json',ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json',ROOT/f'experiments/owner50_retained_rr_2026-10-07_floor/w{w}_m{i}.json'])
bindings={str(p):sha(p) for p in files}
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,policy='Offline retrospective prefix diagnosis. Future delay zero is componentwise lower bound in exact old-offset DAG, not native STA. Frozen completed paths only. Repair/rewrite stages excluded. No measured runtime saving or new admission policy.'),indent=2)+'\n')
rows=[]
for p in sorted(source.glob('w*/result.json')):
 r=json.loads(p.read_text());c=r['result']['candidate'];w=int(p.parent.name.split('_')[0][1:]);i=int(p.parent.name.split('_')[1][1:]);a={**json.loads((ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json').read_text()),**json.loads((ROOT/f'experiments/owner50_retained_rr_2026-10-07_floor/w{w}_m{i}.json').read_text())};row=dict(width=w,index=i,status=r['candidate_model_gate']['status'])
 if any(x['update']['repair'] is not None for x in r['attempts']):
  row.update(supported=False,reason='Repair can replace earlier paths; requires per-generation invalidation before a live prefix gate.');rows.append(row);continue
 events=c['events'];assert all(e['committed'] and e['answer']['status']=='FOUND' for e in events)
 ids=[e['query']['connection_id'] for e in events];assert len(ids)==len(set(ids))
 actual={x['connection_id']:F(x['answer']['delay']*10**9,c['scale']) for x in c['records']};assert set(actual)=={int(k) for k in a['floor_ns']}
 dag=ExactTimingDAG.from_native_metadata(json.loads((ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json').read_text()),json.loads((ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json').read_text()),a,{k:F(0) if k in set(ids) else v for k,v in actual.items()})
 target=F(a['target_cpd_ns']);full=F(r['candidate_model_gate']['actual_cpd_ns']);bounds=[dag.cpd];first=0 if bounds[0]>target else None
 for n,e in enumerate(events,1):
  cid=e['query']['connection_id'];assert F(e['answer']['delay']*10**9,c['scale'])==actual[cid]
  value=dag.update({cid:actual[cid]},commit=True);assert bounds[-1]<=value<=full;bounds.append(value)
  if first is None and value>target:first=n
 assert bounds[-1]==full
 assert (first is None)==(row['status']=='ACTUAL_MODEL_PASS_NATIVE_PENDING')
 row.update(supported=True,queries=len(events),first_proven_reject_prefix=first,remaining_queries_at_proof=None if first is None else len(events)-first,full_cpd_ns=str(full),target_cpd_ns=str(target),prefix_cpd_ns=[str(x) for x in bounds]);rows.append(row)
assert all(sha(p)==h for p,h in bindings.items())
(out/'diagnosis.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows,scope='All eight searched cases accounted; seven fixed-prefix cases verified, one repair case explicitly unsupported. Four initial allocation skips have no query prefix. Remaining query counts are retrospective opportunities, not measured time savings; zero floors avoid retained planning-floor necessity assumptions.'),indent=2)+'\n')
for row in rows:print({k:v for k,v in row.items() if k!='prefix_cpd_ns'},flush=True)
