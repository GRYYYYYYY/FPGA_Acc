"""Private joint CPD/wire native gate, shared VTR remains read-only."""
import json,subprocess
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];parent=ROOT/'build/loaded_native_quality_gate_v2_2026-10-06';out=ROOT/'build/native_joint_qor_gate_2026-10-07';out.mkdir();(out/'source').mkdir();p=json.loads((parent/'protocol.json').read_text());source=parent/'source/route.cpp';s=source.read_text()
s=s.replace('        float reference_cpd=-1;', '        float reference_cpd=-1;\n        size_t reference_wire=0;')
needle='refresh();reference_cpd=std::get<0>(metrics());';assert s.count(needle)==1
s=s.replace(needle,needle+'\n                    reference_wire=calculate_wirelength_info(net_list,available_wirelength).used_wirelength();')
needle='                bool pick_reference=predicted_cpd>reference_cpd;';assert s.count(needle)==1
s=s.replace(needle,'                size_t predicted_wire=calculate_wirelength_info(net_list,available_wirelength).used_wirelength();\n                bool pick_reference=predicted_cpd>reference_cpd || predicted_wire>reference_wire;')
needle='                    if(std::get<0>(metrics())!=reference_cpd)throw std::runtime_error("selected reference STA mismatch");';assert s.count(needle)==1
s=s.replace(needle,needle+'\n                    if(calculate_wirelength_info(net_list,available_wirelength).used_wirelength()!=reference_wire)throw std::runtime_error("selected reference wire mismatch");')
needle='                VTR_LOG("ROUTECAST same-target gate predicted_cpd_ns=%.9g reference_cpd_ns=%.9g selected=%s\\n",1.e9*predicted_cpd,1.e9*reference_cpd,pick_reference?"reference":"predicted");';assert s.count(needle)==1
s=s.replace(needle,needle+'\n                VTR_LOG("ROUTECAST joint-qor gate predicted_wire=%zu reference_wire=%zu selected=%s cpd_regression=%d wire_regression=%d\\n",predicted_wire,reference_wire,pick_reference?"reference":"predicted",int(predicted_cpd>reference_cpd),int(predicted_wire>reference_wire));')
f=out/'source/route.cpp';f.write_text(s);compile=[str(f) if x==str(source) else str(out/'route.o') if x==str(parent/'route.o') else x for x in p['compile']];link=[str(out/'route.o') if x==str(parent/'route.o') else str(out/'gate_vpr') if x==str(parent/'gate_vpr') else x for x in p['link']]
(out/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,parent_protocol_sha256=sha(parent/'protocol.json'),parent_source_sha256=sha(source),source_sha256=sha(f),shared_inputs_sha256=p['shared_inputs_sha256'],policy='Native zero-tolerance CPD AND VPR used-wirelength nonregression against freshly routed same-target reference, ties admitted. Reference winner reimport validates BOTH STA and wire. Other state/rollback semantics inherited; single-step only. No end-to-end claim.'),indent=2)+'\n')
for label,cmd in [('compile',compile),('link',link)]:
 with (out/(label+'.log')).open('w') as stream:code=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
 if code:raise SystemExit(label+' failed '+str(code))
assert all(sha(f)==h for f,h in p['shared_inputs_sha256'].items())
(out/'receipt.json').write_text(json.dumps(dict(binary_sha256=sha(out/'gate_vpr'),protocol_sha256=sha(out/'protocol.json'),scope='Private gate built; runtime native/reference/selected physical and FULLSTA proofs pending.'),indent=2)+'\n');print('Built private native joint QoR gate',flush=True)
