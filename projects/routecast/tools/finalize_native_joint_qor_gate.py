"""Close private native joint gate integration proofs; no lifecycle speed claim."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];build=ROOT/'build/native_joint_qor_gate_2026-10-07';out=ROOT/'experiments/native_joint_qor_gate_integration_2026-10-07'
def read(p):return json.loads(p.read_text())
p=read(build/'protocol.json');b=read(build/'receipt.json');assert b['protocol_sha256']==sha(build/'protocol.json') and b['binary_sha256']==sha(build/'gate_vpr') and p['source_sha256']==sha(build/'source/route.cpp');assert all(sha(f)==h for f,h in p['shared_inputs_sha256'].items())
protocol=ROOT/'experiments/native_joint_qor_gate_five_case_protocol_2026-10-07.json';cp=read(protocol);assert cp['binary_sha256']==b['binary_sha256'];bindings={str(protocol):sha(protocol),str(build/'protocol.json'):sha(build/'protocol.json'),str(build/'receipt.json'):sha(build/'receipt.json'),str(build/'source/route.cpp'):sha(build/'source/route.cpp')};rows=[]
items=[(x['weight'],x['width'],x['index'],f"mux_native_joint_{x['weight']}_w{x['width']}m{x['index']}") for x in cp['cases']]
fixture=ROOT/'experiments/native_joint_cpd_only_fixture_2026-10-07';fp=read(fixture/'protocol.json');items.append(('50ps-forced-negative',8,0,'mux_native_joint_cpd_only_w8m0'))
for f in [fixture/'protocol.json',fixture/'input_verification.json']:bindings[str(f)]=sha(f)
assert fp['input_verification_sha256']==sha(fixture/'input_verification.json') and fp['binary_sha256']==b['binary_sha256']
for f,h in read(fixture/'input_verification.json')['proofs'].items():assert sha(f)==h;bindings[f]=h
for x in cp['cases']:
 assert sha(x['producer'])==x['producer_sha256'] and sha(x['verifier'])==x['verifier_sha256']
for label,w,i,name in items:
 case=ROOT/f'experiments/{name}_quality_gate_2026-10-07';r=read(case/'receipt.json');v=read(case/'verification.json');pp=read(case/'protocol.json');assert r['protocol_sha256']==sha(case/'protocol.json') and v['receipt_sha256']==sha(case/'receipt.json') and len(v['rows'])==1
 assert all(sha(f)==h for group in ('sources','binaries') for f,h in pp[group].items());assert str(build/'gate_vpr') in pp['binaries'] and pp['binaries'][str(build/'gate_vpr')]==b['binary_sha256']
 row=v['rows'][0];assert (row['width'],row['index'])==(w,i);assert row['selected']==('reference' if row['predicted_cpd_ns']>row['reference_cpd_ns'] or row['predicted_wire']>row['reference_wire'] else 'predicted')
 native=r['rows'][0]['native'];reload=r['rows'][0]['reload'];assert reload['exit_code']==0 and reload['mismatches']==reload['fixups']==0
 for files in [native['files'],reload['files']]:
  for f,h in files.items():assert sha(f)==h;bindings[f]=h
 for f in [case/'protocol.json',case/'receipt.json',case/'verification.json']:bindings[str(f)]=sha(f)
 rows.append(dict(weight=label,**row))
assert sum(x['selected']=='predicted' for x in rows)==2 and sum(x['selected']=='reference' for x in rows)==4
out.mkdir();(out/'final_evidence.json').write_text(json.dumps(dict(finalizer_sha256=sha(Path(__file__)),binary_sha256=b['binary_sha256'],bindings=bindings,rows=rows,physical_connection_occurrences=sum(x['physical_connections_checked'] for x in rows),scope='Six integration fixtures: original five-case protocol plus separately prespecified forced MODEL-TIMING-REJECTED CPD-only negative fixture. Actual native gate compares fresh same-target reference CPD AND native VPR used wirelength, validates restored reference metrics, two candidate/four reference selections. Every candidate/reference/selected route independently physical/capacity audited; originalXML perNET union geometry equals all native wire metrics; exact selected paths and original selected canonical FULLSTA zero fixups. Archived predictor content; new native execution for allsix. Not full12 live prediction/admission/lifecycle timing, heldout, continuous moves or durable/concurrent publication.'),indent=2)+'\n');print([(x['weight'],x['width'],x['index'],x['selected'],x['predicted_wire'],x['reference_wire']) for x in rows],flush=True)
