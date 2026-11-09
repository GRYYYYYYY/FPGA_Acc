"""Sequential, frozen AB/BA developed-case full-driver repetitions."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path

root=Path('experiments/alu4_prefilter_pairs_2026-10-05')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,data):
    temp=root/(name+'.tmp');temp.write_text(json.dumps(data,indent=2)+'\n');temp.replace(root/name)
if root.exists():raise ValueError('fresh owner directory required; no automatic resume')
root.mkdir();(root/'owner.lock').write_text(str(os.getpid())+'\n')
source=Path('tools/alu4_free_pin_cohort.py').read_text()
fast=Path('tools/alu4_free_pin_prefilter_cohort.py').read_text()
inputs=json.loads(Path('experiments/alu4_free_pin_cohort_2026-10-05/receipt.json').read_text())['input_sha256']
bindings={str(p):sha(p) for p in Path('tools').glob('*.py')}
bindings.update(inputs)
reference=Path('experiments/alu4_free_pin_cohort_2026-10-05/prediction.json');expected=sha(reference);bindings[str(reference)]=expected
order=['baseline','prefilter','prefilter','baseline'];jobs=[]
for i,mode in enumerate(order,1):
    target=root/f'run_{i}_{mode}'
    code=source if mode=='baseline' else fast
    original='experiments/alu4_free_pin_cohort_2026-10-05' if mode=='baseline' else 'experiments/alu4_free_pin_prefilter_cohort_2026-10-05'
    code=code.replace("out=Path('"+original+"')","out=Path('"+str(target)+"')")
    script=root/f'run_{i}.py';script.write_text(code)
    bindings[str(script)]=sha(script)
    jobs.append({'mode':mode,'script':str(script),'output':str(target)})
save('plan.json',{'jobs':jobs,'bindings':bindings,'expected_prediction_sha256':expected,'order':'AB/BA','timeout_per_run_s':3600,'concurrency':1,'scope':'two full-driver developed-case pairs, not whole-pipeline or native-baseline speed evidence'})
completed=[];start=time.monotonic()
try:
    for i,job in enumerate(jobs,1):
        assert all(sha(p)==h for p,h in bindings.items()),'source/input drift'
        t=time.monotonic()
        with (root/f'run_{i}.log').open('w') as log:
            process=subprocess.Popen([sys.executable,job['script']],stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'PYTHONPATH':'tools','OMP_NUM_THREADS':'1'})
            save('status.json',{'status':'running','run':i,'child_pid':process.pid,'completed':completed})
            try:code=process.wait(timeout=3600)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:process.kill();process.wait()
                raise RuntimeError('per-run timeout; queue stopped')
        assert code==0,('run failed',i,code)
        out=Path(job['output']);receipt=json.loads((out/'receipt.json').read_text())
        assert sha(out/'prediction.json')==expected
        if job['mode']=='prefilter':assert (out/'equivalence.json').exists()
        assert all(sha(p)==h for p,h in bindings.items()),'source/input drift'
        completed.append({'run':i,'mode':job['mode'],'exit_code':code,'driver_wall_s':receipt['full_wall_s'],'outer_wall_s':time.monotonic()-t,'receipt_sha256':sha(out/'receipt.json'),'prediction_sha256':expected})
        save('status.json',{'status':'between_runs','completed':completed})
    ratios=[completed[0]['driver_wall_s']/completed[1]['driver_wall_s'],completed[3]['driver_wall_s']/completed[2]['driver_wall_s']]
    save('receipt.json',{'runs':completed,'paired_wall_ratios':ratios,'full_wall_s':time.monotonic()-start,'scope':'Two sequential AB/BA pairs; unchanged output verified. Shared-host effects not controlled, upstream and native feedback excluded.'})
    save('status.json',{'status':'completed','completed':completed})
except BaseException as error:
    save('status.json',{'status':'failed','completed':completed,'error':repr(error)})
    raise
