import json
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];parent=root/'experiments/native_baseline_critical_rc_delta_2026-10-06';receipt=json.loads((parent/'receipt.json').read_text());assert sha(parent/'results.json')==receipt['results_sha256'];verified=json.loads((parent/'verification.json').read_text());assert verified['results_sha256']==sha(parent/'results.json');rows=json.loads((parent/'results.json').read_text())['results'];protocol=json.loads((parent/'protocol.json').read_text());baseline={x['edge']:x['result']['delay'] for x in rows if x['pair_index']==-1};assert len(baseline)==6;features=[]
for i in range(20):
 cohort=[x for x in rows if x['pair_index']==i];assert {x['edge'] for x in cohort}==set(baseline);delta=sum(x['result']['delay']-baseline[x['edge']] for x in cohort);features.append({'index':i,'delta_integer_rc':delta,'delta_ns':float(Fraction(delta,protocol['scale'])*10**9),'selected':delta<0})
out=root/'experiments/native_baseline_rc_delta_selection_2026-10-06';out.mkdir();(out/'features.json').write_text(json.dumps({'pairs':features,'rule':'Sum exact isolated path witness delay delta < 0, fixed threshold; no candidate native timing labels.','rc_results_sha256':sha(parent/'results.json'),'scope':'Cost-optimal budget-constrained path witnesses, not minimum-delay proof or full STA. Fixed budget zero competing demand, baseline top path only.'},indent=2)+'\n')
# Labels are opened only after the feature artifact is written.
labels_path=root/'experiments/native_candidate_common_state_2026-10-06/receipt.json';labels=json.loads(labels_path.read_text());evaluation=[]
for mode in ('cold','retained'):
 examples=[]
 for f in features:
  row=next(x for x in labels['results'] if x['index']==f['index'] and x['mode']==mode);improves=row['candidate_cpd_ns']<row['before_cpd_ns']-1e-5;examples.append({**f,'strict_improvement':improves,'native_cpd_ns':row['candidate_cpd_ns']})
 selected=[e for e in examples if e['selected']];result={'mode':mode,'selected':len(selected),'captured_improvements':sum(e['strict_improvement'] for e in selected),'missed_improvements':sum(e['strict_improvement'] and not e['selected'] for e in examples),'selected_best_cpd_ns':min((e['native_cpd_ns'] for e in selected),default=None),'all_best_cpd_ns':min(e['native_cpd_ns'] for e in examples),'examples':examples};evaluation.append(result);print({k:v for k,v in result.items() if k!='examples'})
(out/'evaluation.json').write_text(json.dumps({'results':evaluation,'features_sha256':sha(out/'features.json'),'labels_sha256':sha(labels_path),'scope':'Retrospective known-family fixed-rule diagnostic, no threshold tuning and no safe-pruning or pipeline gain claim.'},indent=2)+'\n')
