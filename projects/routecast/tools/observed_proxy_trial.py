"""Posthoc baseline-context proxy on known matched-HPWL controls."""
import json,shutil
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from observed_timing_proxy import path_deltas
from prediction_metrics import spearman

out=Path('experiments/observed_timing_proxy_2026-10-04')
if out.exists():raise ValueError('fresh output required')
parent=Path('experiments/matched_hpwl_trial_2026-10-04');baseline=Path('experiments/lazy_repair_serialization_fix_2026-10-04/lazy_2.json');context=Path('experiments/baseline_timing_context_2026-10-04/observed_context.json');ep=json.loads(Path('experiments/pre_route_endpoints_2026-10-04/diffeq_endpoints.json').read_text());graph=Path(ep['inputs']['graph']['path'])
inputs={'graph':graph,'baseline':baseline,'context':context,'native_results':parent/'receipt.json','original_scores':parent/'decision.json'}
for cid in range(1,8):inputs[f'candidate_{cid}']=parent/f'candidate_{cid}_prediction.json'
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
p={'scope':'posthoc development replay on already-observed candidates; baseline-only partial timing context, not new validation','inputs':{k:{'path':str(v.resolve()),'sha256':sha(v)} for k,v in inputs.items()},'metric':'max baseline reported-path delta of summed group maximum channel span and switch Tdel ps','gate':'require both max deltas <=0, then original span/overuse/candidateID ranking','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');g=read_rr_graph(graph);b=json.loads(baseline.read_text());c=json.loads(context.read_text());scores=json.loads(inputs['original_scores'].read_text())['rows'];native=json.loads(inputs['native_results'].read_text())['native_results'];byid={r['candidate_id']:r for r in native};rows=[]
for cid in range(0,8):
    candidate=b if cid==0 else json.loads(inputs[f'candidate_{cid}'].read_text());r=path_deltas(g,b,candidate,c);result={k:r[k] for k in ('observed_path_max_span_delta','observed_path_max_switch_delay_delta_ps','covered_groups')};result.update(candidate_id=cid,proxy_gate=r['observed_path_max_span_delta']<=0 and r['observed_path_max_switch_delay_delta_ps']<=0)
    rows.append(result);(out/f'candidate_{cid}_detail.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(result),flush=True)
allowed={r['candidate_id'] for r in rows if r['proxy_gate']};selected=min((r for r in scores if r['candidate_id'] in allowed),key=lambda r:(r['channel_net_span_sum'],r['predicted_channel_overuse_units'],r['candidate_id']))['candidate_id']
for r in rows:r['native_cpd_delta_ns']=byid[r['candidate_id']]['cpd_ns']-byid[0]['cpd_ns']
receipt={'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'selected_candidate':selected,'selected_native_metrics':byid[selected],'baseline_native_metrics':byid[0],'cpd_delta_span_proxy_spearman':spearman([r['observed_path_max_span_delta'] for r in rows],[r['native_cpd_delta_ns'] for r in rows]),'scope':p['scope']}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
