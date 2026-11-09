"""Fresh native qualification+selected-state handoff cost, prediction excluded."""
import json,subprocess,time,sys
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context_cached import PersistentRCContext
from native_route_ledger_import_compact import import_native_ledger
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/owner50_cached_native_acceptance_cost_2026-10-07'
if sys.argv[1:]==['--initialize']:
 out.mkdir();items=[]
 for i in (2,3):
  old=f'mux_native_joint_50ps_w8m{i}';new=f'mux_cached_native_cost_50ps_w8m{i}'
  files=[]
  for prefix in ('trial','verify'):
   src=ROOT/f'tools/{prefix}_{old}_quality_gate.py';dst=ROOT/f'tools/{prefix}_{new}_quality_gate.py';assert not dst.exists();dst.write_text(src.read_text().replace(old,new));files.append(dst)
  items.append(dict(width=8,index=i,sources={str(f):sha(f) for f in files},producer=str(files[0]),verifier=str(files[1]),output=new+'_quality_gate_2026-10-07'))
 (out/'protocol.json').write_text(json.dumps(dict(cases=items,driver_sha256=sha(Path(__file__)),cache_sources={str(ROOT/'tools'/name):sha(ROOT/'tools'/name) for name in ('cached_rr_endpoint_context.py','persistent_rc_context_cached.py','integer_rc_context_memo.py','native_route_ledger_import_compact.py')},binary_sha256=sha(ROOT/'build/native_joint_qor_gate_2026-10-07/gate_vpr'),scope='Two known50ps development modelPASS cases only, fresh native same-target cold+candidate joint gate, selected originalcanonical FULLSTA, independent candidate/reference/selected physical+wire checks, target context/selected ledger import and serialization. Perprocess phase clock includes startup/setup. Estimator/floor/input preparation and10 fallback cases NOT executed here; not full12 live accepted lifecycle or speedup. Gate/verification/import phases separately recorded to avoid nested timer addition.'),indent=2)+'\n');print('Native acceptance cost protocol frozen');raise SystemExit
p=json.loads((out/'protocol.json').read_text());assert p['driver_sha256']==sha(Path(__file__));assert all(sha(f)==h for f,h in p['cache_sources'].items());rows=[]
for case in p['cases']:
 assert all(sha(f)==h for f,h in case['sources'].items());start=time.perf_counter();phases={}
 for name,key in [('native_gate_and_selected_canonical','producer'),('independent_verification','verifier')]:
  begin=time.perf_counter()
  with (out/f"w8_m{case['index']}_{name}.log").open('w') as stream:code=subprocess.run([sys.executable,case[key]],stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
  phases[name]=time.perf_counter()-begin;assert code==0
 base=ROOT/'experiments'/case['output'];r=json.loads((base/'receipt.json').read_text());v=json.loads((base/'verification.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json');assert v['rows'][0]['selected']=='predicted';native=r['rows'][0]['reload'];assert native['mismatches']==native['fixups']==0
 route=next(Path(f) for f in native['files'] if f.endswith('/design.route'));assert sha(route)==native['files'][str(route)];spec=json.loads((base/'protocol.json').read_text())['cases'][0]
 begin=time.perf_counter();ctx=PersistentRCContext(spec['target']);state=import_native_ledger(ctx,route);assert len(state.records)==466
 snapshot=out/f"w8_m{case['index']}_accepted_state.json";snapshot.write_text(json.dumps(dict(revision=1,records=[state.records[k] for k in sorted(state.records)],ledger=dict(state.ledger),endpoint_metadata=ctx.endpoint_metadata,scale=ctx.rc.scale),indent=2)+'\n');phases['target_context_import_serialization']=time.perf_counter()-begin
 rows.append(dict(width=8,index=case['index'],phases_seconds=phases,total_wall_seconds=time.perf_counter()-start,gate_receipt_sha256=sha(base/'receipt.json'),gate_verification_sha256=sha(base/'verification.json'),snapshot_sha256=sha(snapshot),selected_route=str(route),selected_route_sha256=sha(route),metrics=v['rows'][0]))
 (out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows,scope=p['scope']),indent=2)+'\n');print(rows[-1],flush=True)

from cached_rr_endpoint_context import STATS
(out/'rr_cache_stats.json').write_text(json.dumps(dict(STATS),indent=2)+'\n')
