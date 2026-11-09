"""Exploratory score/native ordering diagnosis on already observed moves."""
import json,shutil
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from feedback_scores import scores
from prediction_metrics import spearman

out=Path('experiments/feedback_score_diagnosis_2026-10-04')
if out.exists():raise ValueError('fresh output required')
out.mkdir();(out/'source').mkdir()
for n in ('feedback_score_trial.py','feedback_scores.py','rr_graph.py','prediction_metrics.py','pre_route_endpoints.py'):shutil.copyfile(Path(__file__).with_name(n),out/'source'/n)
base=Path('experiments/multi_swap_2026-10-04');native=Path('experiments/native_swap_validation_normalized_v2_2026-10-04/receipt.json')
entries={'baseline':{'endpoints':Path('experiments/pre_route_endpoints_2026-10-04/diffeq_endpoints.json'),'prediction':Path('experiments/lazy_repair_serialization_fix_2026-10-04/lazy_2.json')}}
for step in range(1,5):entries[str(step)]={'endpoints':base/f'step_{step}_endpoints.json','prediction':base/f'step_{step}_fresh.json'}
graph=Path(json.loads(entries['baseline']['endpoints'].read_text())['inputs']['graph']['path'])
protocol={'scope':'posthoc development diagnosis, native outcomes already observed; no unseen or feedback benefit claim','score_formulas':['unique-net channel span sum','channel excess occupancy units','net endpoint bounding box HPWL'],'candidate_ids':list(entries),'inputs':{k:{n:{'path':str(p.resolve()),'sha256':sha(p)} for n,p in v.items()} for k,v in entries.items()},'graph':{'path':str(graph.resolve()),'sha256':sha(graph)},'native_receipt':{'path':str(native.resolve()),'sha256':sha(native)},'source_sha256':{p.name:sha(p) for p in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');g=read_rr_graph(graph);labels=json.loads(native.read_text());truth={'baseline':labels['baseline'],**{str(r['step']):r for r in labels['summary']}};rows=[]
for cid,v in entries.items():
    ep=json.loads(v['endpoints'].read_text());pred=json.loads(v['prediction'].read_text());row={'candidate_id':cid,**scores(g,ep,pred['node_occupancy']),'native_wirelength':truth[cid]['wirelength'],'native_cpd_ns':truth[cid]['cpd_ns']};rows.append(row)
analysis={}
for metric in ('channel_net_span_sum','predicted_channel_overuse_units','net_bbox_hpwl'):
    analysis[metric]={'native_wirelength_spearman':spearman([r[metric] for r in rows],[r['native_wirelength'] for r in rows]),'selected_candidate':min(rows,key=lambda r:(r[metric],r['candidate_id']))['candidate_id']}
result={'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'analysis':analysis,'scope':protocol['scope']}
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
