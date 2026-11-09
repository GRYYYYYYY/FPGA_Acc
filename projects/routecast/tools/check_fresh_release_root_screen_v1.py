"""Compare forward root checker to independent reverse certificates, all16 cases."""
import sys,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from fresh_release_root_screen_v1 import FreshRootScreen
reference=R/'experiments/misex_fresh_root_diagnosis_v1_2026-10-07';rp=reference/'receipt.json';vp=reference/'verification.json';r=json.loads(rp.read_text());v=json.loads(vp.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());parent=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07';bp=parent/'misex3/batch14.json';fp=parent/'misex3/floors.json';ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';out=R/'experiments/fresh_root_screen_contract_v1_2026-10-07';out.mkdir();bindings={**closure([Path(__file__)]),str(rp):sha(rp),str(vp):sha(vp),str(bp):sha(bp),str(fp):sha(fp),str(ep):sha(ep)};bindings.update(r['bindings']);(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='All16 raw forward minima against independently certified reverse original-graph necessary conditions. JSON witness equality not required for tied minimum paths. No new joint success or gain.'))+'\n')
graph,digest,nodes,f,rc,queries=load_endpoints(ep);event=json.loads(bp.read_text());floors={(d['source'],d['sink']):d['minimum_integer'] for d in json.loads(fp.read_text())};start=time.perf_counter();screen=FreshRootScreen(f,rc,event['before_records'],floors);rows=[]
for index in range(4):
 expected=[d for d in r['rows'] if d['release_index']==index];result=screen.check(expected[0]['release'],event['selection']['queries'])
 for got,ref in zip(result['queries'],expected):
  assert got['query']==ref['query'] and got['budget']==ref['budget'] and got['ordinary_budget_feasible']==ref['ordinary_budget_feasible'];assert (None if got['witness'] is None else got['witness']['minimum_integer'])==ref['minimum_integer']
  if got['witness'] is not None:assert screen.rc.path(got['query']['source'],got['query']['sink'],got['witness']['physical_edge_ids'])==ref['minimum_integer']
 assert screen.check(expected[0]['release'],event['selection']['queries'])==result;rows.append(result)
elapsed=time.perf_counter()-start
for invalid in ([],[event['selection']['queries'][0]]*2,[dict(connection_id=event['before_records'][0]['connection_id'],net_id=312,source=12205,sink=11048)]):
 try:screen.check(event['initial_release_net_ids'],invalid)
 except ValueError:pass
 else:raise AssertionError('bad selected scope accepted')
assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows,all16_independent_minima_equal=True,invalid_selected_scopes_rejected=True,construction_and_checks_seconds=elapsed,bindings=bindings),indent=2)+'\n');print('PASS16 fresh-root necessary conditions',elapsed,flush=True)
