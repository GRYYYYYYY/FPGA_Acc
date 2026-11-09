"""Freeze on/off proposals before any new-cohort native candidate execution."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from bound_timing_proxy import evaluate
out=Path('experiments/frisc_bound_proxy_decision_v2_2026-10-05');bg=Path('experiments/frisc_timing_backgrounds_v2_2026-10-05');contextfile=Path('experiments/frisc_bound_timing_context_2026-10-05/context.json');prereg=Path('experiments/frisc_timing_prospective_v2_protocol_2026-10-05/protocol.json')
if out.exists():raise ValueError('fresh output required')
r=json.loads((bg/'receipt.json').read_text());assert len(r['rows'])==9 and r['inputs_unchanged'];protocol=json.loads((bg/'protocol.json').read_text());assert protocol['prospective_protocol_sha256']==sha(prereg);frozen=json.loads(prereg.read_text());assert frozen['inputs_sha256'][str(contextfile)]==sha(contextfile)
inputs={str(prereg):sha(prereg),str(contextfile):sha(contextfile),str(bg/'receipt.json'):sha(bg/'receipt.json'),**protocol['inputs_sha256']}
files={cid:bg/('baseline_prediction.json' if cid==0 else f'candidate_{cid}_prediction.json') for cid in range(9)};inputs.update({str(p):sha(p) for p in files.values()});assert all(sha(p)==h for p,h in inputs.items());start=time.monotonic();e=json.loads(Path('experiments/frisc_endpoints_2026-10-05/endpoints.json').read_text());g=read_rr_graph(e['inputs']['graph']['path']);baseline=json.loads(files[0].read_text());bound=json.loads(contextfile.read_text());rows=[]
for cid in range(9):
 candidate=json.loads(files[cid].read_text());proxy=evaluate(g,baseline,candidate,bound);row={'candidate_id':cid,**r['rows'][cid]['scores'],'proxy':proxy,'proxy_gate':proxy['observed_path_max_span_delta']<=0 and proxy['observed_path_max_switch_delay_delta_ps']<=0};rows.append(row)
key=lambda row:(row['channel_net_span_sum'],row['predicted_channel_overuse_units'],row['candidate_id'])
on=min((x for x in rows if x['proxy_gate']),key=key)['candidate_id'];off=min(rows,key=key)['candidate_id'];assert rows[0]['proxy_gate'];assert all(sha(p)==h for p,h in inputs.items());out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());decision={'on_candidate':on,'off_candidate':off,'rows':rows,'input_sha256':inputs,'source_sha256':sha(__file__),'wall_s':time.monotonic()-start,'scope':'new disjoint cohort proposals frozen from sketches and baseline-only context before native labels; same explored design, no family claim','limitations':['proxy top100 paths only, CPD gate must follow native','original background and context costs separate']};(out/'decision.json').write_text(json.dumps(decision,indent=2)+'\n');print(json.dumps({'on_candidate':on,'off_candidate':off,'proxy_admitted_ids':[x['candidate_id'] for x in rows if x['proxy_gate']]}))
