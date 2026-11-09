"""Real full MMC raw control persistent-context parity, paid cold plus2calls."""
import json,time,sys,hashlib,contextlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from persistent_raw_control_session_v1 import Session
from source_binding_v2 import closure
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_persistent_raw_control_v1_2026-10-18';ref=R/'experiments/mmc_native_raw_control_v1_2026-10-18'
proof_path=ref/'independent_xml_verification_v2.json';proof=json.loads(proof_path.read_text());assert proof['all_paths_original_XML_fraction_RC_budget_singleparent_and_uniqueNET_pass'] and proof['old_floors_explicitly_unknown_not_falsely_certified'];assert all(sha(p)==h for p,h in proof['bindings'].items())
bindings={**closure([Path(__file__)]),**proof['bindings'],str(proof_path):sha(proof_path)}
gp=R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json';geometry=json.loads(gp.read_text());old=Path(geometry['previous_endpoint']);route=Path(geometry['previous_native_route']);new=R/'experiments/mmc_native_state_swap_inputs_v1_2026-10-18/demand/endpoints.json'
with (D/'execution_protocol.json').open('x') as f:json.dump(dict(bindings=bindings,order=['cold_source_graph_RC_native_import','update0','update1','reference_and_negative_checks_outside_paid_interval'],no_local_floor_or_criticality_setup=True,matched_balanced_local_comparison=False),f,indent=2)
start=time.perf_counter();session=Session(old,route);ids=(id(session.fields),id(session.rc),id(session.nativerows));rows=[]
for index in range(2):
 with (D/f'call{index}.log').open('x') as log,contextlib.redirect_stdout(log):
  result=session.predict(new,D/f'model{index}',generation=0)
 assert ids==(id(session.fields),id(session.rc),id(session.nativerows));rows.append({k:result[k] for k in ['total_call_seconds','dirty_search_and_certificates_seconds','recomputed_connections','preserved_connections','source_searches','overflow_units']})
paid=time.perf_counter()-start
# Full independent-reference equality after timed production path.
expected=json.loads((ref/'receipt.json').read_text());certs={Path(c['path']).name:c['sha256'] for c in expected['certificates']}
frame_reference=json.loads((ref/'initial.json').read_text())
for index in range(2):
 model=D/f'model{index}';actual=json.loads((model/'initial.json').read_text())
 assert actual==frame_reference
 assert sha(model/'initial.json')==sha(ref/'initial.json')
 assert len(list((model/'certificates').glob('source_*.json')))==54
 for name,digest in certs.items():assert sha(model/'certificates'/name)==digest
negative=[];snapshot=(id(session.state),id(session.nativerows),session.calls)
def reject(mode,fn):
 try:fn()
 except (ValueError,RuntimeError):negative.append(mode)
 else:raise AssertionError(mode+' admitted')
 assert snapshot==(id(session.state),id(session.nativerows),session.calls)
reject('stale_generation',lambda:session.predict(new,D/'stale',generation=1))
reject('boolean_generation',lambda:session.predict(new,D/'boolean',generation=False))
session.active=True;reject('nested',lambda:session.predict(new,D/'nested',generation=0));session.active=False
bad=json.loads(new.read_text());bad['graph_sha256']='0'*64;badpath=D/'stale_graph.json'
with badpath.open('x') as f:json.dump(bad,f)
reject('stale_graph',lambda:session.predict(badpath,D/'wrong_graph',generation=0))
session.close();reject('closed',lambda:session.predict(new,D/'closed',generation=0))
assert all(sha(p)==h for p,h in bindings.items())
for index in range(2):
 for p in (D/f'model{index}').rglob('*'):
  if p.is_file():bindings[str(p)]=sha(p)
result=dict(status='pass',bindings=bindings,cold_source_seconds=session.cold_seconds,rows=rows,paid_cold_plus2raw_updates_seconds=paid,all115572records_and_complete_ledgers_byte_identical=True,all54dirty_source_minimum_certificates_byte_identical_each_update=True,one_graph_RC_native_source_cache=True,inherited_floor_unknown_connections=115092,negative_cases=negative,compiled_criticality_workspace_loaded=False,old_floor_cache_loaded=False,scope='Two exposed MMC raw update replays with paid graph/RC/native import and proof-producing raw54source Dijkstra. Exact reference XML/Fraction certificates and full115572frame output. No native rerun, full workflow or balanced paired local timing comparison; no gain/promotion claim.')
with (D/'verification.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:v for k,v in result.items() if k!='bindings'}),flush=True)
