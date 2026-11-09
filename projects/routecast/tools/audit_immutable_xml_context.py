import json,shutil,time
from pathlib import Path
from immutable_xml_prediction_audit import ImmutableXMLAudit
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';out=base/'adder_tree_immutable_xml_audit_2026-10-06';out.mkdir()
sp=json.loads((base/'adder_tree_2L032_move_sequence_2026-10-06/protocol.json').read_text());graph=sp['inputs']['rr_graph'];t=time.monotonic();ctx=ImmutableXMLAudit(graph['path'],graph['sha256']);init=time.monotonic()-t;rows=[];parent=base/'adder_tree_online_rc_budget_net_sequence_v2_2026-10-06';receipt=json.loads((parent/'receipt.json').read_text())
for step in receipt['steps']:
 k=step['step'];epfile=base/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json' if k==0 else base/'adder_tree_2L032_move_sequence_2026-10-06'/f'step_{k}_endpoints.json';predfile=parent/f'step_{k}_prediction.json';auditfile=parent/f'step_{k}_physical.json';assert sha(predfile)==step['prediction_sha256'] and sha(auditfile)==step['physical_sha256'];t=time.monotonic();checked=ctx.verify(json.loads(epfile.read_text()),json.loads(predfile.read_text()),topology=True);elapsed=time.monotonic()-t;assert checked==json.loads(auditfile.read_text());p=out/f'step_{k}_audit.json';p.write_text(json.dumps(checked)+'\n');rows.append({'step':k,'all_audit_fields_equal_streaming':True,'wall_s':elapsed,'audit_sha256':sha(p)})
try:ctx.caps[0]=0
except TypeError:pass
else:raise AssertionError('mutable cached metadata')
for n in ['immutable_xml_prediction_audit.py','audit_immutable_xml_context.py']:shutil.copyfile(root/'tools'/n,out/n)
(out/'receipt.json').write_text(json.dumps({'graph_sha256':graph['sha256'],'initial_xml_load_s':init,'immutable_payload_bytes':ctx.payload_bytes,'sources_sha256':{n:sha(out/n) for n in ['immutable_xml_prediction_audit.py','audit_immutable_xml_context.py']},'steps':rows,'scope':'All original streaming audit fields equal on 2064 real paths. Full XML topology cached in immutable bytes, SHA checked before/after each audit. Initial parse/storage cost separate, not full pipeline performance.'},indent=2)+'\n');print(init,ctx.payload_bytes,rows)
