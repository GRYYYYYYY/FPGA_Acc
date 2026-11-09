"""Frozen ABC LUT6 mapping/CEC of independently audited Full combinational cut."""
import json,hashlib,shutil,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'vexriscv_full_combinational_cut_v1_2026-10-09';D=E/'vexriscv_full_cut_mapping_v1_2026-10-09';D.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();proof=json.loads((B/'verification.json').read_text())
for p,h in proof['bindings'].items():assert sha(p)==h
availability=json.loads((E/'prospective_family_candidates_2026-10-06/frontend_availability.json').read_text());abc=Path(availability['yosys_path']).parent.parent/'abc/abc';shutil.copyfile(B/'original.blif',D/'original.blif');bindings={str(p):sha(p) for p in (Path(__file__).resolve(),B/'verification.json',B/'original.blif',B/'sequential_boundary.json',abc,D/'original.blif')};commands=['read_blif original.blif; strash; if -K 6; write_blif mapped.blif','cec original.blif mapped.blif'];(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,abc=str(abc),commands=commands,timeout_each_s=180,scope='Combinational cut LUT6 mapping and CEC only. Retains archived sequential boundary; no whole HDL equivalence, native acceptance, timing or prediction claim.'),indent=2)+'\n');results=[]
for label,cmd in zip(('map','cec'),commands):
 start=time.perf_counter()
 with (D/(label+'.log')).open('x') as log:
  try:code=subprocess.run([str(abc),'-c',cmd],cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=180).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 results.append(dict(stage=label,exit_code=code,seconds=time.perf_counter()-start));print(results[-1],flush=True)
 if code!=0 or not (D/'mapped.blif').exists():break
passed=len(results)==2 and all(x['exit_code']==0 for x in results) and 'Networks are equivalent' in (D/'cec.log').read_text();sizes=[]
if (D/'mapped.blif').exists():sizes=[len(s.split())-2 for s in (D/'mapped.blif').read_text().splitlines() if s.startswith('.names ')]
if passed:assert sizes and max(sizes)<=6
assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,results=results,cut_equivalence_pass=passed,mapped_nodes=len(sizes),max_lut_inputs=max(sizes) if sizes else None,admitted_for_prediction=False,files={str(p):sha(p) for p in D.iterdir() if p.is_file()}),indent=2)+'\n');print('cut_equivalence_pass',passed,flush=True)
