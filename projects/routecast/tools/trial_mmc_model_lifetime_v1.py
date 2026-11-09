"""Full MMC lifetime API parity with every setup/update/export cost charged."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from mmc_model_lifetime_v1 import Model,SOURCE,SOURCE_SHA
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_model_lifetime_v1_2026-10-21';D.mkdir()
P=R/'experiments/mmc_native_cached_feedback_pilot_v1_2026-10-18/protocol.json';p=json.loads(P.read_text());assert all(sha(k)==h for k,h in p['bindings'].items())
files=[Path(__file__),P,R/'tools/mmc_model_lifetime_v1.py',R/'tests/test_mmc_model_lifetime_v1.py'];bindings={**p['bindings'],**{str(f):sha(f) for f in files}}
(D/'protocol.json').write_text(json.dumps({'bindings':bindings,'reference_source_sha256':SOURCE_SHA,'scope':'Fixed-placement two-round lifecycle API correctness trial. Reference algorithm, initialized history/epochs, 54 dirty wholeNET schedule and full outputs unchanged. Each exposed boundary reauthenticates all bound inputs; no model/native acceleration claim or cross-placement reuse. All API, state-read, parity and export costs counted.','rounds':[0,1],'native_calls':0},indent=2)+'\n')
args=p['command'][2:];old=Path(args[1]);args[1]=str(D/'model');start=time.perf_counter();m=Model(*args);ready=m.current
assert ready.round_index==-1 and m.cleanup['calls']==0
rejected=[]
try:m.step(ready,1)
except ValueError:rejected.append('out_of_order')
else:raise AssertionError('out of order accepted')
for index in [0,1]:
 oldticket=m.current;new=m.step(oldticket,index)
 try:m.read_state(oldticket)
 except RuntimeError:rejected.append(f'stale_ticket_after_round{index}')
 else:raise AssertionError('stale read accepted')
 assert m.cleanup['calls']==0
 tick=time.perf_counter();state=m.read_state(new);reference=json.loads((old/f'round{index}.json').read_text());assert state==reference
 m.costs.append({'stage':f'round{index}_detached_read_and_reference_comparison','seconds':time.perf_counter()-tick})
 print('LIFETIME ROUND PARITY',index,flush=True)
result=m.export(m.current);assert m.cleanup=={'calls':1,'search_closed':True,'graph_closed':True};assert m.phase=='EXPORTED'
tick=time.perf_counter();parity={}
for name in ['initial.json','floors.json','round0.json','round1.json','sketch.json','structural_cost_metrics.json']:
 parity[name]=sha(old/name)==sha(D/'model'/name);assert parity[name],name
before=json.loads((old/'receipt.json').read_text());after=json.loads((D/'model/receipt.json').read_text());semantic=lambda rs:[{k:v for k,v in r.items() if k not in ['seconds','state_file']} for r in rs];assert semantic(before['rounds'])==semantic(after['rounds'])
assert all(sha(k)==h for k,h in bindings.items());m.costs.append({'stage':'full_byte_event_and_source_final_audit','seconds':time.perf_counter()-tick})
receipt={'all_reference_state_bytes_exact':parity,'all_round_events_exact':True,'rejected_invalid_calls':rejected,'compiled_owner_stable_across_rounds':True,'cleanup':m.cleanup,'stage_costs':m.costs,'total_with_boundary_guards_and_parity_seconds':time.perf_counter()-start,'model_result':dict(result),'transformed_ast_sha256':m.transformed_ast_sha256,'bindings':{**bindings,str(D/'model/receipt.json'):sha(D/'model/receipt.json')},'scope':'Serial fixed-placement lifecycle interface, original complete outputs/guards preserved plus explicit boundary input checks. No cross-placement reuse, native quality, end-to-end, heldout or hardware proof.'}
(D/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print('MMC MODEL LIFETIME EXACT PARITY PASS',receipt['total_with_boundary_guards_and_parity_seconds'],flush=True)
