"""Freeze explicit pre-move timing input for the exposed XTEA swap experiment."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from frozen_timing_epoch_remap_v1 import remap
from source_binding_v2 import closure
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
before=R/'experiments/freecores_native_demand_v1_2026-10-08/xtea/endpoints.json';after=R/'experiments/xtea_swap_native_demand_v1_2026-10-13/endpoints.json'
old=R/'experiments/xtea_retained_native_inputs_v1_2026-10-13/criticality'
ma=R/'experiments/xtea_retained_input_preflight_v1_2026-10-13/xtea.queries';mb=R/'experiments/xtea_swap_input_preflight_v1_2026-10-13/xtea.queries'
values,bindings,epoch=remap(before,after,old,ma,mb);bindings.update(closure([Path(__file__)]))
# Independent comparison to actual old/new native global-pin observations.
a=json.loads((old/'initial_connection_criticalities.json').read_text());new=R/'experiments/xtea_swap_native_inputs_v1_2026-10-13/criticality';proof=json.loads((new/'verification.json').read_text());assert all(sha(p)==h for p,h in proof['bindings'].items());bindings.update(proof['bindings']);bindings[str(new/'verification.json')]=sha(new/'verification.json');b=json.loads((new/'initial_connection_criticalities.json').read_text());a={x['connection_id']:x for x in a};b={x['connection_id']:x for x in b}
for cid,c in values.items():
 assert (c['net'],c['local_sink_pin'],c['global_pin'],c['source_rr'],c['target_rr'])==tuple(b[cid][k] for k in ['net','local_sink_pin','global_pin','source_rr','target_rr'])
 assert all(c[k]==a[cid][k] for k in ['criticality_float32_text','maximum_text','exponent_text'])
O=R/'experiments/xtea_fixed_timing_epoch_v1_2026-10-13';O.mkdir();p=O/'remapped_criticalities.json';p.write_text(json.dumps([dict(values[k]) for k in sorted(values)],separators=(',',':'))+'\n');bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
(O/'verification.json').write_text(json.dumps(dict(schema='ROUTECAST_FROZEN_TIMING_REMAP_V1',bindings=bindings,timing_epoch_sha256=epoch,before_endpoint=str(before),after_endpoint=str(after),source_criticality_directory=str(old),before_manifest=str(ma),after_manifest=str(mb),connections=len(values),all_native_pin_identities_preserved=True,all_values_equal_before_timing_epoch=True,all_endpoints_equal_after_placement=True,scope='Explicit pre-move timing snapshot remapped by original native pin identity. These are intentionally not refreshed post-move STA values. New timing epoch/global refresh is a separate experimental axis; no sparse update correctness/performance claim yet.'),indent=2)+'\n')
print('FROZEN EPOCH REMAP PASS',len(values),'connections',epoch,flush=True)
