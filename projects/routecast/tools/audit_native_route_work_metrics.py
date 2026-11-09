"""Bind native router work counters to all archived development cold cases."""
import json
from pathlib import Path
from native_route_work_metrics import extract
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];parent=ROOT/'experiments/mux_full_cohort_cold_lifecycle_2026-10-06';rp=parent/'receipt.json';vp=parent/'verification.json';r=json.loads(rp.read_text());assert json.loads(vp.read_text())['receipt_sha256']==sha(rp);rows=[];inputs={str(rp):sha(rp),str(vp):sha(vp)}
for case in r['rows']:
 assert case['complete'] and case['error'] is None
 native=case['rounds'][0]['native']
 log=next(Path(f) for f in native['files'] if f.endswith('/run.log'));assert sha(log)==native['files'][str(log)];inputs[str(log)]=sha(log);metrics=extract(log.read_text());assert metrics['routing_success'] and metrics['native_vpr_succeeded'];rows.append(dict(width=case['width'],index=case['index'],**metrics))
new=ROOT/'experiments/mux32_continuous_cold_baseline_2026-10-07/route.log';inputs[str(new)]=sha(new);observed=extract(new.read_text());assert observed['iterations']==13
raw=ROOT/'experiments/mux32_continuous_native_2026-10-07/import.log';inputs[str(raw)]=sha(raw);analysis=extract(raw.read_text());assert analysis['iterations'] is None and not analysis['routing_success'] and analysis['native_vpr_succeeded']
# Independent token-count totals on actual row strings.
for file in [new]+[Path(f) for f in inputs if f.endswith('/run.log')]:
 data=extract(file.read_text());lines=[line for line in file.read_text().splitlines() if __import__('re').match(r'^\s*\d+\s+[0-9.]+\s+[0-9.]+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\(',line)]
 assert sum(int(line.split()[4]) for line in lines)==data['heap_pushes'];assert sum(int(line.split()[6]) for line in lines)==data['rerouted_connection_attempts']
out=ROOT/'experiments/native_route_work_metrics_2026-10-07';out.mkdir(exist_ok=True);result=dict(sources={str(p):sha(p) for p in (Path(__file__),ROOT/'tools/native_route_work_metrics.py')},inputs=inputs,rows=rows,fresh_w32m2=observed,analysis_only=analysis,scope='Authenticated12 development cold logs plus fresh baseline. Printed internal rounded times not external elapsed or stable speedup, no sums with nested phases. Analysis-only imports have no routing iteration metric (null, never zero). Supports router-work scope, not new routing execution/heldout gain.')
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print([(x['width'],x['index'],x['iterations'],x['printed_path_search_seconds'],x['printed_routing_seconds']) for x in rows]);print(observed)
