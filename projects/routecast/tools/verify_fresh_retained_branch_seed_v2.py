"""Authenticate full fresh forest and exact certified original trace serialization."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'fresh_retained_branch_seed_v2_2026-10-08'
bindings={}
def read(path):
 obj=json.loads(path.read_text())
 for name,digest in obj.get('bindings',{}).items():
  assert sha(name)==digest
  assert name not in bindings or bindings[name]==digest
  bindings[name]=digest
 bindings[str(path)]=sha(path);return obj
r=read(D/'receipt.json');fresh=read(D/'forest.json')
old=read(E/'endpoint_compatible_branch_trim_v1_2026-10-08/w32_m2.json')
proof=read(E/'endpoint_compatible_branch_trim_v1_2026-10-08/verification.json')
assert proof['complete_twelve_cases_independent_branch_forest_pass']
assert fresh['retained']==old['retained'] and fresh['released']==old['released']
assert len(fresh['retained'])==1864 and len(fresh['released'])==65
assert sorted(x['connection_id'] for xs in fresh.values() for x in xs)==list(range(1929))
pins=read(E/'retained_branch_sink_identity_v2_2026-10-08/certificate.json')
assert pins['all_twelve_unique_sink_identity_maps_pass']
serial=read(E/'retained_branch_native_serialization_v1_2026-10-08/receipt.json')
assert serial['all_twelve_serialized_paths_pass']
row=next(x for x in serial['rows'] if x['width']==32 and x['index']==2)
route=D/'w32_m2.route';assert sha(route)==row['route_sha256']==r['rows'][0]['route_sha256']
bindings[str(route)]=sha(route);bindings[str(Path(__file__))]=sha(Path(__file__))
assert all(sha(path)==digest for path,digest in bindings.items())
out=dict(bindings=bindings,all1929_retained_release_decisions_and_physical_fraction_witnesses_equal=True,
         exact_native_trace_and_certified_sink_identity_byte_equality_pass=True,
         retained=1864,released=65,component_elapsed_seconds=r['component_elapsed_seconds'],
         scope='Independent original XML/Fraction and packed sink identity evidence inherited by entire forest and exact serialized bytes. Production derives all decisions/pin indices from provided original route/endpoints/budgets; historical references only verifier. Case32m2 only, upstream endpoint/budget generation excluded; actual resume and full workflow still separate.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'},flush=True)
