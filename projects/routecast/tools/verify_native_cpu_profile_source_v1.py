"""CPU clocks add telemetry only; recover original complete native body."""
import json,ast
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/native_cpu_profile_source_contract_v1_2026-10-10';A=R/'build/native_live_seed_global_edge_v1_2026-10-10/source';B=R/'build/native_live_seed_cpu_profile_v1_2026-10-10/source';s=(B/'route.cpp').read_text()
for old,new in reversed(json.loads((D/'changes.json').read_text())):assert new in s;s=s.replace(new,old)
assert s==(A/'route.cpp').read_text();files=[Path(__file__),D/'changes.json',A/'route.cpp',B/'route.cpp']
for n in ['native_bidi_kernel.h','native_forward_kernel.h']:assert (A/n).read_bytes()==(B/n).read_bytes();files.extend([A/n,B/n])
a=(R/'tools/run_native_live_seed_global_edge_model_v1.py').read_text();b=(R/'tools/run_native_live_seed_cpu_profile_model_v1.py').read_text().replace('native_live_seed_cpu_profile_adapter_v1','native_live_seed_global_edge_adapter_v1');assert ast.dump(ast.parse(a))==ast.dump(ast.parse(b));files.extend([R/'tools/run_native_live_seed_global_edge_model_v1.py',R/'tools/run_native_live_seed_cpu_profile_model_v1.py'])
(D/'verification.json').write_text(json.dumps(dict(native_routing_body_equal_after_only_CPU_clock_substitutions=True,kernels_byte_identical=True,model_AST_unchanged_except_adapter_import=True,bindings={str(p):sha(p) for p in files},scope='CLOCK_THREAD_CPUTIME_ID native router thread and steady wall clock bracket same calls; bidi/forward separately accumulated. No search/transaction/seed policy changes, timer overhead not independently subtracted.'),indent=2)+'\n');print('CPU CLOCK SOURCE PASS')
