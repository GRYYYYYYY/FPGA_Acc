"""Frozen metrics for move sketches against off/on native routes; labels evaluator-only."""
import collections,json,shutil
from pathlib import Path
from pre_route_endpoints import sha
from stream_metric_domain import metric_domain
from prediction_metrics import compare

base=Path('experiments');seq=base/'adder_tree_2L032_move_sequence_2026-10-06';pred=base/'adder_tree_2L032_move_sequence_audit_2026-10-06';native=base/'native_pressure_move_sequence_trial_2026-10-06';out=base/'adder_tree_2L032_move_pressure_evaluation_2026-10-06';out.mkdir();(out/'source').mkdir();bindings={}
def load(path):bindings[str(path)]=sha(path);return json.loads(path.read_text())
p=load(seq/'protocol.json');pr=load(pred/'receipt.json');nr=load(native/'receipt.json');assert nr['protocol_sha256']==sha(native/'protocol.json')
for name in ('evaluate_move_sequence_pressure.py','stream_metric_domain.py','prediction_metrics.py','pre_route_endpoints.py'):
 shutil.copyfile(Path('tools')/name,out/'source'/name);bindings[str(Path('tools')/name)]=sha(Path('tools')/name)
rows=[]
for step in pr['steps']:
 i=step['step'];prediction_path=pred/f'step_{i}_prediction.json';assert sha(prediction_path)==step['prediction_sha256'];prediction=load(prediction_path);ep=load(seq/f'step_{i}_endpoints.json');identity=lambda records:collections.Counter((v['net_id'],v['source'],v['sink']) for v in records)
 assert identity(prediction['connections'])==identity(ep['connections'])
 for mode in ('off','on'):
  trial=next(v for v in nr['results'] if v['step']==i and v['mode']==mode);physical_path=native/f'{i:02d}_{mode}_physical.json';assert sha(physical_path)==trial['physical_sha256'];truth=load(physical_path);assert identity(truth['connections'])==identity(ep['connections']) and truth['overflow_units']==0
  pv=prediction['node_occupancy'];tv=truth['node_occupancy'];rp,rt,sp,st,caps,counts=metric_domain(p['inputs']['rr_graph']['path'],pv,tv)
  report={'step':i,'mode':mode,'resource':compare(rp,rt,max(1,len(rp)//20)),'spatial':compare(sp,st,20),'prediction_all_type_overflow_units':sum(max(0,v-caps[n]) for n,v in pv.items()),'native_all_type_overflow_units':sum(max(0,v-caps[n]) for n,v in tv.items())};rows.append(report);print(json.dumps(report),flush=True)
assert all(sha(path)==digest for path,digest in bindings.items())
(out/'report.json').write_text(json.dumps({'inputs_sha256':bindings,'results':rows,'scope':'Post-outcome descriptive same-cohort metrics, unchanged top5percent/top20/string-ID ties; native labels never passed to predictor. Does not establish causal feedback effect or prospective admission policy.'},indent=2)+'\n');(out/'receipt.json').write_text(json.dumps({'report_sha256':sha(out/'report.json'),'all_exact_cohort_checks_pass':True},indent=2)+'\n')
