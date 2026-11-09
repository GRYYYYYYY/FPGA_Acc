"""Independent histogram rank metric recomputation from frozen full vectors."""
import ast,json,sys,math
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
name=sys.argv[1];out=R/'experiments/ultraembedded_mmc_hotspots_v1_2026-10-08'/name
rp=out/'comparison.json';r=json.loads(rp.read_text())
bindings={**r['bindings'],**closure([Path(__file__)]),str(rp):sha(rp)}
assert all(sha(k)==v for k,v in bindings.items())
source=R/'tools/verify_aes_native_demand_span_ablation_hotspots_v1.py'
bindings[str(source)]=sha(source)
tree=ast.parse(source.read_text());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='audit_metric')
# Histogram ranks differ from producer index-sort rank implementation.
checked=0
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'))
v=json.loads((out/'comparison_vectors.json').read_text());channels=v['channels'];bins=v['bins']
methods={'wire_shared','wire_independent','rc_initial'}
assert len({x['node'] for x in channels})==len(channels)
assert len({tuple(x['key']) for x in bins})==len(bins)
assert all(x['capacity']>0 and set(x['predictions'])==methods for x in channels+bins)
assert r['completed']==r['required']==len(json.loads((R/'experiments/ultraembedded_mmc_native_demand_v1_2026-10-08'/name/'endpoints.json').read_text())['connections'])
for m in methods:
 audit_metric({x['node']:x['predictions'][m]/x['capacity'] for x in channels},{x['node']:x['native']/x['capacity'] for x in channels},r['metrics'][m]['concrete'],max(1,len(channels)//20))
 audit_metric({tuple(x['key']):x['predictions'][m]/x['capacity'] for x in bins},{tuple(x['key']):x['native']/x['capacity'] for x in bins},r['metrics'][m]['spatial'],20)
audit_metric({tuple(x['key']):x['geometry'] for x in bins},{tuple(x['key']):x['native']/x['capacity'] for x in bins},r['metrics']['geometry']['spatial'],20)
assert r['metrics']['geometry']['concrete'] is None and checked==7
assert all(sha(k)==v for k,v in bindings.items())
(out/'metric_verification.json').write_text(json.dumps(dict(bindings=bindings,metric_vectors_recomputed=checked,histogram_ranks_topk_mae_and_full_vector_scope_pass=True,scope='Independent numerical metrics on authenticated vectors. Not an independent second physical mapping/geometry algorithm or HDL/timing/generalization proof.'),indent=2)+'\n')
print('PASS Ethernet metrics',checked)
