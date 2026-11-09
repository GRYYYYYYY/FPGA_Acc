"""Baseline-only context preparation, not a new prospective outcome trial."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from timing_context import route_pairs,observed_context
from bound_timing_proxy import bind,evaluate
out=Path('experiments/frisc_bound_timing_context_2026-10-05');capture=Path('experiments/frisc_graph_capture_2026-10-05');background=Path('experiments/frisc_topology_backgrounds_2026-10-05/baseline_prediction.json')
if out.exists():raise ValueError('fresh output required')
r=json.loads((capture/'receipt.json').read_text());assert r['exit_code']==0;entries={k:r['artifacts'][k] for k in ('rr_graph.xml','frisc.route','report_timing.setup.rpt','frisc.place','frisc.net')};assert all(sha(v['path'])==v['sha256'] for v in entries.values())
start=time.monotonic();g=read_rr_graph(entries['rr_graph.xml']['path']);baseline=json.loads(background.read_text());context=observed_context(Path(entries['report_timing.setup.rpt']['path']).read_text(),route_pairs(Path(entries['frisc.route']['path']).read_text()));bound=bind(g,baseline,context);zero=evaluate(g,baseline,baseline,bound);assert zero['observed_path_max_span_delta']==zero['observed_path_max_switch_delay_delta_ps']==0
out.mkdir();(out/'source').mkdir()
for f in ('prepare_frisc_bound_timing_context.py','timing_context.py','bound_timing_proxy.py','observed_timing_proxy.py'):(out/'source'/f).write_text(Path('tools',f).read_text())
(out/'context.json').write_text(json.dumps(bound,indent=2)+'\n');receipt={'baseline_capture_receipt_sha256':sha(capture/'receipt.json'),'baseline_prediction_sha256':sha(background),'inputs':entries,'source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')},'context_sha256':sha(out/'context.json'),'reported_paths':len(context['paths']),'covered_groups':zero['covered_groups'],'baseline_zero_delta_verified':True,'wall_s':time.monotonic()-start,'limitations':['baseline top100 setup paths only, not complete timing/criticality','frisc candidate outcomes already known; no retrospective gate result claimed prospective','baseline route/STA permitted context inputs, candidate native results unused','bind validates graph/path/context identity, not a signed trust boundary']};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k not in ('inputs','source_sha256')}))
