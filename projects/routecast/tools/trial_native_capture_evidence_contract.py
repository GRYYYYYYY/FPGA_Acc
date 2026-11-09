"""Actual candidate/reference capture staging and refusal/cleanup contracts."""
import json,shutil
from pathlib import Path
from pre_route_endpoints import sha
import native_capture_evidence as module
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_capture_evidence_contract_2026-10-06';out.mkdir();graph=root/'work/nonzero_rc_tseng_reference128_2026-10-06/rr_graph.xml';bindings={};checks=[];rows=[]
cases=[('candidate',root/'experiments/tseng_fused_capture_native_import_2026-10-06',root/'work/tseng_fused_capture_native_import_2026-10-06','import.log'),('reference',root/'work/tseng_sequential_fused4_2026-10-06/0/experiments/tseng_swapped_place_cold_2026-10-06',root/'work/tseng_sequential_fused4_2026-10-06/0/work/tseng_swapped_place_cold_2026-10-06','run.log')]
p={'source_sha256':sha(root/'tools/native_capture_evidence.py'),'cases':[{'name':n,'receipt':str(e/'receipt.json'),'verification':str(e/'verification.json'),'cwd':str(w),'log':log} for n,e,w,log in cases],'scope':'Native capture evidence interface contract on actual candidate/reference receipts; no new routing/quality or performance claim.'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n')
def refuse(label,fn):
 try:fn()
 except ValueError:checks.append(label)
 else:raise AssertionError('missing refusal '+label)
for name,e,w,log in cases:
 evidence=module.load_capture_evidence(e/'receipt.json',e/'verification.json',w,graph,sha(graph),1234,log)
 manifest=evidence.stage(out/name);rows.append({'name':name,'manifest_sha256':sha(manifest),'receipt_sha256':sha(e/'receipt.json')});bindings.update(dict(evidence.bindings))
 refuse(name+'-wrong-graph',lambda:module.load_capture_evidence(e/'receipt.json',e/'verification.json',w,graph,'0'*64,1234,log))
 refuse(name+'-wrong-terminal-count',lambda:module.load_capture_evidence(e/'receipt.json',e/'verification.json',w,graph,sha(graph),1233,log))
 refuse(name+'-existing-destination',lambda:evidence.stage(out/name))
refuse('uncaptured-native-producer',lambda:module.load_capture_evidence(root/'experiments/tseng_joint_native_import_2026-10-06/receipt.json',root/'experiments/tseng_joint_native_import_2026-10-06/verification.json',root/'work/tseng_joint_native_import_2026-10-06',graph,sha(graph),1234))
e,w=cases[0][1:3];evidence=module.load_capture_evidence(e/'receipt.json',e/'verification.json',w,graph,sha(graph),1234)
copy=module.shutil.copyfile
try:
 def fail(*args,**kwargs):raise RuntimeError('injected copy failure')
 module.shutil.copyfile=fail
 try:evidence.stage(out/'copy_failure')
 except RuntimeError:checks.append('copy-failure-no-partial-directory')
 else:raise AssertionError('copy failure missing')
finally:module.shutil.copyfile=copy
assert not (out/'copy_failure').exists() and not list(out.glob('.capture-*'));evidence.validate()
# Isolated copied producer files; altering them never touches original experiments.
fixture=out/'fixture';fixture.mkdir();q=json.loads((e/'receipt.json').read_text());q['files_sha256']={}
for f in w.iterdir():
 if f.is_file():shutil.copyfile(f,fixture/f.name);q['files_sha256'][str(fixture/f.name)]=sha(fixture/f.name)
receipt=fixture/'receipt.json';receipt.write_text(json.dumps(q,indent=2)+'\n');v=json.loads((e/'verification.json').read_text());v['receipt_sha256']=sha(receipt);verification=fixture/'verification.json';verification.write_text(json.dumps(v,indent=2)+'\n')
isolated=module.load_capture_evidence(receipt,verification,fixture,graph,sha(graph),1234);f=fixture/'before_sync.route';saved=f.read_bytes()
try:
 f.write_bytes(saved+b'\n');refuse('changed-capture-no-output',lambda:isolated.stage(out/'changed_capture'))
finally:f.write_bytes(saved)
assert not (out/'changed_capture').exists();isolated.validate()
r={'protocol_sha256':sha(out/'protocol.json'),'cases':rows,'checks':checks,'original_input_bindings':bindings,'original_inputs_unchanged':all(sha(f)==h for f,h in bindings.items())};assert r['original_inputs_unchanged'];(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print('passed',len(checks),'negative/cleanup contracts and2 actual capture stage cases')
