"""Fixed pre-move timing and nodebase; explicit native-state warm schema."""
import json,time,sys
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from prepare_live_native_manifest_v2 import prepare
from frozen_timing_epoch_remap_v1 import remap
from audit_structural_node_base_v1 import audit as audit_base
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from load_design_routing_inputs_v2 import load
D=Path(sys.argv[2]);D.mkdir(exist_ok=False);start=time.perf_counter();before=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json';endpoint=Path(sys.argv[1])/'demand/endpoints.json';staged=Path(sys.argv[1]);proof=json.loads((staged/'staged_input_verification_v1.json').read_text());assert all(sha(p)==h for p,h in proof['bindings'].items());bindings={**closure([Path(__file__)]),**proof['bindings'],str(staged/'staged_input_verification_v1.json'):sha(staged/'staged_input_verification_v1.json')};a=json.loads(before.read_text());b=json.loads(endpoint.read_text());manifest=D/'target.queries';prepare(endpoint,manifest);oldmanifest=R/'experiments/native_manifest_scope_preflight_v1_2026-10-10/mmc.queries';oldcrit=R/'experiments/mmc_native_initial_criticality_snapshot_v2_2026-10-10'
identities=[]
for meta in [a,b]:
 rows=[json.loads(line) for line in Path(meta['inputs']['native_identity']['path']).read_text().splitlines()];identities.append([dict(r,pins=[{k:v for k,v in pin.items() if k not in ['x','y','layer']} for pin in r['pins']]) for r in rows])
assert identities[0]==identities[1];values,cb,epoch=remap(before,endpoint,oldcrit,oldmanifest,manifest);timing=D/'timing';timing.mkdir();vector=timing/'remapped_criticalities.json'
with vector.open('x') as f:json.dump([dict(values[k]) for k in sorted(values)],f,separators=(',',':'));f.write('\n')
cb.update(bindings);cb[str(vector)]=sha(vector)
with (timing/'verification.json').open('x') as f:json.dump(dict(schema='ROUTECAST_FROZEN_TIMING_REMAP_V1',bindings=cb,timing_epoch_sha256=epoch,before_endpoint=str(before),after_endpoint=str(endpoint),source_criticality_directory=str(oldcrit),before_manifest=str(oldmanifest),after_manifest=str(manifest),connections=len(values),all_native_pin_identities_preserved=True,all_values_equal_before_timing_epoch=True,all_endpoints_equal_after_placement=True,scope='Original pre-move criticality; no new target STA.'),f,indent=2);f.write('\n')
oldbase=R/'experiments/mmc_native_node_base_mapping_v1_2026-10-10/verification.json';base=D/'base';base.mkdir();bp=json.loads(oldbase.read_text());assert all(sha(p)==h for p,h in bp['bindings'].items());payload=base/'node_base.u64'
with payload.open('xb') as f:f.write((oldbase.parent/'node_base.u64').read_bytes())
bp['bindings'].update(bindings);bp['bindings'].update({str(oldbase):sha(oldbase),str(payload):sha(payload),str(endpoint):sha(endpoint)})
with (base/'verification.json').open('x') as f:json.dump(bp,f,indent=2);f.write('\n')
expected=audit_base(b['inputs']['graph']['path'],base/'verification.json',bp['scale']);graph,digest,nodes,fields,rc,queries=load_endpoints(endpoint);bases,crit,extra=load(endpoint,base/'verification.json',timing,len(nodes),rc.scale);assert bases==expected and len(crit)==115572;bindings.update(extra)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'verification.json').open('x') as f:json.dump(dict(bindings=bindings,all_native_pin_identities_preserved=True,all115572_frozen_criticalities_remapped=True,nodebase_exact_independent_xml_pass=True,preparation_seconds=time.perf_counter()-start,scope='Fresh frozen old timing remap and unchanged originalXML nodebase for this frozen placement. No target STA or candidate initialization claim.'),f,indent=2)
print('PASS fixed timing/base for frozen placement',len(crit),flush=True)
