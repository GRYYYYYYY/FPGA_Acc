"""Audit live prefix decisions against full predecessor witnesses and exact DAG."""
import json
from fractions import Fraction as F
from pathlib import Path
from exact_incremental_timing_dag import ExactTimingDAG
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/owner50_prefix_live_predictor_2026-10-07';old=ROOT/'experiments/owner50_retained_rr_2026-10-07_predictor'
def read(p):return json.loads(p.read_text())
p=read(out/'protocol.json');r=read(out/'receipt.json');prior=read(old/'receipt.json');assert len(r['rows'])==len(prior['rows'])==12 and r['protocol_sha256']==sha(out/'protocol.json');assert all(sha(f)==h for f,h in p['sources'].items());rows=[]
for row,baseline in zip(r['rows'],prior['rows']):
 w,i=row['width'],row['index'];assert (w,i)==(baseline['width'],baseline['index'])
 if row['status']=='PRIOR_ALLOCATION_SKIP':assert baseline['status']==row['status'];rows.append(row);continue
 path=out/f'w{w}_m{i}/result.json';assert sha(path)==row['result_sha256'];new=read(path);before=read(old/f'w{w}_m{i}/result.json');c=new['result']['candidate'];bc=before['result']['candidate']
 if row['status']=='PREFIX_MODEL_TIMING_REJECTED':
  assert baseline['status']=='ACTUAL_MODEL_TIMING_REJECTED';assert new['attempts'][0]['update']['repair'] is None
  reference_incremental=before['attempts'][0]['update']['incremental'];n=len(c['events']);assert c['events']==reference_incremental['events'][:n]
  originals={x['connection_id']:x for x in reference_incremental['records']};assert all(x==originals[x['connection_id']] for x in c['records'])
  a={**read(ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json'),**read(ROOT/f'experiments/owner50_retained_rr_2026-10-07_floor/w{w}_m{i}.json')}
  values={int(k):F(0) for k in a['floor_ns']};values.update({x['connection_id']:F(x['answer']['delay']*10**9,c['scale']) for x in c['records']})
  d=ExactTimingDAG.from_native_metadata(read(ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json'),read(ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json'),a,values)
  proof=c['failure']['proof'];assert d.cpd==F(proof['cpd_lower_bound_ns'])>F(a['target_cpd_ns']);assert proof['committed_prefix']==n
  row={**row,'prefix_proof':proof}
 else:
  assert row['status']==baseline['status'];assert new==before
 rows.append(row)
assert sum(x['status']=='PREFIX_MODEL_TIMING_REJECTED' for x in rows)==6;assert sum(x['status']=='ACTUAL_MODEL_PASS_NATIVE_PENDING' for x in rows)==2
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),baseline_receipt_sha256=sha(old/'receipt.json'),rows=rows,scope='All12 outcome coverage. Six live prefixes exact prior incremental path/event prefixes and independently recomputed zero-future DAG lower bounds. Two PASS results wholly equal predecessor; previous repair case now terminates before repair; four skips unchanged. Driver restoration assertions passed on each exit. Prior native admissions not reexecuted here. Prospective policy can forgo future repair (observed in width32/m3); no general equivalence or total time gain.'),indent=2)+'\n');print('All12 live prefix outcomes verified')
