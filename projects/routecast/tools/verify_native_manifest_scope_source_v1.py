"""Reversible service gate changes; all four exact kernels byte-identical."""
from pathlib import Path
import json,ast
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];B=R/'build/native_live_seed_manifest_scope_v1_2026-10-10';A=R/'build/native_live_seed_adaptive_width_v1_2026-10-10';O=R/'experiments/native_manifest_scope_source_contract_v1_2026-10-10';O.mkdir(exist_ok=True);v=json.loads((B/'receipt.json').read_text());assert all(sha(p)==h for p,h in v['bindings'].items()) and all(sha(p)==h for p,h in v['source_sha256'].items()) and sha(B/'sequence_vpr')==v['binary_sha256'];s=(B/'source/route.cpp').read_text()
for before,after in reversed(v['edits']):assert s.count(after)==1;s=s.replace(after,before)
assert s==(A/'source/route.cpp').read_text();files=[Path(__file__).resolve(),B/'receipt.json',A/'source/route.cpp',B/'source/route.cpp']
for name in ['native_forward_kernel.h','native_bidi_kernel.h','native_forward_kernel64.h','native_bidi_kernel64.h']:
 a=A/'source'/name;b=B/'source'/name;assert a.read_bytes()==b.read_bytes();files.extend([a,b])
def pin_loops(path):
 f=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='prepare')
 return [ast.dump(n) for n in f.body if isinstance(n,ast.For) and not (isinstance(n.target,ast.Tuple) and any(isinstance(t,ast.Name) and t.id=='event' for t in n.target.elts))]
a=R/'tools/prepare_live_native_manifest_v1.py';b=R/'tools/prepare_live_native_manifest_v2.py';assert pin_loops(a)==pin_loops(b);files.extend([a,b]);bindings={**v['bindings'],**v['source_sha256'],**{str(p):sha(p) for p in files}}
(O/'verification.json').write_text(json.dumps(dict(bindings=bindings,all_four_original_exact_kernels_byte_identical=True,service_changes_exactly_reversible=True,all_original_native_pin_assignment_loops_AST_equal=True,scope='Source contract only; manifest native READY/rejection and full search parity experiments separate.'),indent=2)+'\n');print('MANIFEST SOURCE CONTRACT PASS')
