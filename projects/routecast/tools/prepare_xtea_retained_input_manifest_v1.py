"""Freeze a second exposed development design for input portability checks."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from prepare_live_native_manifest_v2 import prepare
R=Path(__file__).resolve().parents[1]
ep=R/'experiments/freecores_native_demand_v1_2026-10-08/xtea/endpoints.json'
out=R/'experiments/xtea_retained_input_preflight_v1_2026-10-13';out.mkdir()
v=json.loads(ep.read_text());bindings=closure([Path(__file__)]);bindings[str(ep)]=sha(ep)
for spec in v['inputs'].values():assert sha(spec['path'])==spec['sha256'];bindings[spec['path']]=spec['sha256']
arch=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml';bindings[str(arch)]=sha(arch)
manifest=out/'xtea.queries';mapping=prepare(ep,manifest)
assert len(mapping)==len(v['connections'])==2450
bindings[str(manifest)]=sha(manifest)
assert all(sha(p)==h for p,h in bindings.items())
(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,endpoint=str(ep),architecture=str(arch),connections=len(mapping),nets=len(set(mapping.values())),graph_dimensions=manifest.read_text().splitlines()[0],complete_native_identity_pin_to_physical_endpoint_assignment_pass=True,heldout=False,scope='Existing exposed XTEA design; complete static native identity/XML pin manifest only. Live native getter, criticality and node cost observations still required. No generalization or model quality claim.'),indent=2)+'\n')
print('XTEA manifest pass',len(mapping),'connections',len(set(mapping.values())),'NETs',flush=True)
