"""Exact design plus original RAM library; all residual modules reported."""
import json,subprocess,shutil,time
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];S=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow';library=S/'primitives.v';old=R/'experiments/sha1_frontend_readiness_v1_2026-10-10/receipt.json';r=json.loads(old.read_text());assert all(sha(k)==h for k,h in r['bindings'].items());Y=next(Path(k) for k in r['bindings'] if Path(k).name=='yosys');D=R/'experiments/ch_intrinsics_multifile_frontend_v1_2026-10-10';D.mkdir();bindings={str(Path(__file__)):sha(Path(__file__)),str(old):sha(old),str(Y):sha(Y),str(library):sha(library)};cases=[]
for name in ['ch_intrinsics']:
 src=S/'benchmarks/verilog'/(name+'.v');w=D/name;w.mkdir();shutil.copyfile(src,w/'design.v');shutil.copyfile(library,w/'primitives.v');script=f'read_verilog design.v primitives.v\nhierarchy -check -top memset\nsynth -top memset -flatten -lut 6\ndffunmap\ncheck -assert\nstat\nwrite_json design.json\nwrite_blif design.blif\n';(w/'synth.ys').write_text(script)
 for p in [src,w/'design.v',w/'primitives.v',w/'synth.ys']:bindings[str(p)]=sha(p)
 cases.append(dict(name=name,command=[str(Y),'-s','synth.ys']))
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,timeout_per_case_seconds=600,scope='Correct whole-design memset top, original full source plus original primitives.v, no blackbox/zero/reset/latch projection or RAM replacement. Library keep_hierarchy may leave modules; report full module inventory, not silent primitive admission. Original single-port memory behavior/native memory mapping and functional proof pending. No route/heldout evidence.'),indent=2)+'\n');rows=[]
allowed={'$_MUX_','$_XOR_','$_XNOR_','$_NOT_','$_OR_','$_AND_','$_DFF_P_','$_DFF_PP0_','$_DFF_PP1_','$scopeinfo'}
for case in cases:
 w=D/case['name'];tick=time.perf_counter()
 with (w/'synthesis.log').open('w') as log:
  try:code=subprocess.run(case['command'],cwd=w,stdout=log,stderr=subprocess.STDOUT,timeout=600).returncode
  except subprocess.TimeoutExpired:code=124
 row=dict(name=case['name'],exit_code=code,seconds=time.perf_counter()-tick)
 if code==0:
  data=json.loads((w/'design.json').read_text());modules={n:dict(cell_types=dict(Counter(c['type'] for c in m['cells'].values())),attributes=m['attributes']) for n,m in data['modules'].items()};types=Counter(c['type'] for m in data['modules'].values() for c in m['cells'].values());row.update(modules=modules,fully_flattened=set(modules)=={'memset'},unsupported_boolean_schema={k:v for k,v in types.items() if k not in allowed})
 row['files']={str(p):sha(p) for p in w.iterdir() if p.is_file()};rows.append(row);(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print('CH_INTRINSICS_MULTIFILE',case['name'],code,flush=True)
assert all(sha(k)==h for k,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all_cases_attempted=len(rows)==1,primitive_native_admitted=False),indent=2)+'\n')
