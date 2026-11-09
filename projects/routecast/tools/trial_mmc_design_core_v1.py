"""Two identical frozen episodes, shared graph/backend, full fresh-reference parity."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from mmc_design_core_v1 import Core
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_design_core_v1_2026-10-21';D.mkdir()
P=R/'experiments/mmc_native_cached_feedback_pilot_v1_2026-10-18/protocol.json';p=json.loads(P.read_text());assert all(sha(k)==h for k,h in p['bindings'].items())
files=[Path(__file__),P,R/'tools/mmc_design_core_v1.py',R/'tools/mmc_model_lifetime_v2.py',R/'tools/mmc_model_lifetime_v1.py',R/'tests/test_mmc_design_core_v1.py'];bindings={**p['bindings'],**{str(f):sha(f) for f in files}}
(D/'protocol.json').write_text(json.dumps({'bindings':bindings,'episodes':['A1','A2'],'scope':'Two identical frozen exposed MMC episode resets. One private immutable graph/RC and compiled graph core; independent price store/history/epochs/ledger/warm state per episode. All proofs, output files and boundary guards retained. Full fresh historical states/events required for both; same-input reset evidence only, different placements/configurations rejected. Core initialization, each setup/update/export, parity and final destruction charged.','native_calls':0},indent=2)+'\n')
args=p['command'][2:];old=Path(args[1]);core=Core();start=time.perf_counter();rows=[];backend_owner=None
try:
 for episode in ['A1','A2']:
  output=D/episode;current=list(args);current[1]=str(output);tick=time.perf_counter();m=core.open(*current)
  if backend_owner is None:backend_owner=core._backend
  else:assert core._backend is backend_owner
  assert not backend_owner.closed
  for index in [0,1]:m.step(m.current,index)
  result=m.export(m.current);assert core._token is None and not backend_owner.closed
  assert m.cleanup=={'calls':1,'search_closed':True,'graph_closed':True}
  episode_seconds=time.perf_counter()-tick;tick=time.perf_counter();parity={}
  for name in ['initial.json','floors.json','round0.json','round1.json','sketch.json','structural_cost_metrics.json']:
   parity[name]=sha(old/name)==sha(output/name);assert parity[name],(episode,name)
  before=json.loads((old/'receipt.json').read_text());after=json.loads((output/'receipt.json').read_text());semantic=lambda rs:[{k:v for k,v in r.items() if k not in ['seconds','state_file']} for r in rs];assert semantic(before['rounds'])==semantic(after['rounds'])
  rows.append({'episode':episode,'whole_episode_seconds':episode_seconds,'stages':m.costs,'parity_audit_seconds':time.perf_counter()-tick,'all_reference_state_bytes_exact':parity,'round_events_exact':True,'episode_price_and_graph_lease_closed':m.cleanup,'resident_backend_still_open':not backend_owner.closed,'core_stats':dict(core.stats),'result':dict(result)})
  print('SHARED CORE EPISODE PARITY',json.dumps(rows[-1]),flush=True)
 assert core.stats=={'graph_loads':1,'graph_reuses':1,'backend_builds':1,'backend_reuses':1,'price_stores':2,'episodes':2,'releases':2}
 assert all(sha(k)==h for k,h in bindings.items())
finally:
 tick=time.perf_counter();core.close();close_seconds=time.perf_counter()-tick
assert core.closed and backend_owner.closed and backend_owner.handle is None
receipt={'rows':rows,'core_stats':dict(core.stats),'resident_backend_closed_after_core_close':True,'core_close_seconds':close_seconds,'total_with_setup_reset_export_guards_and_parity_seconds':time.perf_counter()-start,'bindings':bindings,'scope':'Same fixed-input reset only. Both full states/events match original fresh execution. Shared design graph/RC/compiled workspace; distinct fresh price stores and model locals. No different-placement reuse, paired native/e2e gain or unseen-family evidence.'}
(D/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print('MMC DESIGN CORE TWO RESET EXACT PARITY PASS',receipt['total_with_setup_reset_export_guards_and_parity_seconds'],flush=True)
