"""Paired fresh full models/handoffs/audits; compact formatting only, not native workflow."""
import json,subprocess,sys,time,ast
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_compact_json_complete_model_pair_v1_2026-10-10';assert not D.exists();D.mkdir();ep=R/'experiments/sha1_expat_topology_complete_workflow_v1_2026-10-10/seed/demand/sha1/endpoints.json';original=R/'tools/run_resident_actual_old_linear_undo_model_v13.py';candidate=R/'tools/run_resident_actual_old_linear_undo_model_compact_json_v1.py';assert ast.dump(ast.parse(candidate.read_text().replace(',indent=None)',',indent=2)')))==ast.dump(ast.parse(original.read_text()));drivers=[R/'tools/run_sha1_actual_old_linear_undo_native_handoff_v1.py',R/'tools/run_sha1_compact_json_native_handoff_v1.py'];assert ast.dump(ast.parse(drivers[1].read_text().replace('from run_resident_actual_old_linear_undo_model_compact_json_v1 import predict','from run_resident_actual_old_linear_undo_model_v13 import predict')))==ast.dump(ast.parse(drivers[0].read_text()));audit=R/'tools/run_shared_actual_old_linear_direct_lattice_audits_v4.py';bindings=closure([Path(__file__).resolve(),*drivers,audit]);bindings[str(ep)]=sha(ep);(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,order=['original','compact'],endpoint=str(ep),scope='Same frozen complete SHA endpoint, fresh full original two-round6273query models+original selector/serializer+allthree independent audits. Only model JSON indentation differs, full inverse AST parity. Single original-then-compact local paired cost, no native/canonical stages/heldout/silicon/end-to-end gain.'),indent=2)+'\n');rows=[]
for arm,driver in zip(['original','compact'],drivers):
 B=D/arm;B.mkdir();commands=[[sys.executable,str(driver),'sha1',str(ep),str(B/'handoff'),str(B/'native'),str(B/'model')],[sys.executable,str(audit),str(B/'model'),'sha1']];tick=time.perf_counter();codes=[]
 for i,cmd in enumerate(commands):
  with (B/f'stage{i}.log').open('w') as log:code=subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
  codes.append(code)
  if code:break
 if codes==[0,0]:
  for p in [B/'handoff/receipt.json',B/'model/shared_audit_receipt.json']:
   v=json.loads(p.read_text())
   for section in ['bindings','files']:assert all(sha(k)==h for k,h in v.get(section,{}).items())
   bindings[str(p)]=sha(p)
  assert v['all_three_complete_audits_pass'] and v['fresh_independent_graph_context']
 rows.append(dict(arm=arm,exit_codes=codes,complete_local_model_handoff_audit_seconds=time.perf_counter()-tick));(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows[-1],flush=True)
assert all(x['exit_codes']==[0,0] for x in rows);A=D/'original';B=D/'compact';comparisons={}
for rel in ['model/initial.json','model/sketch.json','model/round0.json','model/round1.json','native/subset.json','native/bindings.json']:
 p=A/rel;q=B/rel;assert json.loads(p.read_text())==json.loads(q.read_text()),rel;comparisons[rel]='complete parsed object identical';bindings.update({str(p):sha(p),str(q):sha(q)})
assert (A/'native/seed.route').read_bytes()==(B/'native/seed.route').read_bytes();comparisons['native/seed.route']='exact bytes identical'
for a,b in zip(json.loads((A/'model/receipt.json').read_text())['rounds'],json.loads((B/'model/receipt.json').read_text())['rounds']):assert {k:v for k,v in a.items() if k not in ['seconds','state_file']}=={k:v for k,v in b.items() if k not in ['seconds','state_file']}
for p in [A/'model/receipt.json',B/'model/receipt.json',A/'native/seed.route',B/'native/seed.route']:bindings[str(p)]=sha(p)
assert all(sha(k)==h for k,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,full_state_and_handoff_comparisons=comparisons,all_round_events_and_scientific_fields_equal=True,scope='All full state JSON/round scientific fields/events, native subset/bindings and seedbytes identical. Only timing/output-path/source-bindings metadata differ; both complete independent audits pass. Local full model+handoff+audit paired times, not native/canonical completeworkflow gain or family admission.'),indent=2)+'\n');print('FULL MODEL/ROUND/EVENT/HANDOFF PARITY PASS',flush=True)
