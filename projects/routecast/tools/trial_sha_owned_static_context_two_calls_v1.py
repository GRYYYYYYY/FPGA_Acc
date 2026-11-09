"""Cold+warm full model calls, all dynamic work and independent audits retained."""
import json,runpy,sys,subprocess,time,ast
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from owned_static_rr_context_v1 import diagnostics
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_owned_static_context_two_calls_v1_2026-10-10';assert not D.exists();D.mkdir();ep=R/'experiments/sha1_compact_json_complete_workflow_v1_2026-10-10/seed/demand/sha1/endpoints.json';driver=R/'tools/run_sha1_owned_static_context_handoff_v1.py';auditor=R/'tools/run_shared_actual_old_linear_direct_lattice_audits_v4.py';contract=R/'experiments/owned_static_rr_context_full_sha_v1_2026-10-10/verification.json';proof=json.loads(contract.read_text());assert proof['every_node_subtree_CSR_RC_increment_initial_class_switch_exact'] and all(sha(k)==h for k,h in proof['bindings'].items());bindings=closure([Path(__file__).resolve(),driver,auditor]);bindings.update({str(ep):sha(ep),str(contract):sha(contract)});(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Two full same-endpoint model calls only to test static context ownership, cold cost paid first, current input digests/queries refreshed eachaccess. No changed placement or true incremental-update claim. Original all6273queries/floors/twofeedback rounds/handoff and fresh independentfullaudits eachcall, no dynamic/history/label reuse. Not complete native/canonicalworkflow/family/hardware gain.'),indent=2)+'\n');rows=[]
for arm in ['cold_context','warm_context']:
 B=D/arm;B.mkdir();tick=time.perf_counter();sys.argv=[str(driver),'sha1',str(ep),str(B/'handoff'),str(B/'native'),str(B/'model')]
 with (B/'producer.log').open('w') as log:
  oldout=sys.stdout;sys.stdout=log
  try:runpy.run_path(str(driver),run_name='__main__')
  finally:sys.stdout=oldout
 model_seconds=time.perf_counter()-tick
 with (B/'audit.log').open('w') as log:code=subprocess.run([sys.executable,str(auditor),str(B/'model'),'sha1'],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 assert code==0;pp=B/'model/shared_audit_receipt.json';v=json.loads(pp.read_text());assert v['all_three_complete_audits_pass'] and v['fresh_independent_graph_context'] and all(sha(k)==h for k,h in v['bindings'].items());bindings[str(pp)]=sha(pp);rows.append(dict(arm=arm,full_model_handoff_seconds=model_seconds,full_model_handoff_independent_audit_seconds=time.perf_counter()-tick,context=diagnostics()));(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows[-1],flush=True)
assert diagnostics()['loads']==1 and diagnostics()['accesses']==2
for rel in ['model/initial.json','model/sketch.json','model/round0.json','model/round1.json','native/subset.json','native/bindings.json']:
 a=D/'cold_context'/rel;b=D/'warm_context'/rel;assert json.loads(a.read_text())==json.loads(b.read_text());bindings.update({str(a):sha(a),str(b):sha(b)})
assert (D/'cold_context/native/seed.route').read_bytes()==(D/'warm_context/native/seed.route').read_bytes()
assert all(sha(k)==h for k,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all_static_contexts_owned_and_current_queries_reloaded=True,all_full_states_handoff_equal=True,scope='Full same-input two-call static-context component cost only, all dynamicwork/audits retained. No changed-endpoint/fullnativeworkflow/strictfamily/hardware benefit established.'),indent=2)+'\n');print('FULL TWO CALL PARITY PASS')
