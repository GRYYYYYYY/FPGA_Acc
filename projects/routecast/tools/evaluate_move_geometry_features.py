import json
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_move_geometry_features_2026-10-06';p=out/'features.json';features=json.loads(p.read_text());assert all(sha(f)==h for f,h in features['inputs_sha256'].items());parent=root/'experiments/native_candidate_common_state_2026-10-06';verification=json.loads((parent/'verification.json').read_text());assert all(sha(f)==h for f,h in verification['sha256'].items());labels=json.loads((parent/'receipt.json').read_text());results=[]
for mode in ('cold','retained'):
 examples=[]
 for feature in features['pairs']:
  row=next(x for x in labels['results'] if x['mode']==mode and x['index']==feature['index']);assert row['pair']==feature['pair'];improves=row['candidate_cpd_ns']<row['before_cpd_ns']-1e-5;examples.append({'index':row['index'],'delta_hpwl':feature['delta_hpwl'],'selected':feature['selected_by_fixed_rule'],'strict_timing_improvement':improves,'candidate_cpd_ns':row['candidate_cpd_ns']})
 results.append({'mode':mode,'strict_improving_candidates':sum(x['strict_timing_improvement'] for x in examples),'missed_improving_candidates':sum(x['strict_timing_improvement'] and not x['selected'] for x in examples),'selected_candidates':sum(x['selected'] for x in examples),'examples':examples})
(out/'evaluation.json').write_text(json.dumps({'results':results,'features_sha256':sha(p),'labels_verification_sha256':sha(parent/'verification.json'),'scope':'Retrospective fixed HPWL rule diagnostic; no label-driven threshold tuning. No admitted end-to-end pruning policy.'},indent=2)+'\n');print([(x['mode'],x['strict_improving_candidates'],x['missed_improving_candidates']) for x in results])
