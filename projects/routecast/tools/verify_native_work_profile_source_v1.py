"""Recover complete search/heap/native body after counter-only substitutions."""
import json,ast
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/native_work_profile_source_contract_v1_2026-10-10';A=R/'build/native_live_seed_cpu_profile_v1_2026-10-10/source';B=R/'build/native_live_seed_work_profile_v1_2026-10-10/source';files=[Path(__file__),D/'changes.json']
for name,ops in json.loads((D/'changes.json').read_text()).items():
 s=(B/name).read_text()
 for old,new in reversed(ops):assert new in s;s=s.replace(new,old)
 assert s==(A/name).read_text(),name;files.extend([A/name,B/name])
assert (A/'native_bidi_kernel.h').read_bytes()==(B/'native_bidi_kernel.h').read_bytes();files.extend([A/'native_bidi_kernel.h',B/'native_bidi_kernel.h'])
a=(R/'tools/run_native_live_seed_cpu_profile_model_v1.py').read_text();b=(R/'tools/run_native_live_seed_work_profile_model_v1.py').read_text().replace('native_live_seed_work_profile_adapter_v1','native_live_seed_cpu_profile_adapter_v1');assert ast.dump(ast.parse(a))==ast.dump(ast.parse(b));files.extend([R/'tools/run_native_live_seed_cpu_profile_model_v1.py',R/'tools/run_native_live_seed_work_profile_model_v1.py'])
(D/'verification.json').write_text(json.dumps(dict(all_heap_search_and_native_bodies_equal_after_only_counter_output_substitutions=True,bidi_search_body_byte_identical=True,full_model_AST_equal_except_Search_import=True,bindings={str(p):sha(p) for p in files},scope='Counters never used for search/heap/price/transaction predicates; buffered separate work file, full requested paths remain protocol unchanged. Counter/timer overhead included, no subtraction or uninstrumented timing claim.'),indent=2)+'\n');print('WORK COUNTER SOURCE PASS')
