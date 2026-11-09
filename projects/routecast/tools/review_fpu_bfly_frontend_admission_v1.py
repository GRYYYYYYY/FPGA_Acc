"""Apply existing Boolean schema; keep level-sensitive storage explicitly unsupported."""
import json
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];S=R/'experiments/fpu_bfly_frontend_readiness_v1_2026-10-10'
r=json.loads((S/'receipt.json').read_text());assert r['exit_code']==0 and all(sha(k)==v for k,v in r['bindings'].items())
reference=R/'tools/review_ultraembedded_frontend_admission_v2.py';allowed={'$_MUX_','$_XOR_','$_XNOR_','$_NOT_','$_OR_','$_AND_','$_DFF_P_','$_DFF_PP0_','$_DFF_PP1_','$scopeinfo'}
# Reuse frozen existing schema exactly, no acceptance expansion.
import ast
node=next(n for n in ast.parse(reference.read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='allowed' for t in n.targets));assert ast.literal_eval(node.value)==allowed
p=S/'design.json';m=json.loads(p.read_text())['modules']['bfly'];cells=m['cells'];types=Counter(c['type'] for c in cells.values());assert dict(types)==r['cell_types']
latches=[dict(name=n,type=c['type'],source=c.get('attributes',{}).get('src'),connections=c['connections']) for n,c in cells.items() if c['type'].startswith('$_DLATCH_')]
unsupported={k:v for k,v in types.items() if k not in allowed};assert unsupported=={'$_DLATCH_N_':652}
D=R/'experiments/fpu_bfly_frontend_admission_v1_2026-10-10';assert not D.exists();D.mkdir()
bindings={**r['bindings'],**{str(x):sha(x) for x in [Path(__file__).resolve(),reference,S/'receipt.json',p]}}
assert all(sha(k)==v for k,v in bindings.items())
out=dict(bindings=bindings,boolean_schema_matches_existing_admission=True,unsupported_types=unsupported,latches=latches,native_input_admitted=False,heldout_admitted=False,scope='Existing Boolean gates are supported despite no literal LUT cells. 652 negative-level latches remain unsupported by this admission/architecture; no latch-to-FF projection, removal, semantics waiver or source correction. Source/initial-state/function/timing proofs remain separate.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['bindings','latches']},indent=2))
