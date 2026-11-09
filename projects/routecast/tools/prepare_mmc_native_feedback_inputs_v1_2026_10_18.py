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
D=R/'experiments/mmc_native_feedback_inputs_v1_2026-10-18';D.mkdir(exist_ok=False);start=time.perf_counter();before=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json';endpoint=R/'experiments/mmc_native_state_swap_inputs_v1_2026-10-18/demand/endpoints.json';staged=R/'experiments/mmc_old_floor_cache_audit_v1_2026-10-18';proof=json.loads((staged/'verification.json').read_text());assert all(sha(p)==h for p,h in proof['bindings'].items());bindings={**closure([Path(__file__)]),**proof['bindings'],str(staged/'verification.json'):sha(staged/'verification.json')};a=json.loads(before.read_text());b=json.loads(endpoint.read_text());manifest=D/'target.queries';prepare(endpoint,manifest);oldmanifest=R/'experiments/native_manifest_scope_preflight_v1_2026-10-10/mmc.queries';oldcrit=R/'experiments/mmc_native_initial_criticality_snapshot_v2_2026-10-10'
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
warm=D/'warm';warm.mkdir();frame=json.loads((staged/'initial.json').read_text());slots={eid:i for i,eid in enumerate(fields['edge_ids'])};independent=Counter();floors={}
for rec in frame['records']:
 used={rec['source']}|{fields['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids']};independent.update(used);key=rec['source'],rec['sink'];assert key not in floors or floors[key]==rec['floor_integer'];floors[key]=rec['floor_integer']
frame['independent_connection_ledger']=dict(independent)
for name,data in [('initial.json',frame),('floors.json',[dict(source=s,sink=t,minimum_integer=v) for (s,t),v in sorted(floors.items())]),('history.json',{})]:
 with (warm/name).open('x') as f:json.dump(data,f);f.write('\n')
 bindings[str(warm/name)]=sha(warm/name)
receipt=json.loads((R/'experiments/mmc_native_raw_control_v1_2026-10-18/receipt.json').read_text());wp=dict(schema='NATIVE_ANCHORED_WARM_INPUT_V1',bindings=bindings,endpoint=str(endpoint),dirty_nets=receipt['dirty_nets'],native_staged_state_independent_xml_pass=True,zero_initial_history=True,native_anchored_budget_policy='NATIVE_ANCHORED_PROXY_V1',old_floor_evidence='Authenticated zero-price producer contracts and archived originalXML attaining-path audit;381 fresh endpoint minimum crosschecks',all_old_per_design_minima_independently_recertified=False,cached_correctness_fixture=str(staged/'initial.json'),scope='Native old-state initialization, not prior estimator round1 history.')
assert all(sha(p)==h for p,h in bindings.items())
with (warm/'verification.json').open('x') as f:json.dump(wp,f,indent=2);f.write('\n')
with (D/'verification.json').open('x') as f:json.dump(dict(bindings={**bindings,str(warm/'verification.json'):sha(warm/'verification.json')},all_native_pin_identities_preserved=True,all115572_frozen_criticalities_remapped=True,nodebase_exact_independent_xml_pass=True,zero_initial_history=True,preparation_seconds=time.perf_counter()-start,scope='Cached-floor feedback correctness inputs; old global floors inherited with explicit source-contract evidence, not newly all recertified. Preparation includes repeated independent checks, not fresh continuous workflow or native STA timing.'),f,indent=2);f.write('\n')
print('PASS fixed native-state feedback inputs',len(crit),flush=True)
