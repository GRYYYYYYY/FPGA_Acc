"""Run fixed RC-preserving audit stages after the forecast cohort is terminal."""
import json,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/mux_bundle_pressure_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert r['all_cases_retained'] and len(r['rows'])==9
stages=['verify_mux_bundle_pressure.py','evaluate_mux_bundle_pressure_metrics.py','verify_mux_bundle_pressure_metrics.py','compare_mux_bundle_pressure_metrics.py','compare_mux_bundle_pressure_paths.py','evaluate_mux_bundle_pressure_spatial.py','verify_mux_bundle_pressure_spatial.py'];rows=[]
assert not (out/'audit_pipeline.json').exists()
for name in stages:
 log=out/(name+'.log');t=time.monotonic()
 with log.open('w') as f:run=subprocess.run(['python3',str(root/'tools'/name)],cwd=root,stdout=f,stderr=subprocess.STDOUT)
 row={'stage':name,'source_sha256':sha(root/'tools'/name),'exit_code':run.returncode,'wall_s':time.monotonic()-t,'log_sha256':sha(log)};rows.append(row)
 (out/'audit_pipeline.json').write_text(json.dumps({'forecast_receipt_sha256':sha(out/'receipt.json'),'rows':rows,'complete':len(rows)==len(stages) and run.returncode==0},indent=2)+'\n');print(row,flush=True)
 if run.returncode:raise SystemExit(run.returncode)
