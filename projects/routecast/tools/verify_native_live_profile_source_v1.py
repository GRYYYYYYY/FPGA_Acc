"""Native telemetry is reversible; all search kernel bodies byte identical."""
import json,ast
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/native_live_profile_source_contract_v1_2026-10-10';A=R/'build/native_live_seed_known_source_v1_2026-10-10/source';B=R/'build/native_live_seed_profile_v1_2026-10-10/source';s=(B/'route.cpp').read_text()
for old,new in reversed(json.loads((D/'changes.json').read_text())):assert s.count(new)==1;s=s.replace(new,old)
assert s==(A/'route.cpp').read_text()
for n in ['native_forward_kernel.h','native_bidi_kernel.h']:assert (A/n).read_bytes()==(B/n).read_bytes()
a=(R/'tools/run_native_live_seed_known_source_model_v1.py').read_text();b=(R/'tools/run_native_live_seed_profile_model_v1.py').read_text().replace('native_live_seed_profile_adapter_v1','native_live_seed_known_source_adapter_v1');assert ast.dump(ast.parse(a))==ast.dump(ast.parse(b))
files=[Path(__file__),D/'changes.json',A/'route.cpp',B/'route.cpp',A/'native_forward_kernel.h',B/'native_forward_kernel.h',A/'native_bidi_kernel.h',B/'native_bidi_kernel.h',R/'tools/run_native_live_seed_known_source_model_v1.py',R/'tools/run_native_live_seed_profile_model_v1.py'];(D/'verification.json').write_text(json.dumps(dict(native_route_body_equal_after_only_timer_substitutions=True,all_search_kernels_byte_identical=True,full_model_AST_equal_except_Search_import=True,bindings={str(p):sha(p) for p in files},scope='Kernel timers bracket only search calls; inclusive native answer timer also covers response serialization/flush. Native commandwait includes controller/model/audits. Different processes/windows overlap, never add clocks.'),indent=2)+'\n');print('PROFILE SOURCE PASS')
