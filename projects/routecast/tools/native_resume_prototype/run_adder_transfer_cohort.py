"""Fixed-policy transfer, robust local/root transitive Python source freeze."""
import ast,json,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'experiments/native_resume_adder_transfer_2026-10-07';out.mkdir(exist_ok=False);producer=ROOT/'tools/native_resume_prototype/cohort_adder_pipeline_trial.py'
def closure(seeds):
 result={};todo=list(seeds)
 while todo:
  p=todo.pop().resolve()
  if str(p) in result:continue
  result[str(p)]=sha(p)
  for n in ast.walk(ast.parse(p.read_text())):
   names=[n.module] if isinstance(n,ast.ImportFrom) and n.level==0 else [a.name for a in n.names] if isinstance(n,ast.Import) else []
   for name in names:
    if not name:continue
    for folder in (p.parent,ROOT/'tools'):
     f=folder/(name.split('.')[0]+'.py')
     if f.exists():todo.append(f);break
 return result
sources=closure([Path(__file__),producer]);inputs={};source=ROOT/'work/adder_tree_family_native_capture_v2_2026-10-06/adder_tree_2L_032bits'
for i in (1,2,3):
 ep=ROOT/f'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_{i}_endpoints.json';meta=json.loads(ep.read_text());inputs[str(ep)]=sha(ep);inputs.update({v['path']:v['sha256'] for v in meta['inputs'].values()})
for f in (source/'design.blif',source/'design.route',source/'report_timing.setup.rpt',ROOT/'build/native_resume_singlepass_floor_2026-10-07/routecast_resume_vpr',ROOT/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor',ROOT/'build/native_resume_shared_exchange_cpp_2026-10-07/exchange'):inputs[str(f)]=sha(f)
pilot=ROOT/'experiments/native_resume_adder_pipeline_step1_workflow_2026-10-07/receipt.json';protocol=dict(inputs=inputs,sources=sources,pilot_receipt_sha256=sha(pilot),cases=[1,2,3],policy='Same0.01ns all-NET exchange, native index correction and single marking-pass floor policy; native architecture/chanwidth are originalCOFFE/300 input, not retuned. Family existing past evidence disclosed.',scope='Step1workflow was portability pilot before this orchestration freeze. All remaining cold/step2/step3 runs prospective; no algorithm changes after pilot. Family-transfer validation, not virgin unseen-label test. Robust source closure searches sibling and root tools.')
assert all(sha(f)==h for f,h in {**inputs,**sources}.items());(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');runs=[dict(index=1,mode='workflow',exit_code=0,pilot=True,outer_seconds=None)]
for i,mode in ((1,'cold'),(2,'workflow'),(2,'cold'),(3,'workflow'),(3,'cold')):
 log=out/f'step{i}_{mode}.log';begin=time.perf_counter()
 with log.open('w') as stream:
  try:code=subprocess.run([sys.executable,str(producer),mode,str(i)],stdout=stream,stderr=subprocess.STDOUT,cwd=ROOT,timeout=300).returncode
  except subprocess.TimeoutExpired:code='timeout'
 row=dict(index=i,mode=mode,exit_code=code,pilot=False,outer_seconds=time.perf_counter()-begin,log_sha256=sha(log));runs.append(row);(out/'runs.json').write_text(json.dumps(runs,indent=2)+'\n');print(row,flush=True)
assert all(sha(f)==h for f,h in {**inputs,**sources}.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),runs=runs),indent=2)+'\n')
