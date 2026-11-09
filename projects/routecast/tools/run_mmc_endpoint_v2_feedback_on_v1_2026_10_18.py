"""Complete both V2feedback-on arms after new independent initializer audits."""
import json,sys,time,contextlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
from persistent_raw_compiled_session_v1 import Session as Raw
from compact_persistent_native_model_session_v1 import Session as ModelSession
from compiled_criticality_tree_v1 import Graph,BINARY
from run_native_endpoint_v2_feedback_v1_2026_10_18 import predict
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_retained_native_initializers_v1_2026-10-18';O=D/'feedback_on';O.mkdir(exist_ok=False);ap=D/'initial_independent_verification_v1.json';audit=json.loads(ap.read_text());assert audit['status']=='pass' and audit['all115572V2budgets_matched'];assert all(sha(p)==h for p,h in audit['bindings'].items());bindings={**closure([Path(__file__)]),**audit['bindings'],str(ap):sha(ap)}
geo=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());ep=Path(geo['previous_endpoint']);route=Path(geo['previous_native_route']);target=R/'experiments/mmc_native_state_swap_inputs_v1_2026-10-18/demand/endpoints.json';I=R/'experiments/mmc_native_feedback_inputs_v1_2026-10-18';source=json.loads(ep.read_text());new=json.loads(target.read_text());oldq={q['connection_id']:q for q in source['connections']};dirty={q['net_id'] for q in new['connections'] if (q['source'],q['sink'])!=(oldq[q['connection_id']]['source'],oldq[q['connection_id']]['sink'])}
for mode in ['raw_min','native_retained']:
 warm=D/mode;wp=warm/'verification.json'
 with wp.open('x') as f:json.dump(dict(schema='NATIVE_ENDPOINT_ANCHORED_WARM_INPUT_V2',bindings={**audit['bindings'],str(ap):sha(ap)},endpoint=str(target),dirty_nets=sorted(dirty),native_staged_state_independent_xml_pass=True,zero_initial_history=True,native_anchored_budget_policy='NATIVE_ENDPOINT_ANCHORED_PROXY_V2',all_old_per_design_minima_independently_recertified=False,initializer_policy=mode,initial_independent_verification=str(ap),scope='Separately originalXML/Fraction verified new V2initializer; old minima source scope unchanged.'),f,indent=2)
 bindings[str(wp)]=sha(wp)
cache=Cache();tick=time.perf_counter()
with cache.installed():
 raw=Raw(ep,route);g=Graph(raw.fields,raw.rc.increments,[raw.rc.initial(n) for n in range(len(raw.nodes))]);session=object.__new__(ModelSession);session.closed=False;session.active=False;session.owner=None;session.base=None;session.graph=raw.graph;session.digest=raw.digest;session.nodes=raw.nodes;session.fields=raw.fields;session.rc=raw.rc;session.search=g;session.net_digest=source['inputs']['net']['sha256'];session.net_names=source['net_names'];session.identities={cid:q['net_id'] for cid,q in oldq.items()};session.current_queries=None;session.binds=0;session.sources={**closure([Path(__file__)]),str(BINARY):sha(BINARY)}
 setup=time.perf_counter()-tick;rows=[]
 for mode in ['raw_min','native_retained']:
  start=time.perf_counter()
  with (O/(mode+'.log')).open('x') as log,contextlib.redirect_stdout(log):result=predict(target,O/mode,I/'base/verification.json',I/'timing',D/mode,'local',session=session)
  elapsed=time.perf_counter()-start;assert sha(O/mode/'initial.json')==sha(D/mode/'initial.json');r=json.loads((O/mode/'receipt.json').read_text());rows.append(dict(mode=mode,seconds=elapsed,overflow_before=r['rounds'][0]['overflow_before'],overflow_after=r['rounds'][-1]['overflow_after'],commits=[sum(e['status']=='COMMITTED' for e in x['events']) for x in r['rounds']],events=sum(len(x['events']) for x in r['rounds'])));print('V2 FEEDBACK DONE',rows[-1],flush=True)
  bindings[str(O/mode/'receipt.json')]=sha(O/mode/'receipt.json')
 session.close();raw.close();assert all(sha(p)==h for p,h in bindings.items())
with (O/'receipt.json').open('x') as f:json.dump(dict(bindings=bindings,rows=rows,source_graph_import_and_compiled_workspace_seconds=setup,digest=cache.snapshot(),initial_frame_audit_transferred_by_byte_equality=True,final_and_events_independent_audits_pending=True,scope='Both feedback-on arms executed from separately verified V2initials with same original2round algorithm. One exposed case; not balanced latency, globaloldFproduction or fresh complete native workflow.'),f,indent=2)
print('BOTH ON ARMS COMPLETE',flush=True)
