"""Complete deterministic frontend cohort, retaining all rejects; no heldout admission."""
import ast,json,re,shutil,subprocess,time
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/fpu_softlogic_cohort_readiness_v1_2026-10-10';assert not D.exists()
S=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow/benchmarks/fpu'
prior=R/'experiments/fpu_bfly_frontend_readiness_v1_2026-10-10/receipt.json';old=json.loads(prior.read_text());assert old['exit_code']==0 and all(sha(k)==v for k,v in old['bindings'].items())
Y=next(Path(p) for p in old['bindings'] if Path(p).name=='yosys');ref=R/'tools/review_ultraembedded_frontend_admission_v2.py';node=next(n for n in ast.parse(ref.read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='allowed' for t in n.targets));allowed=ast.literal_eval(node.value)
bindings={str(p):sha(p) for p in [Path(__file__).resolve(),prior,Y,ref,*sorted(S.rglob('*.v'))]};cases=[]
for p in sorted((S/'softlogic').glob('*.v')):
 top=p.stem;assert re.search(r'\bmodule\s+'+re.escape(top)+r'\s*\(',p.read_text()),top
 cases.append(dict(name=top,source=str(p),sha256=sha(p),reuse_prior=top=='bfly'))
assert len(cases)==8;D.mkdir()
# Every source/script and command is frozen before remaining synthesis begins.
for c in cases:
 if c['reuse_prior']:continue
 w=D/c['name'];w.mkdir();shutil.copyfile(c['source'],w/'design.v')
 (w/'synth.ys').write_text('read_verilog design.v\nhierarchy -check -top '+c['name']+'\nsynth -top '+c['name']+' -flatten -lut 6\ndffunmap\ncheck -assert\nstat\nwrite_json design.json\nwrite_blif design.blif\n')
 for p in [w/'design.v',w/'synth.ys']:bindings[str(p)]=sha(p)
 c['command']=[str(Y),'-s','synth.ys']
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,timeout_s=600,order='alphabetical sequential; all outcomes retained',allowed_types=sorted(allowed),scope='Whole softlogic cohort frontend screening. Authenticated bfly reused only for screening, all hardlogic variants stay quarantined with it. No route labels, heldout or source-equivalence admission.'),indent=2)+'\n');rows=[]
for c in cases:
 if c['reuse_prior']:
  row=dict(name=c['name'],exit_code=old['exit_code'],seconds=old['seconds'],cell_types=old['cell_types'],reused_frontend_receipt=str(prior))
 else:
  w=D/c['name'];tick=time.perf_counter()
  with (w/'synthesis.log').open('w') as log:
   try:code=subprocess.run(c['command'],cwd=w,stdout=log,stderr=subprocess.STDOUT,timeout=600).returncode
   except subprocess.TimeoutExpired:code=124
  row=dict(name=c['name'],exit_code=code,seconds=time.perf_counter()-tick)
  if code==0:
   m=json.loads((w/'design.json').read_text())['modules'];assert set(m)=={c['name']};row['cell_types']=dict(Counter(x['type'] for x in m[c['name']]['cells'].values()))
  for p in w.iterdir():
   if p.is_file():bindings[str(p)]=sha(p)
 row.update(unsupported_types={k:v for k,v in row.get('cell_types',{}).items() if k not in allowed},native_admitted=False,heldout_admitted=False);rows.append(row)
 (D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print(row,flush=True)
assert len(rows)==8 and all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all_eight_frontend_outcomes_accounted=True,scope='Type screen only; even empty unsupported set is not functional, serialized, native, timing or heldout admission. Failures/timeouts retained, no retries.'),indent=2)+'\n')
