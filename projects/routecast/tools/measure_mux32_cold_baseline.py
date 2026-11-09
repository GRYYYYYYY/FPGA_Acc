"""External cold-process wall timer, including its metadata checks and startup."""
import json,subprocess,sys,time
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];script=ROOT/'tools/run_mux32_continuous_cold_baseline.py';start=time.perf_counter();code=subprocess.run([sys.executable,str(script)],cwd=ROOT).returncode;elapsed=time.perf_counter()-start
out=ROOT/'experiments/mux32_continuous_cold_baseline_2026-10-07';result=dict(source_sha256=sha(Path(__file__)),script_sha256=sha(script),exit_code=code,external_process_seconds=elapsed,receipt_sha256=sha(out/'receipt.json') if (out/'receipt.json').exists() else None,scope='Entire cold process external timer includes child protocol hashes and startup; workflow wrapper setup/generation outside its continuous clock. Small setup scope difference explicit; not raw-input preparation or stable performance claim.')
(out/'external_timer.json').write_text(json.dumps(result,indent=2)+'\n')
if code:raise SystemExit(code)
