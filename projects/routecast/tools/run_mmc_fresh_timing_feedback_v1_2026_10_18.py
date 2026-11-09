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
from run_native_fresh_timing_feedback_v1_2026_10_18 import predict
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_fresh_timing_feedback_v1_2026-10-18';D.mkdir();T=R/'experiments/mmc_fresh_initial_timing_inputs_v1_2026-10-18';tp=T/'verification.json';tv=json.loads(tp.read_text());assert tv['status']=='pass' and tv['all3_fresh_native_timing_and_unchanged_nodebase_inputs_loaded'];bindings={**closure([Path(__file__)]),**tv['bindings'],str(tp):sha(tp)}
g=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());ep=Path(g['previous_endpoint']);route=Path(g['previous_native_route']);source=json.loads(ep.read_text());oldq={q['connection_id']:q for q in source['connections']};cache=Cache();rows=[]
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,case_order=['case_01','case_02','case_03'],intervention='Fresh independently sampled per-placement native criticality float32 values only. Exact same audited retained_off initial, oldF/V2budgets, endpoint-only NET schedule,2round price/objective/overflow guards.',controls=['same-case frozen-old-criticality retained_on','raw_min_on','previous_native density'],scope='Isolated mechanism on already exposed layouts. Fresh snapshot production ~25seconds/case separately paid; these are cached admitted inputs, no continuous flow latency or promotion/heldout claim.'),f,indent=2)
with cache.installed():
 assert all(sha(p)==h for p,h in bindings.items())
 for case in ['case_01','case_02','case_03']:
  W=D/case;W.mkdir();warm=W/'warm';warm.mkdir();M=R/'experiments/mmc_multiplacement_models_v1_2026-10-18'/case;ap=M/'initial_independent_verification_v1.json';audit=json.loads(ap.read_text());assert audit['status']=='pass' and audit['all115572V2budgets_matched'] and all(sha(p)==h for p,h in audit['bindings'].items());target=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case/'demand/endpoints.json';stage=json.loads((target.parent.parent/'staged_input_verification_v1.json').read_text());b={**audit['bindings'],str(ap):sha(ap)}
  for name in ['initial.json','floors.json','history.json']:shutil.copyfile(M/'native_retained'/name,warm/name);assert sha(warm/name)==sha(M/'native_retained'/name);b[str(warm/name)]=sha(warm/name)
  with (warm/'verification.json').open('x') as f:json.dump(dict(schema='NATIVE_ENDPOINT_ANCHORED_WARM_INPUT_V2',bindings=b,endpoint=str(target),dirty_nets=stage['affected']['affected_net_ids'],native_staged_state_independent_xml_pass=True,zero_initial_history=True,native_anchored_budget_policy='NATIVE_ENDPOINT_ANCHORED_PROXY_V2',all_old_per_design_minima_independently_recertified=False,initializer_policy='native_retained',initial_independent_verification=str(ap),scope='Byte-identical audited retained_off initialization; only feedback timing input refreshed; old floor scope unchanged.'),f,indent=2)
 tick=time.perf_counter()
 raw=Raw(ep,route);g=Graph(raw.fields,raw.rc.increments,[raw.rc.initial(n) for n in range(len(raw.nodes))]);session=object.__new__(ModelSession);session.closed=False;session.active=False;session.owner=None;session.base=None;session.graph=raw.graph;session.digest=raw.digest;session.nodes=raw.nodes;session.fields=raw.fields;session.rc=raw.rc;session.search=g;session.net_digest=source['inputs']['net']['sha256'];session.net_names=source['net_names'];session.identities={cid:q['net_id'] for cid,q in oldq.items()};session.current_queries=None;session.binds=0;session.sources={**closure([Path(__file__)]),str(BINARY):sha(BINARY)}
 setup=time.perf_counter()-tick
 for case in ['case_01','case_02','case_03']:
  W=D/case;target=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case/'demand/endpoints.json';base=R/'experiments/mmc_multiplacement_feedback_inputs_v1_2026-10-18'/case/'base/verification.json';start=time.perf_counter();print('FRESH TIMING FEEDBACK START',case,flush=True)
  with (W/'model.log').open('x') as log,contextlib.redirect_stdout(log):predict(target,W/'model',base,T/case,W/'warm','local',session=session)
  r=json.loads((W/'model/receipt.json').read_text());assert sha(W/'model/initial.json')==sha(W/'warm/initial.json');row=dict(case=case,seconds=time.perf_counter()-start,overflow_before=r['rounds'][0]['overflow_before'],overflow_after=r['rounds'][-1]['overflow_after'],events=sum(len(x['events']) for x in r['rounds']),commits=[sum(e['status']=='COMMITTED' for e in x['events']) for x in r['rounds']]);rows.append(row);(D/'rows.json').write_text(json.dumps(rows,indent=2));bindings[str(W/'model/receipt.json')]=sha(W/'model/receipt.json');print('FRESH TIMING FEEDBACK DONE',row,flush=True)
 session.close();raw.close();assert all(sha(p)==h for p,h in bindings.items())
with (D/'receipt.json').open('x') as f:json.dump(dict(bindings=bindings,rows=rows,shared_graph_setup_seconds=setup,digest=cache.snapshot(),independent_final_and_events_audits_pending=True,scope='Cached isolated timing-input mechanism, not balanced runtime/fullflow or unseen quality evidence.'),f,indent=2)
