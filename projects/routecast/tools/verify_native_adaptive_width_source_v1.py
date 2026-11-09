"""Recover original128 and the exact guarded64 clone transformations."""
import json,re,ast
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/native_adaptive_width_source_contract_v1_2026-10-10';A=R/'build/native_live_seed_work_profile_v1_2026-10-10/source';B=R/'build/native_live_seed_adaptive_width_v1_2026-10-10/source';t=json.loads((D/'changes.json').read_text());files=[Path(__file__),D/'changes.json']
for name,recipe in t['headers'].items():
 assert (A/name).read_bytes()==(B/name).read_bytes();s=(B/name.replace('.h','64.h')).read_text();ops=recipe['operations']
 for old,new in reversed(ops[1:]):
  assert new in s
  if old=='extern \"C\"':s=re.sub(r'\bstatic (?=(?:int|void\*?) rc_)',old+' ',s)
  else:s=s.replace(new,old)
 for f in recipe['functions']:s=re.sub(r'\b'+f+'64'+r'\b',f,s)
 for old,new in recipe['classes'].items():s=re.sub(r'\b'+new+r'\b',old,s)
 old,new=ops[0];assert old=='Wide';s=s.replace(new,old);assert s==(A/name).read_text(),name;files.extend([A/name,B/name,B/name.replace('.h','64.h')])
s=(B/'route.cpp').read_text()
for old,new in reversed(t['route']):assert new in s;s=s.replace(new,old)
assert s==(A/'route.cpp').read_text();files.extend([A/'route.cpp',B/'route.cpp'])
a=(R/'tools/run_native_live_seed_work_profile_model_v1.py').read_text();b=(R/'tools/run_native_live_seed_adaptive_width_model_v1.py').read_text().replace('native_live_seed_adaptive_width_adapter_v1','native_live_seed_work_profile_adapter_v1');assert ast.dump(ast.parse(a))==ast.dump(ast.parse(b));files.extend([R/'tools/run_native_live_seed_work_profile_model_v1.py',R/'tools/run_native_live_seed_adaptive_width_model_v1.py'])
(D/'verification.json').write_text(json.dumps(dict(original128_headers_byte_identical=True,guarded64_kernels_recover_exact_original_after_type_radix_inf_high_word_renames=True,full_native_body_recovered_after_dispatch_guard_scratch_additions=True,full_model_AST_unchanged_except_Search_import=True,bindings={str(p):sha(p) for p in files},scope='uint64 guarded by2*n*(maxcost+weight*maxprice)<UINT64_MAX at every P/static preparation. Exact64 radix applies original high0 branch, output high0; static internal clone only. Independent64/128 workspace and outputs; original128 handles larger bounds. Runtime complete scope/mode-switch tests still required.'),indent=2)+'\n');print('ADAPTIVE WIDTH SOURCE PASS')
