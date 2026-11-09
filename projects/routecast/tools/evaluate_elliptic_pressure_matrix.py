"""Evaluator-only descriptive ranking; requires completed audited matrix."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from prediction_metrics import spearman
root=Path('experiments/elliptic_pressure_candidate_matrix_2026-10-05');native=Path('experiments/elliptic_native_candidate_labels_2026-10-05');out=Path('experiments/elliptic_pressure_ranking_evaluation_2026-10-05')
if out.exists():raise ValueError('fresh output required')
m=json.loads((root/'receipt.json').read_text());audit=json.loads((root/'matrix_audit.json').read_text());n=json.loads((native/'receipt.json').read_text());na=json.loads((native/'native_labels_audit.json').read_text())
assert na['all_nine_native_runs_authenticated'] and len(m['reports'])==18 and len(n['rows'])==9
assert all(sha(root/f)==h for f,h in audit['artifact_sha256'].items());assert sha(native/'receipt.json')==na['receipt_sha256']
native_protocol=json.loads((native/'protocol.json').read_text());matrix_protocol=json.loads((root/'protocol.json').read_text())
assert native_protocol['matrix_protocol_sha256']==sha(root/'protocol.json')
assert na['protocol_sha256']==sha(native/'protocol.json') and n['protocol_sha256']==sha(native/'protocol.json')
for path,h in native_protocol['inputs_sha256'].items():
 if path in matrix_protocol['inputs_sha256']:assert matrix_protocol['inputs_sha256'][path]==h
 assert sha(path)==h
truth={r['candidate_id']:r for r in n['rows']};reports=[]
for alpha in (0,256):
 rows={r['candidate_id']:r for r in m['reports'] if r['alpha']==alpha};assert set(rows)==set(truth)==set(range(9))
 ranking=sorted(rows,key=lambda c:(rows[c]['scores']['channel_net_span_sum'],rows[c]['scores']['predicted_channel_overuse_units'],c));assert ranking==m['ranking'][str(alpha)]
 selected=ranking[0];base=rows[0]['scores']['channel_net_span_sum'];deltas=[{'candidate_id':cid,'predicted_span_delta':rows[cid]['scores']['channel_net_span_sum']-base,'native_wirelength_delta':truth[cid]['wirelength']-truth[0]['wirelength']} for cid in range(1,9)]
 accept=truth[selected]['wirelength']<truth[0]['wirelength'] and truth[selected]['cpd_ns']<=truth[0]['cpd_ns'];false_improve=[r['candidate_id'] for r in deltas if r['predicted_span_delta']<0 and r['native_wirelength_delta']>=0]
 reports.append({'alpha':alpha,'ranking':ranking,'selected_candidate':selected,'native_selected_wirelength_delta':truth[selected]['wirelength']-truth[0]['wirelength'],'native_selected_cpd_delta_ns':truth[selected]['cpd_ns']-truth[0]['cpd_ns'],'postroute_accept':accept,'final_candidate':selected if accept else 0,'spearman_all9':spearman([rows[c]['scores']['channel_net_span_sum'] for c in range(9)],[truth[c]['wirelength'] for c in range(9)]),'spearman_candidates8':spearman([rows[c]['scores']['channel_net_span_sum'] for c in range(1,9)],[truth[c]['wirelength'] for c in range(1,9)]),'delta_mae':sum(abs(r['predicted_span_delta']-r['native_wirelength_delta']) for r in deltas)/8,'false_predicted_improvement_ids':false_improve,'deltas':deltas,'arm_wall_sum_s':sum(r['wall_s'] for r in rows.values()),'selected_native_launcher_wall_s':truth[selected]['launcher_wall_s']})
out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());(out/'prediction_metrics.py').write_text(Path('tools/prediction_metrics.py').read_text());receipt={'reports':reports,'matrix_full_wall_s':m['full_wall_s'],'matrix_preparation_wall_s':m['preparation_wall_s'],'source_evidence_sha256':{str(p):sha(p) for p in (root/'receipt.json',root/'matrix_audit.json',native/'receipt.json',native/'native_labels_audit.json')},'metric_source_sha256':sha('tools/prediction_metrics.py'),'evaluator_sha256':sha(__file__),'limitations':['previously explored single design, eight nonimproving candidates','postroute baseline protection not predictor benefit','single ordered runtime observations, excludes original sketch production and candidate generation','no timing proxy selection or unseen-family evidence']}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(reports))
