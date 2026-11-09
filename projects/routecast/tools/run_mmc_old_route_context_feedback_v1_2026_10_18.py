"""Complete both V2feedback-on arms after new independent initializer audits."""
import json,sys,time,contextlib,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
from persistent_raw_compiled_session_v1 import Session as Raw
from compact_persistent_native_model_session_v1 import Session as ModelSession
from compiled_criticality_tree_v1 import Graph,BINARY
from run_old_route_context_feedback_v1_2026_10_18 import predict
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_old_route_context_feedback_v1_2026-10-18';D.mkdir();S=R/'experiments/mmc_old_route_spatial_context_v1_2026-10-18';sp=S/'selection.json';vp=S/'independent_selection_verification_v1.json';v=json.loads(vp.read_text());assert v['status']=='pass';selection=json.loads(sp.read_text());bindings={**closure([Path(__file__)]),**v['bindings'],str(vp):sha(vp)}
geo=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());ep=Path(geo['previous_endpoint']);route=Path(geo['previous_native_route']);source=json.loads(ep.read_text());oldq={q['connection_id']:q for q in source['connections']}
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,case_order=['case_01','case_02','case_03'],radius=2,initial_policy='Exact independently audited retained_off V2 frame; zero history and original endpoint-only initial epochs retained',update_policy='Same2round criticality/price/objective/overflow guards with old-route spatial context NET schedule only',controls=['archived same-case retained_on endpoint closure','matched raw_min_on','previous_native density'],scope='Mechanism experiment on already exposed development cases. Cached independently audited initialization and timing/base inputs; no new all-old floor proof, no prospective unseen/promotion or end-to-end latency claim. All contexts/cases retained regardless of outcomes.'),f,indent=2)
cache=Cache();rows=[]
with cache.installed():
 assert all(sha(p)==h for p,h in bindings.items())
 for case in ['case_01','case_02','case_03']:
  O=D/case;O.mkdir();warm=O/'warm';warm.mkdir();M=R/'experiments/mmc_multiplacement_models_v1_2026-10-18'/case;ap=M/'initial_independent_verification_v1.json';audit=json.loads(ap.read_text());assert audit['status']=='pass' and audit['all115572V2budgets_matched'] and all(sha(p)==h for p,h in audit['bindings'].items());I=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case;target=I/'demand/endpoints.json';staged=json.loads((I/'staged_input_verification_v1.json').read_text());context_row=next(x for x in selection['rows'] if x['case']==case and x['radius']==2)
  wb={**audit['bindings'],str(ap):sha(ap),**v['bindings'],str(vp):sha(vp)}
  for name in ['initial.json','floors.json','history.json']:shutil.copyfile(M/'native_retained'/name,warm/name);assert sha(warm/name)==sha(M/'native_retained'/name);wb[str(warm/name)]=sha(warm/name)
  with (warm/'verification.json').open('x') as f:json.dump(dict(schema='NATIVE_ENDPOINT_ANCHORED_WARM_INPUT_V2',bindings=wb,endpoint=str(target),dirty_nets=context_row['net_ids'],endpoint_dirty_nets=staged['affected']['affected_net_ids'],context_case=case,context_radius=2,context_selection=str(sp),context_selection_proof=str(vp),native_staged_state_independent_xml_pass=True,zero_initial_history=True,native_anchored_budget_policy='NATIVE_ENDPOINT_ANCHORED_PROXY_V2',all_old_per_design_minima_independently_recertified=False,initializer_policy='native_retained',initial_independent_verification=str(ap),scope='Identical audited endpoint-only initialization; wider independently selected old-route context affects feedback schedule only. Cached oldF scope unchanged.'),f,indent=2)
 tick=time.perf_counter()
 raw=Raw(ep,route);g=Graph(raw.fields,raw.rc.increments,[raw.rc.initial(n) for n in range(len(raw.nodes))]);session=object.__new__(ModelSession);session.closed=False;session.active=False;session.owner=None;session.base=None;session.graph=raw.graph;session.digest=raw.digest;session.nodes=raw.nodes;session.fields=raw.fields;session.rc=raw.rc;session.search=g;session.net_digest=source['inputs']['net']['sha256'];session.net_names=source['net_names'];session.identities={cid:q['net_id'] for cid,q in oldq.items()};session.current_queries=None;session.binds=0;session.sources={**closure([Path(__file__)]),str(BINARY):sha(BINARY)}
 setup=time.perf_counter()-tick
 for case in ['case_01','case_02','case_03']:
  O=D/case;target=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case/'demand/endpoints.json';I=R/'experiments/mmc_multiplacement_feedback_inputs_v1_2026-10-18'/case;start=time.perf_counter();print('CONTEXT FEEDBACK START',case,flush=True)
  with (O/'model.log').open('x') as log,contextlib.redirect_stdout(log):predict(target,O/'model',I/'base/verification.json',I/'timing',O/'warm','local',session=session)
  r=json.loads((O/'model/receipt.json').read_text());assert sha(O/'model/initial.json')==sha(O/'warm/initial.json');row=dict(case=case,seconds=time.perf_counter()-start,overflow_before=r['rounds'][0]['overflow_before'],overflow_after=r['rounds'][-1]['overflow_after'],events=sum(len(x['events']) for x in r['rounds']),commits=[sum(e['status']=='COMMITTED' for e in x['events']) for x in r['rounds']]);rows.append(row);(D/'rows.json').write_text(json.dumps(rows,indent=2));bindings[str(O/'model/receipt.json')]=sha(O/'model/receipt.json');print('CONTEXT FEEDBACK DONE',row,flush=True)
 session.close();raw.close();assert all(sha(p)==h for p,h in bindings.items())
with (D/'receipt.json').open('x') as f:json.dump(dict(bindings=bindings,rows=rows,shared_graph_setup_seconds=setup,digest=cache.snapshot(),independent_final_and_events_audits_pending=True,scope='Cached-input development mechanism experiment; no timing comparison or fresh full-flow gain.'),f,indent=2)
