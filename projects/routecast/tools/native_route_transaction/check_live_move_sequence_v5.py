"""Three live transactions; pay server startup and initial graph once."""
import subprocess,os,time,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];out=R/'experiments/native_live_search_move_sequence_v5_2026-10-07';out.mkdir();sock=out/'mailbox';start=time.perf_counter()
with (out/'server.log').open('w') as log:
 server=subprocess.Popen([sys.executable,str(R/'tools/native_route_transaction/live_search_server_v5.py'),str(sock),'3'],stdout=log,stderr=subprocess.STDOUT)
 try:
  deadline=time.monotonic()+10
  while not (sock/'ready').exists():
   assert server.poll() is None and time.monotonic()<deadline;time.sleep(.02)
  rows=[]
  for i in range(3):
   env=dict(os.environ,ROUTECAST_SEARCH_MAILBOX=str(sock),ROUTECAST_REUSE_STEP=str(i));subprocess.run([sys.executable,str(R/'tools/native_route_transaction/check_live_move_step_v5.py')],env=env,check=True,timeout=160)
   rows.append(json.loads((out/f'step_{i+1}/receipt.json').read_text()))
  assert server.wait(timeout=10)==0
  assert [r['producer']['context_reused'] for r in rows]==[False,True,True]
  assert len({r['producer']['candidate_sha256'] for r in rows})==3
  assert len({r['producer']['inputs'][next(k for k in r['producer']['inputs'] if k.endswith('design.place'))] for r in rows})==3
  (out/'receipt.json').write_text(json.dumps(dict(total_seconds=time.perf_counter()-start,rows=rows,scope='Three serial changing prepared placement development-fixture live exports; worker reuses graph/RC/inventory only, reconstructs all owner/search state each request. Startup/initialization paid once. Initial seed-routing/report generation excluded; these are prepared initial routed states, not online seed-update/full cold cost comparison.'),indent=2)+'\n');print('REUSE PASS',[(r['native_including_producer_seconds'],r['producer']['producer_seconds']) for r in rows])
 finally:
  if server.poll() is None:server.terminate();server.wait(timeout=10)

