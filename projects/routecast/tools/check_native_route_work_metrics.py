"""Evidence parser checks: incomplete success fails; analysis does not mean zero."""
import json
from pathlib import Path
from native_route_work_metrics import extract
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];log=ROOT/'experiments/mux32_continuous_cold_baseline_2026-10-07/route.log';text=log.read_text();full=extract(text);assert full['iterations']==13 and full['rerouted_connection_attempts']==7908 and full['heap_pushes']==437198
first=next(line for line in text.splitlines() if line.lstrip().startswith('1    0.0'))
for changed in (text.replace(first+'\n','',1),text.replace('Successfully routed after 13 routing iterations.','Successfully routed after 12 routing iterations.'),text.replace('Successfully routed after 13 routing iterations.','Successfully routed after 13 routing iterations.\nSuccessfully routed after 13 routing iterations.')):
 try:extract(changed)
 except ValueError:pass
 else:raise AssertionError('incomplete evidence accepted')
analysis=extract('VPR succeeded\nFinal critical path delay (least slack): 2.87349 ns\n');assert analysis['iterations'] is None and analysis['heap_pushes'] is None and analysis['rerouted_connection_attempts'] is None
failed=extract(text.replace('Successfully routed after 13 routing iterations.','Routing failed.').replace('VPR succeeded','VPR failed'));assert not failed['routing_success'] and not failed['native_vpr_succeeded'] and failed['iterations'] is None and len(failed['iteration_rows'])==13
out=ROOT/'experiments/native_route_work_metrics_2026-10-07';r=dict(source_sha256=sha(Path(__file__)),parser_sha256=sha(ROOT/'tools/native_route_work_metrics.py'),input_sha256=sha(log),known_count_checks=True,incomplete_success_rejections=3,analysis_has_no_iteration_metric=True,failed_run_rows_retained=True,scope='Parser contract on authenticated real table and explicit malformed/incomplete variants. Failure variant synthetic, not actual native run failure.')
(out/'contract_verification.json').write_text(json.dumps(r,indent=2)+'\n');print('parser contract verified')
