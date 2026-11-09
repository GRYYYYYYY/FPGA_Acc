"""Actual legal endpoint change; complete fresh dynamic model versus original full rebuild."""
import json,runpy,sys,subprocess,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from owned_static_rr_context_v1 import diagnostics
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_whole_net_initial_cache_actual_swap_v2_2026-10-10';assert not D.exists();D.mkdir();scope=R/'experiments/sha_legal_swap_native_scope_v1_2026-10-10/verification.json';v=json.loads(scope.read_text());assert v['all6770_endpoint_types_classes_capacity_bbox_pass'] and v['all6273_physical_and497_ignored_partition_pass'] and all(sha(k)==h for k,h in v['bindings'].items());old=Path(v['old_endpoints']);new=Path(v['new_endpoints']);driver=R/'tools/run_sha1_whole_net_initial_cache_handoff_v2.py';reference=R/'tools/run_sha1_actual_old_linear_undo_native_handoff_v1.py';audit=R/'tools/run_shared_actual_old_linear_direct_lattice_audits_v4.py';bindings=closure([Path(__file__).resolve(),driver,reference,audit]);bindings.update({str(p):sha(p) for p in [scope,old,new]});(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,old_endpoints=str(old),new_endpoints=str(new),changed_connections=v['physical_changed_connection_ids'],changed_nets=v['physical_changed_net_ids'],order=['old_cold_context','new_warm_context','new_original_rebuild'],scope='Actual first-block-ID sameCLB legal swap; Complete unchanged NET zero-price initial searches reused from process-local first-call cache; changed whole NETs recomputed, all ledgers and feedback rebuilt. Owned RR/RC context only. Fresh independent full3audits eachphase. Compare new warm to independent original complete rebuild, no native final route labels generated/read, no strictfamily/HDL/hardware/fullworkflow gain.'),indent=2)+'\n');rows=[]
from whole_net_zero_price_search_cache_v2 import diagnostics as cache_diagnostics
for arm,ep in [('old_cold_context',old),('new_warm_context',new),('new_original_rebuild',new)]:
 B=D/arm;B.mkdir();tick=time.perf_counter();args=['sha1',str(ep),str(B/'handoff'),str(B/'native'),str(B/'model')]
 if arm!='new_original_rebuild':
  sys.argv=[str(driver),*args]
  with (B/'producer.log').open('w') as log:
   previous=sys.stdout;sys.stdout=log
   try:runpy.run_path(str(driver),run_name='__main__')
   finally:sys.stdout=previous
 else:
  with (B/'producer.log').open('w') as log:code=subprocess.run([sys.executable,str(reference),*args],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
  assert code==0
 producer_seconds=time.perf_counter()-tick
 with (B/'audit.log').open('w') as log:code=subprocess.run([sys.executable,str(audit),str(B/'model'),'sha1'],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 assert code==0;p=B/'model/shared_audit_receipt.json';proof=json.loads(p.read_text());assert proof['all_three_complete_audits_pass'] and proof['fresh_independent_graph_context'] and all(sha(k)==h for k,h in proof['bindings'].items());bindings[str(p)]=sha(p);rows.append(dict(arm=arm,complete_model_handoff_seconds=producer_seconds,complete_model_handoff_independent_audit_seconds=time.perf_counter()-tick,owned_context=diagnostics(),initial_cache=cache_diagnostics()));(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows[-1],flush=True)
assert diagnostics()['loads']==1 and diagnostics()['accesses']==2;A=D/'new_warm_context';B=D/'new_original_rebuild'
for rel in ['model/initial.json','model/sketch.json','model/round0.json','model/round1.json','native/subset.json','native/bindings.json']:
 p=A/rel;q=B/rel;x=json.loads(p.read_text());assert x==json.loads(q.read_text()),rel
 if rel.startswith('model/'):assert len(x['records'])==len({r['connection_id'] for r in x['records']})==6273
 bindings.update({str(p):sha(p),str(q):sha(q)})
a=json.loads((A/'model/receipt.json').read_text());b=json.loads((B/'model/receipt.json').read_text());assert len(a['rounds'])==len(b['rounds'])==2;events=0
for x,y in zip(a['rounds'],b['rounds']):assert {k:v for k,v in x.items() if k not in ['seconds','state_file']}=={k:v for k,v in y.items() if k not in ['seconds','state_file']};events+=len(x['events'])
assert (A/'native/seed.route').read_bytes()==(B/'native/seed.route').read_bytes()
for p in [A/'model/receipt.json',B/'model/receipt.json',A/'native/seed.route',B/'native/seed.route']:bindings[str(p)]=sha(p)
assert all(sha(k)==h for k,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all6273_new_layout_states_and_handoff_equal_original_rebuild=True,all_new_round_events_equal=events,seed_bytes_equal=True,static_context_load_once_queries_updated=True,scope='Full actual moved-endpoint model equivalence with original full rebuild. Static prep reuse only, all dynamic queries/floors/feedback recomputed. Marginal model/handoff/audit timers retain first coldload separately; no actual path-incremental algorithm or fullnative/canonical/heldout/hardware gain.'),indent=2)+'\n');print('ACTUAL SWAP FULL MODEL PARITY PASS',events)
