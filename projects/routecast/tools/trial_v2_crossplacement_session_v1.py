"""Existing V2 retained policy across all3 frozen MMC layouts, then return to A."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from v2_crossplacement_session_v1 import Session
R=Path(__file__).resolve().parents[1];D=R/'experiments/v2_crossplacement_session_v1_2026-10-21';D.mkdir()
I=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18';F=R/'experiments/mmc_multiplacement_feedback_inputs_v1_2026-10-18';M=R/'experiments/mmc_multiplacement_models_v1_2026-10-18'
bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/v2_crossplacement_session_v1.py',R/'tests/test_v2_crossplacement_session_v1.py',R/'tools/compact_persistent_native_model_session_v1.py',R/'tools/run_native_endpoint_v2_feedback_v1_2026_10_18.py',R/'tools/mmc_design_core_v1.py']}
def bind(path):
 d=json.loads(path.read_text());bindings[str(path)]=sha(path)
 for p,h in d.get('bindings',{}).items():
  if p in bindings:assert bindings[p]==h,p
  bindings[p]=h
 return d
cases={};compat=[];first=None
for case in ['case_01','case_02','case_03']:
 epf=I/case/'demand/endpoints.json';ep=json.loads(epf.read_text());bindings[str(epf)]=sha(epf)
 for spec in ep['inputs'].values():
  path,h=spec['path'],spec['sha256']
  if path in bindings:assert bindings[path]==h,path
  bindings[path]=h
 b=bind(F/case/'base/verification.json');bind(F/case/'timing/verification.json');warm=bind(M/case/'native_retained/verification.json');audit=bind(M/case/'feedback_audits/verification.json');ref=M/case/'feedback_on/native_retained';rp=bind(ref/'protocol.json');rr=bind(ref/'receipt.json')
 assert warm['schema']=='NATIVE_ENDPOINT_ANCHORED_WARM_INPUT_V2' and warm['native_anchored_budget_policy']=='NATIVE_ENDPOINT_ANCHORED_PROXY_V2'
 assert audit['status']=='pass' and audit['both_final_and_all_event_audits_pass']
 for path,h in rr['files'].items():
  if path in bindings:assert bindings[path]==h,path
  bindings[path]=h
 basefile=F/case/'base/node_base.u64';basehash=sha(basefile);bindings[str(basefile)]=basehash
 ids={q['connection_id']:q['net_id'] for q in ep['connections']};assert len(ids)==len(ep['connections'])
 static=(ep['graph_sha256'],ep['inputs']['net']['sha256'],ep['net_names'],ids,basehash,b['nodes'],b['scale'])
 if first is None:first=static;oldqs={q['connection_id']:(q['source'],q['sink']) for q in ep['connections']}
 else:assert static==first,'incompatible static design'
 compat.append({'case':case,'graph_sha256':ep['graph_sha256'],'net_sha256':ep['inputs']['net']['sha256'],'base_sha256':basehash,'connections':len(ids),'changed_endpoint_connections_vs_case01':sum(oldqs[q['connection_id']]!=(q['source'],q['sink']) for q in ep['connections']),'placement_sha256':ep['inputs']['place']['sha256'],'budget_policy':warm['native_anchored_budget_policy']})
 cases[case]=(epf,F/case/'base/verification.json',F/case/'timing',M/case/'native_retained',ref)
(D/'protocol.json').write_text(json.dumps({'bindings':bindings,'compatibility':compat,'order':['case_01','case_02','case_03','case_01'],'policy':'Original NATIVE_ENDPOINT_ANCHORED_PROXY_V2 native_retained-on, original two rounds; V1 proxy not substituted.','scope':'All existing development layouts in frozen order plus return-to-A. Prepared complete initializer/timing/base proofs; no new native/source/floor capture. Current whole-byte guards retained, graph data privately sealed, lease failures close backend. Full states/events must match each original audited reference. No total-time or heldout admission.','native_calls':0},indent=2)+'\n')
assert all(sha(p)==h for p,h in bindings.items());print('ALL3 STATIC COMPATIBILITY AND INPUT BINDINGS PASS',flush=True)
start=time.perf_counter();tick=start;session=Session(cases['case_01'][0]);setup=time.perf_counter()-tick;backend=session.search;rows=[]
try:
 for index,case in enumerate(['case_01','case_02','case_03','case_01']):
  ep,base,timing,warm,ref=cases[case];tick=time.perf_counter();ticket=session.reserve(ep);result=session.execute(ticket,D/f'{index}_{case}',base,timing,warm);elapsed=time.perf_counter()-tick
  assert not session.active and not backend.closed and session.search is backend
  tick=time.perf_counter();parity={}
  for name in ['initial.json','floors.json','round0.json','round1.json','sketch.json','structural_cost_metrics.json']:
   parity[name]=sha(D/f'{index}_{case}'/name)==sha(ref/name);assert parity[name],(case,name)
  before=json.loads((ref/'receipt.json').read_text());after=json.loads((D/f'{index}_{case}'/'receipt.json').read_text());semantic=lambda rs:[{k:v for k,v in r.items() if k not in ['seconds','state_file']} for r in rs];assert semantic(before['rounds'])==semantic(after['rounds'])
  try:session.execute(ticket,'unused',base,timing,warm)
  except RuntimeError:stale_rejected=True
  else:raise AssertionError('stale lease accepted')
  rows.append({'case':case,'index':index,'whole_model_reserve_execute_seconds':elapsed,'reference_comparison_seconds':time.perf_counter()-tick,'full_state_bytes_exact':parity,'round_events_exact':True,'stale_lease_rejected':stale_rejected,'backend_reused_and_open':True,'binds':session.binds,'result':result})
  print('CROSSPLACEMENT FULL PARITY',json.dumps(rows[-1]),flush=True)
 assert session.binds==4 and all(sha(p)==h for p,h in bindings.items())
finally:
 tick=time.perf_counter();session.close();close_seconds=time.perf_counter()-tick
assert backend.closed and backend.handle is None
receipt={'compatibility':compat,'rows':rows,'design_setup_seconds':setup,'backend_closed_after_final_close':True,'close_seconds':close_seconds,'total_with_model_guards_exports_and_reference_audits_seconds':time.perf_counter()-start,'bindings':bindings,'scope':'Cross-placement state/event correctness for exposed MMC V2 policy only. Compatibility/proof preregistration audit precedes total timer; setup and every model/export/parity/final source check after it included. No new native/floor/source capture, strict unseen, paired speedup or original full9 claim.'}
(D/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print('V2 THREE PLACEMENTS RETURN-A FULL PARITY PASS',flush=True)
