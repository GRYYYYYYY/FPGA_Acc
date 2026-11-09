"""Contemporary stateless producer repeat control, identical input and proof."""
import subprocess,os,time,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];out=R/'experiments/native_live_search_stateless_repeat_2026-10-07';out.mkdir();start=time.perf_counter();rows=[]
for i in range(3):
 subprocess.run([sys.executable,str(R/'tools/native_route_transaction/check_live_stateless_step.py')],env=dict(os.environ,ROUTECAST_REUSE_STEP=str(i)),check=True,timeout=160)
 rows.append(json.loads((out/f'step_{i}/receipt.json').read_text()))
assert len({r['producer']['candidate_sha256'] for r in rows})==1
(out/'receipt.json').write_text(json.dumps(dict(total_seconds=time.perf_counter()-start,rows=rows,scope='Three stateless repeated identical development fixtures. Identical native bootstrap/export/producer/import/final proof. Comparison isolates graph context reuse, not cold native routing or changing-placement sequence.'),indent=2)+'\n');print('STATELESS PASS')
